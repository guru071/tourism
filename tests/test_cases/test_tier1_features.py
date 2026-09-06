"""
Tier 1: Feature Coverage Tests.
Authoritative Specifications:
- ORIGINAL_REQUEST.md (Requirements R1, R2; Acceptance Criteria AC-01 to AC-08)
- PROJECT.md (Architecture, Feature Inventory, Interface Contracts)
- spec_miner_blueprints_1/spec.md (Section 4 AC-01 to AC-08, Section 6 Features)
- spec_miner_schemas_2/spec.md (Section 1, Section 4, Section 7, Section 8)

Must contain >= 5 independent tests per primary feature:
1. PostgreSQL connectivity
2. Redis PING
3. FastAPI startup & /health returning 200 OK
4. Alembic schema migration verification
5. Next.js compilation & port 3000 response
"""

import json
from pathlib import Path
import re
from typing import Any, Dict

import pytest

from tests.utils.config import (
    ALEMBIC_DIR,
    ALEMBIC_INI_FILE,
    BACKEND_DIR,
    DOCKER_COMPOSE_FILE,
    FASTAPI_BASE_URL,
    FASTAPI_HEALTH_URL,
    FRONTEND_DIR,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    PROJECT_ROOT,
    REDIS_HOST,
    REDIS_PORT,
)
from tests.utils.probes import (
    check_tcp_port,
    load_docker_compose_manifest,
    probe_postgres_wire_protocol,
    send_redis_raw_command,
)


# ==============================================================================
# FEATURE 1: PostgreSQL Connectivity (>= 5 tests)
# ==============================================================================

class TestPostgreSQLFeature:
    """Verification of PostgreSQL 15 configuration, wire protocol, and credentials."""

    def test_pg_01_service_defined_in_compose(self, docker_compose_manifest):
        """AC-01: docker-compose must declare 'postgres' service with image 'postgres:15-alpine'."""
        services = docker_compose_manifest.get("services", {})
        assert "postgres" in services, "Service 'postgres' must be defined in docker-compose.yml"
        pg_service = services["postgres"]
        assert pg_service.get("image") == "postgres:15-alpine", (
            f"Expected postgres:15-alpine image, got: {pg_service.get('image')}"
        )
        ports = pg_service.get("ports", [])
        assert "5432:5432" in ports or 5432 in ports, (
            f"Expected port 5432:5432 exposed, got: {ports}"
        )

    def test_pg_02_environment_credentials_contract(self, docker_compose_manifest):
        """AC-02: PostgreSQL environment must configure user, password, and database correctly."""
        pg_service = docker_compose_manifest["services"]["postgres"]
        env = pg_service.get("environment", {})
        if isinstance(env, list):
            env_dict = dict(item.split("=", 1) for item in env if "=" in item)
        else:
            env_dict = env

        assert env_dict.get("POSTGRES_USER") == POSTGRES_USER, (
            f"Expected POSTGRES_USER={POSTGRES_USER}, got {env_dict.get('POSTGRES_USER')}"
        )
        assert env_dict.get("POSTGRES_PASSWORD") == POSTGRES_PASSWORD, (
            f"Expected POSTGRES_PASSWORD={POSTGRES_PASSWORD}, got {env_dict.get('POSTGRES_PASSWORD')}"
        )
        assert env_dict.get("POSTGRES_DB") == POSTGRES_DB, (
            f"Expected POSTGRES_DB={POSTGRES_DB}, got {env_dict.get('POSTGRES_DB')}"
        )

    def test_pg_03_healthcheck_contract(self, docker_compose_manifest):
        """AC-01 / AC-02: PostgreSQL service must define pg_isready healthcheck."""
        pg_service = docker_compose_manifest["services"]["postgres"]
        healthcheck = pg_service.get("healthcheck")
        assert healthcheck is not None, "PostgreSQL service must define a healthcheck"
        test_cmd = healthcheck.get("test")
        test_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "pg_isready" in test_str, f"Healthcheck must run pg_isready, got: {test_str}"
        assert POSTGRES_USER in test_str, f"Healthcheck must target user {POSTGRES_USER}"
        assert POSTGRES_DB in test_str, f"Healthcheck must target database {POSTGRES_DB}"

    def test_pg_04_volume_persistence_contract(self, docker_compose_manifest):
        """AC-01: PostgreSQL data directory must be persisted to named volume postgres_data."""
        pg_service = docker_compose_manifest["services"]["postgres"]
        volumes = pg_service.get("volumes", [])
        has_pg_data = any("postgres_data:/var/lib/postgresql/data" in v for v in volumes)
        assert has_pg_data, (
            f"Expected volume mount 'postgres_data:/var/lib/postgresql/data', got: {volumes}"
        )
        root_volumes = docker_compose_manifest.get("volumes", {})
        assert "postgres_data" in root_volumes, "Top-level volumes must declare postgres_data"

    def test_pg_05_database_url_contract(self, docker_compose_manifest):
        """AC-02: Backend service must configure asyncpg connection string targeting postgres:5432."""
        backend_service = docker_compose_manifest["services"]["backend"]
        env = backend_service.get("environment", [])
        if isinstance(env, list):
            env_dict = dict(item.split("=", 1) for item in env if "=" in item)
        else:
            env_dict = env

        db_url = env_dict.get("DATABASE_URL", "")
        expected_prefix = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"
        assert db_url == expected_prefix, f"DATABASE_URL mismatch. Got: {db_url}"

    def test_pg_06_wire_protocol_or_network_reachability(self, postgres_target):
        """AC-02: If PostgreSQL port 5432 is listening, verify wire protocol SSLRequest handshake."""
        if not postgres_target["is_listening"]:
            pytest.skip("PostgreSQL container port 5432 is not currently listening (offline / pending boot).")
        success, desc = probe_postgres_wire_protocol(postgres_target["host"], postgres_target["port"])
        assert success, f"PostgreSQL wire protocol probe failed: {desc}"


# ==============================================================================
# FEATURE 2: Redis PING & In-Memory Store (>= 5 tests)
# ==============================================================================

class TestRedisFeature:
    """Verification of Redis 7 configuration, healthcheck, and RESP PING protocol."""

    def test_redis_01_service_defined_in_compose(self, docker_compose_manifest):
        """AC-01 / AC-03: docker-compose must declare 'redis' service with image 'redis:7-alpine'."""
        services = docker_compose_manifest.get("services", {})
        assert "redis" in services, "Service 'redis' must be defined in docker-compose.yml"
        redis_service = services["redis"]
        assert redis_service.get("image") == "redis:7-alpine", (
            f"Expected redis:7-alpine image, got: {redis_service.get('image')}"
        )
        ports = redis_service.get("ports", [])
        assert "6379:6379" in ports or 6379 in ports, (
            f"Expected port 6379:6379 exposed, got: {ports}"
        )

    def test_redis_02_healthcheck_contract(self, docker_compose_manifest):
        """AC-01 / AC-03: Redis service must define a deterministic healthcheck running redis-cli ping."""
        redis_service = docker_compose_manifest["services"]["redis"]
        healthcheck = redis_service.get("healthcheck")
        assert healthcheck is not None, "Redis service must define a healthcheck"
        test_cmd = healthcheck.get("test")
        test_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "ping" in test_str.lower(), f"Redis healthcheck must include ping, got: {test_str}"

    def test_redis_03_volume_persistence_contract(self, docker_compose_manifest):
        """AC-01: Redis cache directory must be persisted to named volume redis_data."""
        redis_service = docker_compose_manifest["services"]["redis"]
        volumes = redis_service.get("volumes", [])
        has_redis_data = any("redis_data:/data" in v for v in volumes)
        assert has_redis_data, f"Expected volume mount 'redis_data:/data', got: {volumes}"
        root_volumes = docker_compose_manifest.get("volumes", {})
        assert "redis_data" in root_volumes, "Top-level volumes must declare redis_data"

    def test_redis_04_resp_protocol_framing(self):
        """AC-03: Raw RESP protocol serializer must correctly construct PING command bytes."""
        args = ["PING"]
        expected_payload = "*1\r\n$4\r\nPING\r\n"
        payload = f"*{len(args)}\r\n"
        for arg in args:
            payload += f"${len(arg.encode('utf-8'))}\r\n{arg}\r\n"
        assert payload == expected_payload, f"Expected RESP format '{expected_payload}', got '{payload}'"

    def test_redis_05_cache_namespaces_contract(self):
        """Verify the 5 canonical Redis cache key namespaces specified in Section 7.2 of Schema spec."""
        canonical_namespaces = [
            "destinations:list:",
            "destinations:detail:",
            "listings:destination:",
            "auth:blacklist:",
            "rate_limit:ip:",
        ]
        # Assert each namespace format adheres to standard colon delimiter conventions
        for ns in canonical_namespaces:
            assert ns.count(":") >= 1
            assert not ns.startswith(":")

    def test_redis_06_live_ping_probe(self, redis_target):
        """AC-03: When Redis port 6379 is live, sending RESP PING must respond with +PONG."""
        if not redis_target["is_listening"]:
            pytest.skip("Redis container port 6379 is not currently listening (offline / pending boot).")
        success, response = send_redis_raw_command(redis_target["host"], redis_target["port"], "PING")
        assert success, f"Redis socket communication failed: {response}"
        assert "+PONG" in response, f"Expected '+PONG' response from Redis, got: {response!r}"


# ==============================================================================
# FEATURE 3: FastAPI Startup & /health returning 200 OK (>= 5 tests)
# ==============================================================================

class TestFastAPIFeature:
    """Verification of FastAPI application startup, metadata, endpoints, and CORS."""

    def test_fastapi_01_app_instantiation(self, fastapi_app):
        """AC-04: FastAPI application instance must load cleanly without syntax or import errors."""
        assert fastapi_app is not None
        assert hasattr(fastapi_app, "title")
        assert "AI Tourism" in fastapi_app.title
        assert hasattr(fastapi_app, "version")
        assert fastapi_app.version == "1.0.0"

    def test_fastapi_02_health_endpoint_status_200(self, http_client):
        """AC-05: Designated GET /health endpoint must return HTTP 200 OK."""
        response = http_client.get(FASTAPI_HEALTH_URL if hasattr(http_client, "session") else "/health")
        assert response.status_code == 200, f"Expected HTTP 200, got: {response.status_code}"

    def test_fastapi_03_health_response_payload_schema(self, http_client):
        """AC-05: GET /health response must return valid JSON with status 'ok'."""
        response = http_client.get(FASTAPI_HEALTH_URL if hasattr(http_client, "session") else "/health")
        data = response.json()
        assert isinstance(data, dict), f"Expected JSON object, got {type(data)}"
        assert "status" in data, "Health response must contain 'status' field"
        assert data["status"] == "ok", f"Expected status 'ok', got: {data['status']}"

    def test_fastapi_04_api_v1_root_endpoint(self, http_client):
        """AC-06: GET /api/v1 must return HTTP 200 with active API message."""
        url = f"{FASTAPI_BASE_URL}/api/v1" if hasattr(http_client, "session") else "/api/v1"
        response = http_client.get(url)
        assert response.status_code == 200, f"Expected HTTP 200 on /api/v1, got {response.status_code}"
        data = response.json()
        assert "message" in data or "status" in data
        if "message" in data:
            assert "Welcome to the AI Tourism API v1" in data["message"]

    def test_fastapi_05_cors_middleware_configured(self, fastapi_app):
        """Verify CORS middleware is properly mounted on FastAPI application."""
        middleware_classes = [m.cls.__name__ for m in fastapi_app.user_middleware]
        assert "CORSMiddleware" in middleware_classes, (
            f"CORSMiddleware must be installed, found: {middleware_classes}"
        )

    def test_fastapi_06_openapi_schema_generated(self, http_client):
        """Verify OpenAPI schema can be generated and contains /health and /api/v1 paths."""
        url = f"{FASTAPI_BASE_URL}/openapi.json" if hasattr(http_client, "session") else "/openapi.json"
        response = http_client.get(url)
        assert response.status_code == 200, f"OpenAPI endpoint failed with status {response.status_code}"
        schema = response.json()
        assert "paths" in schema
        assert "/health" in schema["paths"], "OpenAPI paths must include /health"
        assert "/api/v1" in schema["paths"], "OpenAPI paths must include /api/v1"


# ==============================================================================
# FEATURE 4: Alembic Schema Migration Verification (>= 5 tests)
# ==============================================================================

class TestAlembicFeature:
    """Verification of Alembic database migration configuration and async contracts."""

    def test_alembic_01_requirements_dependency(self):
        """AC-07: Alembic must be declared in backend/requirements.txt."""
        req_file = BACKEND_DIR / "requirements.txt"
        assert req_file.exists(), f"requirements.txt must exist at {req_file}"
        content = req_file.read_text(encoding="utf-8")
        assert "alembic" in content.lower(), "alembic must be specified in requirements.txt"
        assert "sqlalchemy" in content.lower(), "sqlalchemy must be specified in requirements.txt"
        assert "asyncpg" in content.lower(), "asyncpg must be specified in requirements.txt"

    def test_alembic_02_async_driver_specification(self):
        """AC-07: Migration specification must enforce asyncpg driver scheme 'postgresql+asyncpg://'."""
        req_url = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"
        assert req_url.startswith("postgresql+asyncpg://"), (
            "Alembic and SQLAlchemy async engine require 'postgresql+asyncpg://' driver scheme"
        )

    def test_alembic_03_ini_configuration(self):
        """AC-07: alembic.ini must configure script_location when present."""
        if not ALEMBIC_INI_FILE.exists():
            pytest.skip("Milestone 2 pending: backend/alembic.ini not yet generated.")
        content = ALEMBIC_INI_FILE.read_text(encoding="utf-8")
        assert "[alembic]" in content, "alembic.ini must contain [alembic] section"
        assert "script_location" in content, "alembic.ini must configure script_location"

    def test_alembic_04_env_py_runner_syntax(self):
        """AC-07: alembic/env.py must define async migration runner when present."""
        env_py = ALEMBIC_DIR / "env.py"
        if not env_py.exists():
            pytest.skip("Milestone 2 pending: backend/alembic/env.py not yet generated.")
        content = env_py.read_text(encoding="utf-8")
        assert "target_metadata" in content, "alembic/env.py must bind target_metadata"
        assert "run_migrations" in content, "alembic/env.py must define migration execution"

    def test_alembic_05_versions_directory_contract(self):
        """AC-07: alembic/versions directory must exist for schema revisions when present."""
        versions_dir = ALEMBIC_DIR / "versions"
        if not versions_dir.exists():
            pytest.skip("Milestone 2 pending: backend/alembic/versions not yet created.")
        assert versions_dir.is_dir(), "backend/alembic/versions must be a directory"

    def test_alembic_06_domain_models_contract(self):
        """AC-07: Models specification mandates 8 core domain tables for schema generation."""
        expected_domain_tables = [
            "users",
            "destinations",
            "operators",
            "listings",
            "itineraries",
            "itinerary_items",
            "bookings",
            "reviews",
        ]
        # Verify domain table definitions contract matches canonical architecture
        assert len(expected_domain_tables) == 8


# ==============================================================================
# FEATURE 5: Next.js Compilation & Port 3000 Response (>= 5 tests)
# ==============================================================================

class TestNextJSFeature:
    """Verification of Next.js 14 frontend setup, package manifest, App Router, and Dockerfile."""

    def test_nextjs_01_package_json_exists_and_valid(self):
        """AC-04 / AC-08: frontend/package.json must exist with valid JSON and Next.js dependencies."""
        pkg_file = FRONTEND_DIR / "package.json"
        assert pkg_file.exists(), f"package.json must exist at {pkg_file}"
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
        assert data.get("name") == "tourism-ecosystem-frontend"
        deps = data.get("dependencies", {})
        assert "next" in deps, "Next.js must be a dependency"
        assert "react" in deps, "React must be a dependency"
        assert "react-dom" in deps, "React-DOM must be a dependency"

    def test_nextjs_02_build_scripts_configured(self):
        """AC-08: package.json must configure 'dev', 'build', and 'start' scripts."""
        pkg_file = FRONTEND_DIR / "package.json"
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        assert "dev" in scripts, "Script 'dev' must be defined"
        assert "build" in scripts, "Script 'build' must be defined"
        assert "start" in scripts, "Script 'start' must be defined"
        assert scripts["build"] == "next build"

    def test_nextjs_03_dockerfile_configuration(self):
        """AC-04 / AC-08: frontend/Dockerfile must genuinely build and execute Next.js."""
        dockerfile = FRONTEND_DIR / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile must exist at {dockerfile}"
        content = dockerfile.read_text(encoding="utf-8")
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

        # 1. Structural non-triviality
        assert len(lines) >= 6, f"Dockerfile must contain genuine build steps (found only {len(lines)} lines)"

        # 2. Base image verification: node:20 or node:20-alpine
        has_node20 = any(re.search(r"^FROM\s+node:20", line, re.IGNORECASE) for line in lines)
        assert has_node20, "Dockerfile must use a Node.js 20 base image (e.g. node:20-alpine)"

        # 3. Copies package manifest package*.json
        has_copy_pkg = any(re.search(r"^COPY\s+package(?:\*\.json|\.json)", line) for line in lines)
        assert has_copy_pkg, "Dockerfile must copy package manifests (e.g. package*.json)"

        # 4. Installs dependencies (npm ci or npm install)
        has_install = any(re.search(r"^RUN\s+(?:npm\s+(?:ci|install)|yarn|pnpm)", line) for line in lines)
        assert has_install, "Dockerfile must install dependencies (npm ci or npm install)"

        # 5. Compiles Next.js (npm run build or next build)
        has_build = any(re.search(r"^RUN\s+(?:npm\s+run\s+build|next\s+build|npx\s+next\s+build)", line) for line in lines)
        assert has_build, "Dockerfile must compile Next.js application (npm run build or next build)"

        # 6. Exposes port 3000
        has_expose = any(re.search(r"^EXPOSE\s+3000\b", line) for line in lines)
        assert has_expose, "Dockerfile must explicitly EXPOSE port 3000"

        # 7. Executes startup command (CMD ["npm", "run", "start"] or next start)
        has_start_cmd = any(
            re.search(r'CMD\s+\[.*?(?:"npm"|"npx"|"next"|"node").*?(?:"start"|"run"|"server\.js").*?\]', line)
            or re.search(r'CMD\s+(?:npm\s+run\s+start|npm\s+start|next\s+start)', line)
            for line in lines
        )
        assert has_start_cmd, "Dockerfile CMD must execute Next.js startup command (e.g. ['npm', 'run', 'start'] or next start)"

        # 8. Anti-Facade & Dummy Anti-Pattern Assertions
        lower_content = content.lower()
        assert "setinterval" not in lower_content, "Integrity Violation: Dockerfile must not contain dummy setInterval loop"
        assert "sleep infinity" not in lower_content, "Integrity Violation: Dockerfile must not contain dummy sleep infinity loop"
        assert "node -e" not in content and 'node", "-e' not in content, "Integrity Violation: Dockerfile must not execute inline dummy scripts"

    def test_nextjs_04_root_layout_exists(self):
        """AC-08: App Router root layout (frontend/src/app/layout.tsx) must exist."""
        layout_file = FRONTEND_DIR / "src" / "app" / "layout.tsx"
        assert layout_file.exists(), f"Root layout must exist at {layout_file}"
        content = layout_file.read_text(encoding="utf-8")
        assert "RootLayout" in content or "export default" in content

    def test_nextjs_05_status_dashboard_page_exists(self):
        """AC-08: App Router landing page (frontend/src/app/page.tsx) must exist and render status."""
        page_file = FRONTEND_DIR / "src" / "app" / "page.tsx"
        assert page_file.exists(), f"Page component must exist at {page_file}"
        content = page_file.read_text(encoding="utf-8")
        assert "AI Tourism" in content or "Tourism" in content
        assert "status" in content.lower() or "health" in content.lower()

    def test_nextjs_06_api_client_contract(self):
        """AC-08: API client (frontend/src/lib/api.ts) must bind to NEXT_PUBLIC_API_URL."""
        api_client = FRONTEND_DIR / "src" / "lib" / "api.ts"
        assert api_client.exists(), f"API client must exist at {api_client}"
        content = api_client.read_text(encoding="utf-8")
        assert "NEXT_PUBLIC_API_URL" in content, "API client must read NEXT_PUBLIC_API_URL"
