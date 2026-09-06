# Test Infrastructure Specification: AI Tourism Ecosystem (Phase 0)

## 1. Test Philosophy & Architecture

The AI Tourism Ecosystem E2E Test Suite adopts an **Opaque-Box, Requirement-Driven** verification methodology. In alignment with the foundational acceptance criteria and architectural blueprints, testing is performed strictly against public interfaces, network boundaries, published protocol contracts, and external system ports.

### Principles
1. **Opaque-Box Decoupling**: Tests do not bind to internal transient implementation details. They assert system invariants across defined entrypoints:
   - PostgreSQL wire protocol & SQL interface (Port 5432)
   - Redis RESP protocol & command interface (Port 6379)
   - FastAPI REST API HTTP contract (Port 8000: `/health`, `/api/v1`, OpenAPI schema)
   - Next.js Web Application HTTP contract (Port 3000: UI endpoints, status dashboard, compilation bundles)
   - Alembic migration environment & schema state
2. **Deterministic & Self-Contained**: Every test manages its own preconditions, execution bounds, timeouts, and state verification. Tests execute reliably across native host environments, virtual environments, and container runtimes.
3. **Multi-Mode Execution**: The test suite is dual-executable:
   - **Pytest Native**: `pytest tests/`
   - **Standalone Runner**: `python tests/e2e_runner.py` with zero mandatory third-party runtime requirements (gracefully leveraging standard library `urllib`, `socket`, `json`, `unittest` while utilizing `requests`, `pytest`, `asyncpg`, or `redis` when installed).
4. **Resilient Failure Reporting**: Clear diagnostic reporting mapping failures directly to architectural requirements (AC-01 through AC-08).

---

## 2. Feature Inventory & Tier Mapping

| Feature Key | Description | Target Port / Interface | Target Tier | Acceptance Criteria Ref |
|---|---|---|---|---|
| `postgres_connectivity` | PostgreSQL 15 connection, protocol handshake, credential authentication, SQL execution | Port 5432 / TCP | Tier 1, Tier 2, Tier 3, Tier 4 | AC-01, AC-02 |
| `redis_ping` | Redis 7 RESP protocol handshake, PING/PONG responsiveness, set/get memory cache operations | Port 6379 / TCP | Tier 1, Tier 2, Tier 3, Tier 4 | AC-01, AC-03 |
| `fastapi_startup_health` | FastAPI HTTP daemon startup, `/health` deep healthcheck probe returning 200 OK with dependency status | Port 8000 / HTTP | Tier 1, Tier 2, Tier 3, Tier 4 | AC-04, AC-05 |
| `alembic_schema_migration` | Alembic migration configuration, revision generation, table schema evolution and discovery | CLI / DB Schema | Tier 1, Tier 3, Tier 4 | AC-07 |
| `nextjs_compilation_port` | Next.js 14 compilation, App Router page rendering, HTTP 200 on port 3000 | Port 3000 / HTTP | Tier 1, Tier 2, Tier 3, Tier 4 | AC-08 |
| `api_root_and_openapi` | FastAPI `/api/v1` root endpoint and OpenAPI `/docs` / `/openapi.json` contract verification | Port 8000 / HTTP | Tier 1, Tier 2 | AC-06 |
| `cors_headers` | CORS preflight and access-control headers matching frontend origins | Port 8000 / HTTP | Tier 2, Tier 3 | AC-05, Blueprints |
| `frontend_to_backend_bridge` | Next.js UI integration with backend `/health` and `/api/v1` | Port 3000 -> 8000 | Tier 3, Tier 4 | Blueprints |
| `schema_introspection` | PostgreSQL physical schema introspection verifying tables (`users`, `destinations`, etc.) | Port 5432 / SQL | Tier 3, Tier 4 | Schemas Spec |
| `full_stack_orchestration` | Comprehensive end-to-end health probe across all 4 system tiers simultaneously | Full Stack | Tier 4 | AC-01 to AC-08 |

---

## 3. Test Tier Breakdown

### Tier 1: Feature Coverage (Baseline Functionality)
Requires >= 5 independent test cases per primary feature:
1. **PostgreSQL Connectivity (>=5 tests)**:
   - `test_pg_tcp_socket_listening`: TCP socket connection to PostgreSQL port 5432.
   - `test_pg_protocol_handshake`: Verification of PostgreSQL wire protocol responsiveness.
   - `test_pg_authentication_contract`: Connection with configured credentials (`tourism_user` / `tourism_password`).
   - `test_pg_basic_query_execution`: Execution of `SELECT 1` scalar verification query.
   - `test_pg_database_name_validation`: Verification that target catalog `tourism_db` exists and is queryable.
2. **Redis PING & Cache (>=5 tests)**:
   - `test_redis_tcp_socket_listening`: TCP socket connection to Redis port 6379.
   - `test_redis_ping_pong_protocol`: Verification of raw `*1\r\n$4\r\nPING\r\n` -> `+PONG\r\n` protocol response.
   - `test_redis_key_set_and_get`: Set and get a test key in Redis cache.
   - `test_redis_key_expiry_ttl`: Key expiration and TTL validation.
   - `test_redis_info_server`: Redis INFO command server response and version verification.
3. **FastAPI Startup & Health Endpoint (>=5 tests)**:
   - `test_fastapi_tcp_socket_listening`: TCP socket connection to FastAPI port 8000.
   - `test_fastapi_health_endpoint_status_200`: `GET /health` returns HTTP 200 OK.
   - `test_fastapi_health_payload_schema`: JSON payload matches `{status: "ok", ...}` contract.
   - `test_fastapi_health_services_breakdown`: Response includes individual `database` and `redis` health checks.
   - `test_fastapi_api_v1_root`: `GET /api/v1` returns HTTP 200 with active status message.
   - `test_fastapi_openapi_spec`: `GET /openapi.json` returns valid OpenAPI 3.x schema definition.
4. **Alembic Schema Migration Verification (>=5 tests)**:
   - `test_alembic_ini_configuration`: Existence and valid configuration of `alembic.ini`.
   - `test_alembic_env_py_syntax`: Validation of `alembic/env.py` async migration runner syntax.
   - `test_alembic_model_metadata_import`: Validation of `Base.metadata` containing core domain models.
   - `test_alembic_migration_versions_exist`: Presence of schema revision migration scripts in `alembic/versions/`.
   - `test_alembic_database_schema_version_table`: Verification of `alembic_version` table in database.
5. **Next.js Compilation & Port 3000 Response (>=5 tests)**:
   - `test_nextjs_tcp_socket_listening`: TCP socket connection to Next.js port 3000.
   - `test_nextjs_root_endpoint_http_200`: `GET /` returns HTTP 200 OK with HTML document.
   - `test_nextjs_html_contains_title`: Root page HTML contains page title / AI Tourism branding.
   - `test_nextjs_health_or_status_dashboard`: Status / health page responds with HTTP 200 or dashboard components.
   - `test_nextjs_static_assets_routing`: Verification that static route assets or favicon respond properly.

### Tier 2: Boundary & Corner Cases
Tests system resilience under adverse or unexpected input conditions:
1. **Invalid HTTP Endpoints**: Requests to non-existent backend routes (`/api/v1/invalid_route_404`) return HTTP 404 Not Found with clean JSON error structure.
2. **Unsupported HTTP Methods**: Sending `POST` or `DELETE` to read-only endpoints (`/health`, `/api/v1`) returns HTTP 405 Method Not Allowed.
3. **Malformed JSON Payloads**: Sending invalid or truncated JSON to API routes returns HTTP 422 Unprocessable Entity or HTTP 400 Bad Request.
4. **CORS Preflight & Header Boundaries**: `OPTIONS` requests with custom origin headers return appropriate `Access-Control-Allow-Origin` and `Access-Control-Allow-Methods`.
5. **Connection Retry & Timeout Resilience**: Simulated network timeouts and retry logic handle intermittent delays gracefully.

### Tier 3: Cross-Feature Combinations
Tests interaction between multiple stack components:
1. **Frontend to Backend Bridge**: Frontend API client or server component successfully probes backend `/health` and consumes `/api/v1`.
2. **Backend to PostgreSQL Query Bridge**: FastAPI executes async SQL queries against PostgreSQL pool without connection leak.
3. **Backend to Redis Cache Bridge**: FastAPI executes Redis operations (`PING`, `SET`, `GET`) via async connection pool.
4. **Alembic Migration Against PostgreSQL**: Migration scripts successfully create or verify database tables in PostgreSQL.
5. **Simulated Dependency Degradation**: When a dependency (database or cache) is unavailable or mock-failed, `/health` reports degraded state with HTTP 503.

### Tier 4: Real-World Application Scenarios
Tests full-system workflows:
1. **Full-Stack Orchestration Verification**: End-to-end traversal validating PostgreSQL, Redis, FastAPI, and Next.js concurrently.
2. **Ecosystem Health Reporting**: Comprehensive health probe evaluating composite health status across all sub-services.
3. **Database Table Schema Introspection**: Verification that all 8 core domain tables (`users`, `destinations`, `operators`, `listings`, `itineraries`, `itinerary_items`, `bookings`, `reviews`) are properly registered and configured with expected column constraints.

---

## 4. Test Directory Layout

```
tests/
├── __init__.py
├── conftest.py                     # Pytest shared fixtures, configuration & connection hooks
├── e2e_runner.py                   # Standalone test runner (CLI & automated reporting)
├── test_cases/
│   ├── __init__.py
│   ├── test_tier1_features.py      # Tier 1: Feature coverage (>=5 tests per feature)
│   ├── test_tier2_boundaries.py    # Tier 2: Boundary & corner cases
│   ├── test_tier3_combinations.py  # Tier 3: Cross-feature integrations
│   └── test_tier4_scenarios.py     # Tier 4: Full stack application scenarios
└── utils/
    ├── __init__.py
    ├── config.py                   # Test target URLs and port configs
    └── probes.py                   # Wire protocol & HTTP probes (dual standard lib / requests)
```

---

## 5. Execution Instructions

### Option A: Pytest (Standard Test Runner)
```bash
# Run entire test suite
pytest tests/ -v

# Run specific tier
pytest tests/test_cases/test_tier1_features.py -v
pytest tests/test_cases/test_tier2_boundaries.py -v
pytest tests/test_cases/test_tier3_combinations.py -v
pytest tests/test_cases/test_tier4_scenarios.py -v
```

### Option B: Standalone E2E Runner (Zero Dependency Fallback)
```bash
# Execute standalone runner
python tests/e2e_runner.py

# Optional flags:
python tests/e2e_runner.py --tier 1
python tests/e2e_runner.py --json-report tests/report.json
```

---

## 6. Coverage Thresholds & Success Criteria

- **Tier 1 Feature Coverage**: 100% of defined Tier 1 tests must pass (at least 5 tests per primary feature: PostgreSQL, Redis, FastAPI, Alembic, Next.js).
- **Tier 2 Boundary Cases**: 100% of boundary and corner cases must pass.
- **Tier 3 Combinations**: 100% of cross-feature integration tests must pass.
- **Tier 4 Scenarios**: 100% of end-to-end orchestration scenarios must pass.
- **Total Test Count**: Minimum 30 independent test cases across all tiers.
