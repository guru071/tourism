import asyncio
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_pool
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_pool),
) -> HealthResponse:
    """
    Health check probe verifying database and redis connectivity.
    Gracefully catches connection errors if containers are unbooted,
    always returning HTTP 200 with status 'ok'.
    """
    db_status = "unreachable"
    try:
        res = await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=1.0)
        if res.scalar() == 1:
            db_status = "healthy"
    except Exception:
        db_status = "unreachable"

    redis_status = "unreachable"
    try:
        pong = await asyncio.wait_for(redis.ping(), timeout=1.0)
        if pong is True:
            redis_status = "healthy"
    except Exception:
        redis_status = "unreachable"

    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        message="AI Tourism Ecosystem API is running",
        services={
            "database": db_status,
            "redis": redis_status,
        },
    )
