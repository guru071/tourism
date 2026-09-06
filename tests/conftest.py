"""
Pytest fixtures and test environment configuration for E2E testing.
Provides both live-port clients and in-process test runners.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
import yaml

# Add backend and tests directories to sys.path
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from tests.utils.config import (
    ALEMBIC_DIR,
    ALEMBIC_INI_FILE,
    FASTAPI_BASE_URL,
    FRONTEND_DIR,
    NEXTJS_BASE_URL,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from tests.utils.probes import check_tcp_port


@pytest.fixture(scope="session")
def docker_compose_manifest() -> Dict[str, Any]:
    """Parse and return docker-compose.yml structure."""
    compose_file = PROJECT_ROOT / "docker-compose.yml"
    assert compose_file.exists(), f"docker-compose.yml must exist at {compose_file}"
    with open(compose_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def postgres_target() -> Dict[str, Any]:
    """Return configured PostgreSQL target connection parameters."""
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "database": POSTGRES_DB,
        "is_listening": check_tcp_port(POSTGRES_HOST, POSTGRES_PORT, timeout=0.5),
    }


@pytest.fixture(scope="session")
def redis_target() -> Dict[str, Any]:
    """Return configured Redis target parameters."""
    return {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "is_listening": check_tcp_port(REDIS_HOST, REDIS_PORT, timeout=0.5),
    }


@pytest.fixture(scope="session")
def fastapi_target() -> Dict[str, Any]:
    """Return configured FastAPI parameters and live listening status."""
    is_live = check_tcp_port("localhost", 8000, timeout=0.5)
    return {
        "base_url": FASTAPI_BASE_URL,
        "health_url": f"{FASTAPI_BASE_URL}/health",
        "api_v1_url": f"{FASTAPI_BASE_URL}/api/v1",
        "openapi_url": f"{FASTAPI_BASE_URL}/openapi.json",
        "is_listening": is_live,
    }


@pytest.fixture(scope="session")
def nextjs_target() -> Dict[str, Any]:
    """Return configured Next.js target parameters."""
    is_live = check_tcp_port("localhost", 3000, timeout=0.5)
    return {
        "base_url": NEXTJS_BASE_URL,
        "frontend_dir": FRONTEND_DIR,
        "package_json": FRONTEND_DIR / "package.json",
        "is_listening": is_live,
    }


@pytest.fixture(scope="session")
def fastapi_app():
    """Import and return the FastAPI application instance from backend."""
    try:
        from app.main import app
        return app
    except Exception as exc:
        pytest.fail(f"Could not import FastAPI app from app.main: {exc}")


@pytest.fixture(scope="session")
def http_client(fastapi_app, fastapi_target):
    """
    HTTP client for testing FastAPI:
    Uses live network requests if port 8000 is listening,
    otherwise uses starlette TestClient with the actual FastAPI app.
    """
    if fastapi_target["is_listening"]:
        import requests
        session = requests.Session()
        yield session
        session.close()
    else:
        from starlette.testclient import TestClient
        with TestClient(fastapi_app, base_url=FASTAPI_BASE_URL) as client:
            yield client
