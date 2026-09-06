# Project: AI Tourism Ecosystem (Phase 0: Product Foundation)

## Architecture
The AI Tourism Ecosystem is structured as a **Modular Monolith** designed for high scalability, developer velocity, and seamless evolution toward microservices.

```
+-------------------------------------------------------------------------+
|                           FRONTEND LAYER                                |
|   Next.js 14+ (App Router, TypeScript, Tailwind CSS)                    |
|   - Port 3000                                                           |
|   - Health & Status Dashboard                                           |
|   - API Client targeting NEXT_PUBLIC_API_URL                            |
+------------------------------------+------------------------------------+
                                     | HTTP REST (:3000 -> :8000)
                                     v
+------------------------------------+------------------------------------+
|                         BACKEND API LAYER                               |
|   FastAPI Application (Port 8000)                                       |
|   +-------------------------------------------------------------------+ |
|   | Core: Config (pydantic-settings), CORS, Database, Redis           | |
|   | API v1: /health (active DB/Redis ping), /api/v1 (API root)        | |
|   | Domain Models: Users, Destinations, Operators, Listings,          | |
|   |                Itineraries, Bookings, Reviews                     | |
|   | Migrations: Alembic async (alembic/env.py -> Base.metadata)       | |
|   +-------------------------------------------------------------------+ |
+------------------------------------+------------------------------------+
                                     |
              +----------------------+----------------------+
              | (SQL :5432)                                 | (Redis Protocol :6379)
              v                                             v
+-------------+-----------------------------+ +-------------+---------------------+
|      PERSISTENCE DATA STORE               | |            CACHE & QUEUE          |
|  PostgreSQL 15 (Alpine)                   | |  Redis 7 (Alpine)                 |
|  - Database: tourism_db                   | |  - Key-Value Cache                |
|  - Port: 5432                             | |  - Port: 6379                     |
|  - Volume: postgres_data                  | |  - Volume: redis_data             |
+-------------------------------------------+ +-----------------------------------+
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | PostgreSQL 15 Container | PostgreSQL 15 Alpine data store with healthcheck & volume persistence | M1 | Blueprints / docker-compose |
| 2 | Redis 7 Container | Redis 7 Alpine cache store with healthcheck & volume persistence | M1 | Blueprints / docker-compose |
| 3 | Compose Orchestration | Multi-container compose definition with health dependencies | M1 | Blueprints / docker-compose |
| 4 | Configuration Management | Pydantic-settings `app/core/config.py` loading .env and env vars | M2 | Blueprints / Backend spec |
| 5 | Async Database Engine | SQLAlchemy 2.0 `create_async_engine` and `async_sessionmaker` with asyncpg | M2 | Blueprints / Schema spec |
| 6 | Domain Models | SQLAlchemy 2.0 declarative models (User, Destination, Operator, Listing, Itinerary, Booking, Review) | M2 | Schema spec |
| 7 | Alembic Async Migrations | Alembic configured with `env.py` async runner generating initial schema | M2 | User Request R2 / AC-3 |
| 8 | FastAPI Application Skeleton | Modular FastAPI entrypoint, router mounting, lifespan management | M2 | User Request R2 / AC-2 |
| 9 | Health Check Endpoint | `GET /health` with DB `SELECT 1` and Redis `PING` probes returning 200 OK | M2 | User Request AC-2 |
| 10 | API Root Endpoint | `GET /api/v1` returning API status & version information | M2 | Blueprints spec |
| 11 | CORS Middleware | Configured CORS middleware allowing frontend communication | M2 | Blueprints spec |
| 12 | Backend Test Suite | Pytest test suite covering health endpoints and database connectivity | M2 | Verification |
| 13 | Next.js 14 Skeleton | Next.js 14 App Router project with TypeScript, Tailwind CSS | M3 | User Request R2 / AC-4 |
| 14 | Frontend Dockerfile | Production/Dev Dockerfile building frontend container on port 3000 | M3 | User Request AC-4 / docker-compose |
| 15 | Status & Health Dashboard | Next.js UI consuming `/health` and rendering system operational status | M3 | Blueprints spec |
| 16 | Frontend Build Cleanliness | Clean compilation (`npm run build` exit code 0) without type errors | M3 | User Request AC-4 |
| 17 | E2E Test Suite | Independent opaque-box test suite (Tiers 1-4) | E2E Track | Project Pattern |
| 18 | Multi-Container E2E Boot | `docker-compose up -d` starting all services cleanly | M4 | User Request AC-1 |
| 19 | Adversarial Hardening | Tier 5 adversarial edge cases testing and hardening | M4 | Project Pattern |
| 20 | Forensic Integrity Audit | Systematic integrity audit verifying genuine implementation | M4 | Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Database & Infra Foundation | Redis healthcheck in docker-compose.yml, container startup & connectivity verification | None | PLANNED |
| M2 | Backend Skeleton & Alembic | Modular package structure, Pydantic settings, SQLAlchemy async engine, domain models, Alembic migrations, `/health` endpoint, pytest | M1 | PLANNED |
| M3 | Frontend Skeleton | Next.js 14 App Router skeleton, Dockerfile, Status Dashboard, build verification | None | PLANNED |
| E2E | E2E Testing Suite | Independent opaque-box test infrastructure and Tiers 1-4 test cases | None | PLANNED |
| M4 | Final Integration & Audit | 100% E2E test suite pass across all containers, Tier 5 hardening, Forensic Integrity Audit | M1, M2, M3, E2E | PLANNED |

## Interface Contracts
### Backend (`backend/app/main.py`) ↔ Frontend (`frontend/src/`)
- Base URL: `http://localhost:8000` (or `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`)
- Health Check: `GET /health`
  - Response (200 OK):
    ```json
    {
      "status": "ok",
      "version": "1.0.0",
      "services": {
        "database": "healthy",
        "redis": "healthy"
      }
    }
    ```
- API Root: `GET /api/v1`
  - Response (200 OK):
    ```json
    {
      "message": "Welcome to the AI Tourism API v1",
      "status": "active"
    }
    ```

### Backend (`app/core/database.py`) ↔ PostgreSQL (`postgres:5432`)
- Connection String: `postgresql+asyncpg://tourism_user:tourism_password@postgres:5432/tourism_db` (inside docker) or `localhost:5432` (host)
- Driver: `asyncpg`
- Protocol: Asynchronous SQLAlchemy 2.0 `AsyncSession`

### Backend (`app/core/redis.py`) ↔ Redis (`redis:6379`)
- Connection String: `redis://redis:6379/0` (inside docker) or `redis://localhost:6379/0` (host)
- Driver: `redis.asyncio`

### Alembic (`backend/alembic/env.py`) ↔ Models (`backend/app/models/`)
- Target Metadata: `target_metadata = Base.metadata`
- Model Registry: `app/models/__init__.py` imports all declarative models
- Async Migration: `async_engine_from_config` executing `connection.run_sync(do_run_migrations)`

## Code Layout
```
tourism-ecosystem/
├── docker-compose.yml              # M1: Multi-container topology
├── ORIGINAL_REQUEST.md             # Project requirements
├── PROJECT.md                      # Global architecture & milestone tracking
├── TEST_INFRA.md                   # E2E test suite architecture & feature inventory
├── TEST_READY.md                   # Published when E2E test suite is complete
├── backend/                        # M2: FastAPI modular monolith
│   ├── Dockerfile                  # Python 3.11 container definition
│   ├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, Alembic, pytest, etc.)
│   ├── alembic.ini                 # Alembic migration configuration
│   ├── alembic/                    # Migration scripts
│   │   ├── env.py                  # Async Alembic runner
│   │   └── versions/               # Generated schema revisions
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application factory
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings
│   │   │   ├── database.py         # SQLAlchemy async engine & session
│   │   │   └── redis.py            # Redis client connection factory
│   │   ├── models/
│   │   │   ├── __init__.py         # Model exports for Alembic
│   │   │   ├── base.py             # DeclarativeBase with common fields
│   │   │   ├── user.py
│   │   │   ├── destination.py
│   │   │   ├── operator.py
│   │   │   ├── listing.py
│   │   │   ├── itinerary.py
│   │   │   ├── booking.py
│   │   │   └── review.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── v1/
│   │           ├── router.py
│   │           └── endpoints/
│   │               └── health.py
│   └── tests/                      # Unit & integration tests
│       ├── conftest.py
│       └── test_health.py
├── frontend/                       # M3: Next.js 14 App Router
│   ├── Dockerfile                  # Node.js container definition
│   ├── package.json                # Next.js dependencies & scripts
│   ├── tsconfig.json               # TypeScript configuration
│   ├── next.config.js              # Next.js configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   ├── postcss.config.js           # PostCSS configuration
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx          # Root layout
│   │   │   ├── page.tsx            # Main page & Status dashboard
│   │   │   └── globals.css         # Global styling
│   │   └── lib/
│   │       └── api.ts              # API client wrapper
└── tests/                          # E2E Test Suite (Opaque-box)
    ├── e2e_runner.py               # E2E test runner
    └── test_cases/                 # Tiers 1-4 test cases
```
