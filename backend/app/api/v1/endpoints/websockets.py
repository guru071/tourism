import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_pool
from app.models.booking import Booking
from app.models.listing import Listing

logger = logging.getLogger("control_tower_ws")

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """
    Production-ready asynchronous WebSocket Connection Manager.
    Manages active client connections, concurrent broadcasting,
    dead connection pruning, and optional Redis Pub/Sub integration.
    """

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self._lock: Optional[asyncio.Lock] = None
        self._pubsub_task: Optional[asyncio.Task] = None
        self._redis_channel = "control_tower_events"
        self._redis_checked: bool = False
        self._redis_available: bool = False

    @property
    def lock(self) -> asyncio.Lock:
        """Lazy initialization of asyncio.Lock to ensure it is bound to the running loop."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def check_redis(self) -> bool:
        """Check if Redis is accessible without blocking application workflow."""
        if self._redis_checked:
            return self._redis_available
        try:
            redis = await get_redis_pool()
            await asyncio.wait_for(redis.ping(), timeout=0.2)
            self._redis_available = True
        except Exception:
            self._redis_available = False
            logger.debug("Redis server not available. Running in standalone in-memory mode.")
        finally:
            self._redis_checked = True
        return self._redis_available

    async def connect(self, websocket: WebSocket) -> None:
        """Accept connection and register websocket."""
        await websocket.accept()
        async with self.lock:
            self.active_connections.add(websocket)
        logger.info("WebSocket connected. Active clients: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister websocket connection."""
        async with self.lock:
            self.active_connections.discard(websocket)
        logger.info("WebSocket disconnected. Active clients: %d", len(self.active_connections))

    def get_active_count(self) -> int:
        """Return the number of currently active websocket connections."""
        return len(self.active_connections)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> bool:
        """Send a JSON payload to a specific client connection."""
        try:
            await websocket.send_json(message)
            return True
        except (WebSocketDisconnect, RuntimeError, Exception) as exc:
            logger.debug("Failed sending message to websocket client: %s", exc)
            await self.disconnect(websocket)
            return False

    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[WebSocket] = None,
    ) -> None:
        """
        Broadcast JSON message concurrently to active connections.
        Can optionally exclude a specific websocket (e.g. the newly connected client).
        Automatically prunes disconnected clients.
        """
        async with self.lock:
            if exclude is not None:
                sockets = [ws for ws in self.active_connections if ws != exclude]
            else:
                sockets = list(self.active_connections)

        if not sockets:
            return

        tasks = [self.send_personal_message(message, ws) for ws in sockets]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def publish_redis(self, message: Dict[str, Any]) -> None:
        """Publish message to Redis Pub/Sub channel if Redis is active."""
        if not self._redis_checked:
            await self.check_redis()
        if not self._redis_available:
            return

        try:
            redis = await get_redis_pool()
            await redis.publish(self._redis_channel, json.dumps(message))
        except Exception as exc:
            self._redis_available = False
            logger.debug("Redis publish unavailable, switching to local broadcast mode: %s", exc)

    async def start_redis_listener(self) -> None:
        """Listen to Redis Pub/Sub channel and broadcast received messages locally."""
        if not await self.check_redis():
            return

        try:
            redis = await get_redis_pool()
            pubsub = redis.pubsub()
            await pubsub.subscribe(self._redis_channel)
            logger.info("Subscribed to Redis channel: %s", self._redis_channel)

            async for msg in pubsub.listen():
                if msg and msg.get("type") == "message":
                    raw_data = msg.get("data")
                    if raw_data:
                        try:
                            payload = json.loads(raw_data)
                            await self.broadcast(payload)
                        except Exception as parse_err:
                            logger.warning("Error parsing Redis message: %s", parse_err)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._redis_available = False
            logger.debug("Redis listener stopped: %s", exc)

    def ensure_redis_listener(self) -> None:
        """Start the background Redis listener task if not already running."""
        if self._redis_checked and not self._redis_available:
            return

        if self._pubsub_task is None or self._pubsub_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._pubsub_task = loop.create_task(self.start_redis_listener())
            except RuntimeError:
                pass


manager = ConnectionManager()


async def get_recent_bookings(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent bookings with listing titles from database."""
    try:
        async def _query():
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(Booking, Listing.title)
                    .join(Listing, Booking.listing_id == Listing.id, isouter=True)
                    .order_by(Booking.created_at.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                return result.all()

        rows = await asyncio.wait_for(_query(), timeout=1.5)
        recent = []
        for b, listing_title in rows:
            recent.append({
                "id": str(b.id),
                "booking_reference": b.booking_reference,
                "status": b.status,
                "listing_title": listing_title or "General Booking",
                "guests_count": b.guests_count,
                "total_price": float(b.total_price) if b.total_price is not None else 0.0,
                "currency": b.currency,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            })
        return recent
    except Exception as e:
        logger.warning("Error fetching recent bookings: %s", e)
        return []


async def broadcast_active_users(exclude: Optional[WebSocket] = None) -> None:
    """Broadcast current active user counts to connected clients."""
    payload = {
        "type": "active_users_update",
        "data": {
            "active_users": manager.get_active_count(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(payload, exclude=exclude)
    await manager.publish_redis(payload)


async def broadcast_booking_notification(booking_data: Dict[str, Any]) -> None:
    """
    Broadcast recent booking notification to all connected Control Tower clients.
    Can be invoked from bookings endpoint or background tasks.
    """
    payload = {
        "type": "booking_notification",
        "data": booking_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(payload)
    await manager.publish_redis(payload)


@router.websocket("/ws/control-tower")
@router.websocket("/control-tower")
async def control_tower_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time Control Tower updates.
    Broadcasts current active user counts and recent booking notifications.
    Supports bidirectional commands (ping/pong, get_stats, get_recent_bookings).
    """
    await manager.connect(websocket)
    manager.ensure_redis_listener()

    try:
        # Send initial snapshot immediately upon connection
        recent_bookings = await get_recent_bookings(limit=10)
        initial_snapshot = {
            "type": "initial_state",
            "data": {
                "active_users": manager.get_active_count(),
                "recent_bookings": recent_bookings,
                "server_time": datetime.now(timezone.utc).isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await manager.send_personal_message(initial_snapshot, websocket)

        # Notify existing clients that a new client joined (exclude the new client who has snapshot)
        await broadcast_active_users(exclude=websocket)

        # Listen for client messages (e.g. ping/pong, refresh requests)
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except (json.JSONDecodeError, ValueError):
                try:
                    text_data = await websocket.receive_text()
                    data = {"action": text_data}
                except (WebSocketDisconnect, RuntimeError):
                    break
            except RuntimeError:
                break

            action = data.get("action") if isinstance(data, dict) else str(data)

            if action == "ping":
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )
            elif action == "get_recent_bookings":
                limit = data.get("limit", 10) if isinstance(data, dict) else 10
                bookings = await get_recent_bookings(limit=limit)
                await manager.send_personal_message(
                    {
                        "type": "recent_bookings",
                        "data": bookings,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )
            elif action == "get_active_users":
                await manager.send_personal_message(
                    {
                        "type": "active_users_update",
                        "data": {
                            "active_users": manager.get_active_count(),
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )
            else:
                await manager.send_personal_message(
                    {
                        "type": "ack",
                        "action": action,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        logger.info("Control Tower WebSocket client disconnected normally.")
    except Exception as exc:
        logger.warning("Unexpected WebSocket connection exception: %s", exc)
    finally:
        await manager.disconnect(websocket)
        # Notify remaining clients about updated active user count
        await broadcast_active_users()
