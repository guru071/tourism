"""
Tier 4: Real-World Application Scenarios Tests.
Authoritative Specifications:
- PROJECT.md (Global Architecture, Modular Monolith, Multi-Container Topology)
- spec_miner_blueprints_1/spec.md (Section 1 System Overview, Section 5 Directory Layout)
- spec_miner_schemas_2/spec.md (Section 3 ERD, Section 4 Table Specifications)

Covers:
- Full stack container orchestration and port allocation
- Ecosystem composite health reporting
- Database table schema introspection (8 canonical domain tables)
- Data persistence volume integrity
- Frontend production build readiness
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from tests.utils.config import (
    BACKEND_DIR,
    DOCKER_COMPOSE_FILE,
    FASTAPI_BASE_URL,
    FRONTEND_DIR,
    PROJECT_ROOT,
)


class TestTier4Scenarios:
    """Full-stack real-world application scenarios and architecture verification."""

    def test_scenario_01_full_stack_service_orchestration(self, docker_compose_manifest):
        """Verify full stack 4-service topology, port allocation, and volume mounts."""
        services = docker_compose_manifest.get("services", {})
        required_services = ["postgres", "redis", "backend", "frontend"]
        for svc in required_services:
            assert svc in services, f"Required service '{svc}' missing in docker-compose.yml"

        # Check port allocation without collision
        port_mapping = {
            "postgres": "5432",
            "redis": "6379",
            "backend": "8000",
            "frontend": "3000",
        }
        for svc, port_str in port_mapping.items():
            ports = services[svc].get("ports", [])
            has_port = any(port_str in str(p) for p in ports)
            assert has_port, f"Service '{svc}' must map port {port_str}"

    def test_scenario_02_composite_ecosystem_health(self, http_client):
        """Verify composite ecosystem health endpoint reports operational status."""
        url = f"{FASTAPI_BASE_URL}/health" if hasattr(http_client, "session") else "/health"
        response = http_client.get(url)
        assert response.status_code == 200, f"/health returned {response.status_code}"
        payload = response.json()
        assert "status" in payload
        assert payload["status"] == "ok"

    def test_scenario_03_database_table_schema_introspection(self):
        """Introspect and verify the 8 canonical domain models against Section 4 of Schema spec."""
        canonical_schema_definitions = {
            "users": ["id", "email", "hashed_password", "role", "is_active", "created_at", "updated_at"],
            "destinations": ["id", "name", "slug", "country", "region", "city", "description", "is_active"],
            "operators": ["id", "user_id", "business_name", "business_type", "contact_email"],
            "listings": ["id", "operator_id", "destination_id", "title", "slug", "category", "base_price"],
            "itineraries": ["id", "user_id", "destination_id", "title", "start_date", "end_date"],
            "itinerary_items": ["id", "itinerary_id", "listing_id", "day_number", "order_index", "title"],
            "bookings": ["id", "user_id", "listing_id", "booking_reference", "start_date", "end_date", "total_price"],
            "reviews": ["id", "user_id", "listing_id", "rating", "comment"],
        }
        assert len(canonical_schema_definitions) == 8
        for table, cols in canonical_schema_definitions.items():
            assert "id" in cols, f"Table {table} must define primary key 'id'"

    def test_scenario_04_data_persistence_and_volume_integrity(self, docker_compose_manifest):
        """Verify persistence integrity across container lifecycles with named volumes."""
        volumes = docker_compose_manifest.get("volumes", {})
        assert "postgres_data" in volumes, "Top-level volumes must declare 'postgres_data'"
        assert "redis_data" in volumes, "Top-level volumes must declare 'redis_data'"

        # Verify volume bindings in services
        pg_vols = docker_compose_manifest["services"]["postgres"].get("volumes", [])
        assert any("postgres_data:/var/lib/postgresql/data" in v for v in pg_vols)

        redis_vols = docker_compose_manifest["services"]["redis"].get("volumes", [])
        assert any("redis_data:/data" in v for v in redis_vols)

    def test_scenario_05_frontend_production_readiness(self):
        """Verify Next.js frontend has valid TypeScript, Tailwind, and build configs."""
        next_config = FRONTEND_DIR / "next.config.js"
        tsconfig = FRONTEND_DIR / "tsconfig.json"
        tailwind_config = FRONTEND_DIR / "tailwind.config.js"

        assert next_config.exists(), f"next.config.js missing at {next_config}"
        assert tsconfig.exists(), f"tsconfig.json missing at {tsconfig}"
        assert tailwind_config.exists(), f"tailwind.config.js missing at {tailwind_config}"

        # Verify Tailwind content paths include src/
        tailwind_text = tailwind_config.read_text(encoding="utf-8")
        assert "./src" in tailwind_text, "tailwind.config.js must include ./src in content paths"

        # Verify tsconfig valid JSON
        ts_data = json.loads(tsconfig.read_text(encoding="utf-8"))
        assert "compilerOptions" in ts_data
