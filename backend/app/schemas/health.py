from typing import Dict
from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    database: str = Field(default="healthy", description="Database connectivity status")
    redis: str = Field(default="healthy", description="Redis connectivity status")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall system health status")
    version: str = Field(default="1.0.0", description="API SemVer version")
    message: str = Field(
        default="AI Tourism Ecosystem API is running",
        description="Service status message",
    )
    services: Dict[str, str] = Field(
        default_factory=lambda: {
            "database": "healthy",
            "redis": "healthy",
        },
        description="Individual service connection statuses",
    )
