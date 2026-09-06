"""
Tier 3: Cross-Feature Combinations Tests.
Authoritative Specifications:
- PROJECT.md (Interface Contracts, Backend <-> Frontend, Backend <-> DB, Backend <-> Redis)
- spec_miner_blueprints_1/spec.md (Section 2 Architecture & Boundaries)
- spec_miner_schemas_2/spec.md (Section 8 Environment Variables, Section 9 FastAPI Integration)

Covers:
- Frontend to Backend health check & API client integration
- Backend to PostgreSQL configuration and query alignment
- Backend to Redis cache connection alignment
- Alembic migration alignment against PostgreSQL container
- Service dependency graph in multi-container topology
"""

from pathlib import Path
from typing import Any, Dict

import pytest

from tests.utils.config import (
    ALEMBIC_INI_FILE,
    BACKEND_DIR,
    FASTAPI_BASE_URL,
    FRONTEND_DIR,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    PROJECT_ROOT,
    REDIS_PORT,
)


class TestTier3Combinations:
    """Integration and cross-feature contract tests."""

    def test_combo_01_frontend_to_backend_api_integration(self):
        """Verify frontend API client correctly binds to backend /health contract."""
        api_client_file = FRONTEND_DIR / "src" / "lib" / "api.ts"
        assert api_client_file.exists(), f"Frontend API client missing at {api_client_file}"
        content = api_client_file.read_text(encoding="utf-8")
        assert "NEXT_PUBLIC_API_URL" in content, "Frontend must configure NEXT_PUBLIC_API_URL"
        assert "health" in content.lower(), "Frontend API client must include health fetching logic"

    def test_combo_02_backend_to_postgres_config_alignment(self, docker_compose_manifest):
        """Verify Backend DATABASE_URL matches PostgreSQL service credentials and port."""
        services = docker_compose_manifest["services"]
        assert "backend" in services and "postgres" in services

        backend_env = services["backend"].get("environment", [])
        if isinstance(backend_env, list):
            env_map = dict(item.split("=", 1) for item in backend_env if "=" in item)
        else:
            env_map = backend_env

        db_url = env_map.get("DATABASE_URL", "")
        # Must target postgres host on port 5432 with configured user and db
        assert "postgres:5432" in db_url
        assert POSTGRES_USER in db_url
        assert POSTGRES_DB in db_url
        assert db_url.startswith("postgresql+asyncpg://")

    def test_combo_03_backend_to_redis_config_alignment(self, docker_compose_manifest):
        """Verify Backend REDIS_URL matches Redis service host and port."""
        services = docker_compose_manifest["services"]
        assert "backend" in services and "redis" in services

        backend_env = services["backend"].get("environment", [])
        if isinstance(backend_env, list):
            env_map = dict(item.split("=", 1) for item in backend_env if "=" in item)
        else:
            env_map = backend_env

        redis_url = env_map.get("REDIS_URL", "")
        assert "redis:6379" in redis_url or f"redis:{REDIS_PORT}" in redis_url
        assert redis_url.startswith("redis://")

    def test_combo_04_compose_dependency_chain_and_health_conditions(self, docker_compose_manifest):
        """AC-01 / AC-03: Verify compose dependency chain with deterministic health conditions."""
        services = docker_compose_manifest["services"]
        backend_deps = services["backend"].get("depends_on", {})
        frontend_deps = services["frontend"].get("depends_on", {})

        # Backend must depend on postgres and redis being healthy
        assert "postgres" in backend_deps, "Backend must depend on postgres"
        assert "redis" in backend_deps, "Backend must depend on redis"

        if isinstance(backend_deps, dict):
            assert backend_deps["postgres"].get("condition") == "service_healthy", (
                "Backend must wait for postgres condition: service_healthy"
            )
            assert backend_deps["redis"].get("condition") == "service_healthy", (
                "Backend must wait for redis condition: service_healthy"
            )

        # Frontend must depend on backend
        if isinstance(frontend_deps, dict):
            assert "backend" in frontend_deps
        elif isinstance(frontend_deps, list):
            assert "backend" in frontend_deps

    def test_combo_05_alembic_postgres_migration_target(self):
        """AC-07: Verify Alembic database URL is configured targeting PostgreSQL."""
        if not ALEMBIC_INI_FILE.exists():
            pytest.skip("Milestone 2 pending: alembic.ini not yet generated.")
        content = ALEMBIC_INI_FILE.read_text(encoding="utf-8")
        assert "tourism_db" in content
        assert "tourism_user" in content or "POSTGRES_USER" in content or "DATABASE_URL" in content

    def test_combo_06_cors_alignment_between_frontend_and_backend(self, fastapi_app):
        """AC-05: Verify backend CORS allows requests from frontend origin (localhost:3000)."""
        cors_found = False
        for middleware in fastapi_app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_found = True
                allow_origins = getattr(middleware, "kwargs", {}).get("allow_origins", [])
                # Either wildcard '*' or 'http://localhost:3000' is required
                assert "*" in allow_origins or "http://localhost:3000" in allow_origins, (
                    f"CORS allow_origins {allow_origins} must include '*' or 'http://localhost:3000'"
                )
        assert cors_found, "CORSMiddleware not found in FastAPI app"
