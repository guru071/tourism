"""
Configuration constants and environmental bindings for E2E Test Suite.
Authoritative source: PROJECT.md, ORIGINAL_REQUEST.md, spec_miner_blueprints_1/spec.md
"""

import os
from pathlib import Path

# Paths
TESTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = TESTS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
ALEMBIC_INI_FILE = BACKEND_DIR / "alembic.ini"
ALEMBIC_DIR = BACKEND_DIR / "alembic"

# Network Endpoints & Credentials
POSTGRES_HOST = os.getenv("TEST_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("TEST_POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("TEST_POSTGRES_USER", "tourism_user")
POSTGRES_PASSWORD = os.getenv("TEST_POSTGRES_PASSWORD", "tourism_password")
POSTGRES_DB = os.getenv("TEST_POSTGRES_DB", "tourism_db")

REDIS_HOST = os.getenv("TEST_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("TEST_REDIS_PORT", "6379"))

FASTAPI_BASE_URL = os.getenv("TEST_FASTAPI_URL", "http://localhost:8000").rstrip("/")
FASTAPI_HEALTH_URL = f"{FASTAPI_BASE_URL}/health"
FASTAPI_API_V1_URL = f"{FASTAPI_BASE_URL}/api/v1"
FASTAPI_OPENAPI_URL = f"{FASTAPI_BASE_URL}/openapi.json"

NEXTJS_BASE_URL = os.getenv("TEST_NEXTJS_URL", "http://localhost:3000").rstrip("/")

# Default timeouts
DEFAULT_SOCKET_TIMEOUT = float(os.getenv("TEST_SOCKET_TIMEOUT", "2.0"))
DEFAULT_HTTP_TIMEOUT = float(os.getenv("TEST_HTTP_TIMEOUT", "5.0"))
