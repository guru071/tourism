from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import async_engine
from app.core.redis import close_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    # Startup
    yield
    # Shutdown: gracefully release connections
    try:
        await async_engine.dispose()
    except Exception:
        pass
    try:
        await close_redis_pool()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for the AI Tourism Operating System (Modular Monolith)",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health probe
app.include_router(health_router, prefix="", tags=["Monitoring"])

# Versioned API Router (/api/v1)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
