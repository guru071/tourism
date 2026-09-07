import asyncio
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.api.v1.endpoints.websockets import (
    ConnectionManager,
    broadcast_booking_notification,
    broadcast_active_users,
    manager,
)


def test_control_tower_websocket_connection_and_initial_state():
    """Verify WebSocket connection succeeds and returns initial snapshot."""
    client = TestClient(app)
    with client.websocket_connect("/ws/control-tower") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "initial_state"
        assert "active_users" in msg["data"]
        assert "recent_bookings" in msg["data"]
        assert isinstance(msg["data"]["recent_bookings"], list)
        assert msg["data"]["active_users"] >= 1


def test_control_tower_websocket_versioned_route():
    """Verify WebSocket can also be accessed via /api/v1/ws/control-tower."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/control-tower") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "initial_state"
        assert "active_users" in msg["data"]


def test_control_tower_websocket_ping_pong():
    """Verify client ping is answered with server pong."""
    client = TestClient(app)
    with client.websocket_connect("/ws/control-tower") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial_state"

        ws.send_json({"action": "ping"})
        response = ws.receive_json()
        assert response["type"] == "pong"
        assert "timestamp" in response


def test_control_tower_websocket_get_active_users():
    """Verify client can explicitly request active users count."""
    client = TestClient(app)
    with client.websocket_connect("/ws/control-tower") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial_state"

        ws.send_json({"action": "get_active_users"})
        resp = ws.receive_json()
        assert resp["type"] == "active_users_update"
        assert "active_users" in resp["data"]
        assert resp["data"]["active_users"] >= 1


def test_control_tower_websocket_get_recent_bookings():
    """Verify client can query recent bookings via websocket."""
    client = TestClient(app)
    with client.websocket_connect("/ws/control-tower") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial_state"

        ws.send_json({"action": "get_recent_bookings", "limit": 5})
        resp = ws.receive_json()
        assert resp["type"] == "recent_bookings"
        assert isinstance(resp["data"], list)


def test_control_tower_websocket_unrecognized_action_ack():
    """Verify client sending custom action receives an acknowledgment."""
    client = TestClient(app)
    with client.websocket_connect("/ws/control-tower") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial_state"

        ws.send_json({"action": "refresh_dashboard"})
        resp = ws.receive_json()
        assert resp["type"] == "ack"
        assert resp["action"] == "refresh_dashboard"


def test_control_tower_websocket_broadcast_booking():
    """Verify broadcast_booking_notification delivers to active WebSocket client."""
    client = TestClient(app)
    with client.websocket_connect("/ws/control-tower") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial_state"

        test_booking = {
            "id": "test-id-123",
            "booking_reference": "TOS-TEST01",
            "status": "pending",
            "listing_title": "Bali Sunset Villa",
            "guests_count": 2,
            "total_price": 450.0,
            "currency": "USD",
            "event": "created",
        }

        asyncio.run(broadcast_booking_notification(test_booking))

        msg = ws.receive_json()
        assert msg["type"] == "booking_notification"
        assert msg["data"]["id"] == "test-id-123"
        assert msg["data"]["booking_reference"] == "TOS-TEST01"
        assert msg["data"]["listing_title"] == "Bali Sunset Villa"


@pytest.mark.asyncio
async def test_connection_manager_multi_client_lifecycle():
    """Verify ConnectionManager concurrent broadcasting and connection tracking."""
    mgr = ConnectionManager()

    class MockWebSocket:
        def __init__(self, name: str):
            self.name = name
            self.accepted = False
            self.sent_messages = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, data):
            self.sent_messages.append(data)

    ws1 = MockWebSocket("client1")
    ws2 = MockWebSocket("client2")

    # Connect client 1
    await mgr.connect(ws1)
    assert mgr.get_active_count() == 1
    assert ws1.accepted

    # Connect client 2
    await mgr.connect(ws2)
    assert mgr.get_active_count() == 2
    assert ws2.accepted

    # Broadcast to all clients
    broadcast_msg = {"type": "booking_notification", "reference": "REF-001"}
    await mgr.broadcast(broadcast_msg)
    assert len(ws1.sent_messages) == 1
    assert ws1.sent_messages[0]["reference"] == "REF-001"
    assert len(ws2.sent_messages) == 1
    assert ws2.sent_messages[0]["reference"] == "REF-001"

    # Broadcast with exclude (e.g., active user update to existing clients only)
    exclude_msg = {"type": "active_users_update", "active_users": 2}
    await mgr.broadcast(exclude_msg, exclude=ws2)
    assert len(ws1.sent_messages) == 2
    assert ws1.sent_messages[1]["type"] == "active_users_update"
    assert len(ws2.sent_messages) == 1  # ws2 was excluded

    # Disconnect client 1
    await mgr.disconnect(ws1)
    assert mgr.get_active_count() == 1

    # Disconnect client 2
    await mgr.disconnect(ws2)
    assert mgr.get_active_count() == 0
