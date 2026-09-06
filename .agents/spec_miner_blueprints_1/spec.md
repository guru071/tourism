# AI Tourism Ecosystem — Phase 0 (Product Foundation) Specification

## 1. Executive Summary & System Overview

The **AI Tourism Operating System (Ecosystem)** is an intelligent, scalable platform designed to unify destination management, AI-driven personalized itineraries, local vendor commerce, and visitor experiences. 

For **Phase 0 (Product Foundation)**, the project establishes a robust, extensible **Modular Monolith** architecture. This foundation provides the infrastructure, data layer, backend application skeleton, and frontend application skeleton necessary to support subsequent vertical feature slices (Destinations, Itineraries, AI Recommender Engine, Vendor Portals, and Bookings).

### Core Goals for Phase 0
1. **Containerized Infrastructure**: Orchestrate PostgreSQL 15 and Redis 7 via Docker Compose with deterministic health checks and persistent storage.
2. **Backend Application Skeleton**: Deploy an asynchronous FastAPI service structured as a modular monolith with Pydantic v2 settings, async SQLAlchemy 2.0 session handling, structured logging, and verified `/health` endpoints.
3. **Database Migration Framework**: Configure Alembic with async SQLAlchemy support to establish reproducible, version-controlled schema migrations based on declarative ORM models.
4. **Frontend Application Skeleton**: Establish a Next.js frontend application capable of compiling cleanly, connecting to the backend via `NEXT_PUBLIC_API_URL`, and rendering baseline application routes.

---

## 2. Architecture & Modular Monolith Boundaries

The AI Tourism Ecosystem follows a **Modular Monolith** architectural pattern. All core business modules reside within a unified codebase and runtime during Phase 0 to Phase 2, maintaining strict logical boundaries via distinct module directories, explicit interface boundaries, and isolated data access patterns.

```
+-------------------------------------------------------------------------+
|                           FRONTEND LAYER                                |
|   Next.js 14+ (React, TypeScript / JavaScript, Tailwind CSS)            |
|   - App Router / Pages: Home, Health Dashboard, Destination Explorer    |
|   - API Client: Axios / Fetch communicating with Backend REST API       |
+------------------------------------+------------------------------------+
                                     | HTTP / JSON (:3000 -> :8000)
                                     v
+------------------------------------+------------------------------------+
|                         BACKEND API LAYER                               |
|   FastAPI Application (:8000)                                           |
|   +-------------------------------------------------------------------+ |
|   | App Core: Config (pydantic-settings), CORS, Logging, Exception Handlers|
|   +-------------------------------------------------------------------+ |
|   | System Endpoints: GET /health, GET /api/v1                        | |
|   +-------------------------------------------------------------------+ |
|   | Modular Domain Boundaries (Future Expansion Modules):             | |
|   | - Destinations & Points of Interest (POIs)                        | |
|   | - Users & Auth                                                    | |
|   | - Itineraries & AI Recommendations                                | |
|   | - Vendors & Bookings                                              | |
|   +-------------------------------------------------------------------+ |
|   | Data Layer: SQLAlchemy 2.0 Async Engine, AsyncSession, Declarative Base |
|   | Migrations: Alembic async migrations environment                   |
+------------------------------------+------------------------------------+
                                     |
              +----------------------+----------------------+
              |                                             |
              v (SQL / asyncpg :5432)                       v (Redis Protocol :6379)
+-------------+-----------------------------+ +-------------+---------------------+
|      PERSISTENCE DATA STORE               | |            CACHE & QUEUE          |
|  PostgreSQL 15 (Alpine)                   | |  Redis 7 (Alpine)                 |
|  - Database: tourism_db                   | |  - Key-Value Cache                |
|  - User: tourism_user                     | |  - Session / Rate-Limiting Store  |
|  - Volumes: postgres_data                 | |  - Volume: redis_data             |
+-------------------------------------------+ +-----------------------------------+
```

### Module Boundaries Breakdown

1. **Database & Infrastructure Module**:
   - **PostgreSQL 15**: Primary relational data store for structured domain entities (users, destinations, attractions, itineraries, bookings).
   - **Redis 7**: High-performance in-memory cache for session tokens, AI response caching, rate limiting, and ephemeral search states.
   - **Docker Compose**: Single command orchestration (`docker-compose up -d`) encapsulating container lifecycle, volume persistence (`postgres_data`, `redis_data`), and container networking.

2. **Backend Module (`/backend`)**:
   - **Core Subsystem**:
     - `app/core/config.py`: Centralized environment configuration via Pydantic `BaseSettings`.
     - `app/core/database.py`: Async engine creation (`create_async_engine`), scoped async sessionmaker (`AsyncSession`), declarative base (`Base`), and dependency injection helper `get_db()`.
     - `app/core/redis.py`: Async Redis client connection factory (`redis.asyncio`).
   - **API Subsystem**:
     - `app/api/v1/`: Versioned API router mounting endpoint modules.
     - `app/main.py`: Application entrypoint configuring CORS, routers, lifespan/events, and health check.
   - **Database Migrations Subsystem (`alembic/`)**:
     - `alembic.ini`: Configuration file pointing to migration scripts and async database URL.
     - `alembic/env.py`: Asynchronous migration runner importing SQLAlchemy `Base.metadata` to support `autogenerate`.
     - `alembic/versions/`: Chronological migration scripts tracking schema evolution.

3. **Frontend Module (`/frontend`)**:
   - Next.js application running on port 3000.
   - Built with modern React standards, handling client-side and server-side data fetching.
   - Configured with environment variable `NEXT_PUBLIC_API_URL` targeting `http://localhost:8000/api/v1`.

---

## 3. Technology Stack Specification

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Runtime / OS | Python | 3.11-slim | Backend containerized runtime |
| Web Framework | FastAPI | 0.110.0 | High-performance asynchronous REST API |
| ASGI Server | Uvicorn | 0.27.1 | Production ASGI server with hot reloading |
| ORM | SQLAlchemy | 2.0.28 | Modern async declarative ORM |
| Database Driver | asyncpg | 0.29.0 | High-performance async PostgreSQL driver |
| Database Migration | Alembic | 1.13.1 | Database schema migrations and revision control |
| Validation & Settings | Pydantic / Pydantic-Settings | 2.6.4 / 2.2.1 | Data validation and type-safe environment configuration |
| Cache Client | redis-py | 5.0.3 | Asynchronous Redis client |
| Primary Database | PostgreSQL | 15-alpine | Relational persistence |
| Cache Store | Redis | 7-alpine | In-memory key-value cache |
| Frontend Framework | Next.js | 14.x | React framework for web UI |
| Containerization | Docker & Docker Compose | Compose v2 / 3.8 | Multi-container development and deployment |

---

## 4. Phase 0 Detailed Requirements & Acceptance Criteria

### Requirement R1: Digest Documentation & Split Work
- **Description**: Read and assimilate system blueprints, decompose architectural responsibilities across Database, Backend, and Frontend modules, and provide clean interfaces between services.
- **Verification**: Architectural specifications and module boundaries fully documented and referenced in project artifacts.

### Requirement R2: Foundational Build (Modular Monolith)
- **Description**: Construct the Phase 0 containerized environment, database migrations, backend skeleton, and frontend skeleton.

### Acceptance Criteria

| Criteria ID | Requirement | Verification Condition |
|---|---|---|
| **AC-01** | Data Store Containers | `docker-compose up -d` brings up `postgres` and `redis` services. Containers remain in `healthy`/`running` state without restart loops or crashes. |
| **AC-02** | PostgreSQL Connectivity | `pg_isready -U tourism_user -d tourism_db` inside the container returns exit code 0. SQLAlchemy async engine connects successfully. |
| **AC-03** | Redis Connectivity | Redis responds to `PING` with `PONG` on port 6379. |
| **AC-04** | FastAPI Backend Startup | Backend starts on port 8000 without import errors, syntax errors, or unhandled startup exceptions. |
| **AC-05** | Health Check Endpoint | `GET http://localhost:8000/health` returns HTTP status `200 OK` with JSON `{"status": "ok", "message": "AI Tourism Ecosystem API is running"}`. |
| **AC-06** | API Root Endpoint | `GET http://localhost:8000/api/v1` returns HTTP status `200 OK`. |
| **AC-07** | Alembic Migration Setup | `alembic init` configured with async database URL; `alembic revision --autogenerate` or `alembic upgrade head` executes cleanly against the database. |
| **AC-08** | Next.js Frontend Skeleton | Next.js application inside `/frontend` compiles without build/type errors and serves pages on port 3000. |

---

## 5. Directory Layout & File Structure Specification

The project layout conforms to the modular monolith pattern:

```
tourism-ecosystem/
├── docker-compose.yml              # Multi-container service definitions (db, redis, backend, frontend)
├── ORIGINAL_REQUEST.md             # Project requirements and acceptance criteria
├── PROJECT.md                      # Teamwork project tracking and milestone status
├── backend/
│   ├── Dockerfile                  # Python 3.11-slim container definition
│   ├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, Alembic, etc.)
│   ├── alembic.ini                 # Alembic migration configuration
│   ├── alembic/
│   │   ├── env.py                  # Async Alembic migration environment
│   │   ├── script.py.mako          # Migration template
│   │   └── versions/               # Schema revision scripts
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI application factory and entrypoint
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py           # Pydantic Settings (DATABASE_URL, REDIS_URL, etc.)
│       │   ├── database.py         # SQLAlchemy async engine, sessionmaker, Base
│       │   └── redis.py            # Redis client wrapper
│       ├── models/
│       │   ├── __init__.py         # Imports all models for Alembic discovery
│       │   └── base.py             # DeclarativeBase with common timestamp columns
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── health.py           # Healthcheck and status Pydantic schemas
│       └── api/
│           ├── __init__.py
│           ├── v1/
│           │   ├── __init__.py
│           │   ├── router.py       # Aggregator for v1 API endpoints
│           │   └── endpoints/
│           │       ├── __init__.py
│           │       └── health.py   # Health and system status router
├── frontend/
│   ├── Dockerfile                  # Node.js container definition
│   ├── package.json                # Next.js and React dependencies
│   ├── next.config.js              # Next.js configuration
│   ├── tsconfig.json               # TypeScript configuration
│   ├── public/                     # Static assets (favicons, logos)
│   └── src/ (or app/)
│       ├── app/
│       │   ├── layout.tsx          # Root layout
│       │   ├── page.tsx            # Landing page / System status
│       │   └── health/
│       │       └── page.tsx        # System health dashboard
│       └── lib/
│           └── api.ts              # API client configured with NEXT_PUBLIC_API_URL
└── .agents/                        # Agent metadata (plans, progress, handoffs)
```

---

## 6. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| 1 | Infrastructure | PostgreSQL Service | Containerized relational database (PostgreSQL 15 Alpine) with persistent storage and automatic healthcheck | DB name, user, password, port 5432 | Port 5432 listener, healthy status | Container crash/restart if credentials or volume mount invalid | `docker-compose.yml` |
| 2 | Infrastructure | Redis Service | Containerized in-memory key-value cache (Redis 7 Alpine) | Port 6379, data volume | Port 6379 listener | Crash if memory exhaustion or port collision | `docker-compose.yml` |
| 3 | Infrastructure | Docker Network & DependsOn | Inter-service networking with dependency condition `postgres: service_healthy` | Container start event | Network bridge and container DNS resolution | Service fails to start if dependency fails health check | `docker-compose.yml` |
| 4 | Backend Core | Asynchronous Web Application | FastAPI application configured with CORS, title, description, and versioning | HTTP requests on port 8000 | HTTP responses | 404 on missing route, 422 on validation error, 500 on unhandled exception | `backend/app/main.py` |
| 5 | Backend Core | Health Check Endpoint | Liveness probe returning backend operational status | HTTP GET `/health` | JSON `{"status": "ok", "message": "..."}`, HTTP 200 | HTTP 500 if internal server error | `backend/app/main.py`, `ORIGINAL_REQUEST.md` |
| 6 | Backend Core | API Root Endpoint | API version indicator for `/api/v1` | HTTP GET `/api/v1` | JSON `{"message": "Welcome to the AI Tourism API v1"}`, HTTP 200 | HTTP 404/500 | `backend/app/main.py` |
| 7 | Backend Core | CORS Middleware | Cross-Origin Resource Sharing enabling frontend communication | HTTP request origin headers | Access-Control-Allow-* headers | Origin rejected if disallowed (currently open `*` for demo) | `backend/app/main.py` |
| 8 | Database | Async SQLAlchemy Engine | Async connection pooling and session management with `asyncpg` | `DATABASE_URL` environment variable | `AsyncEngine` & `AsyncSession` | Connection error raised if PostgreSQL unreachable | `backend/requirements.txt`, `docker-compose.yml` |
| 9 | Database | Alembic Migrations | Automated schema revision tracking using declarative SQLAlchemy models | `alembic.ini`, model definitions | Revision script files in `alembic/versions/` | Migration fails on syntax error, unmapped type, or DB disconnection | `ORIGINAL_REQUEST.md`, `backend/requirements.txt` |
| 10 | Frontend | Next.js Application Skeleton | Web frontend interface providing user and destination interactions | User browser requests on port 3000 | HTML/CSS/JS bundles | 500 server error, build error if syntax invalid | `ORIGINAL_REQUEST.md`, `docker-compose.yml` |
| 11 | Frontend | API Integration Gateway | Frontend client communication layer connecting to backend | `NEXT_PUBLIC_API_URL` env var | Typed JSON responses from backend | Network error/fallback if backend unavailable | `docker-compose.yml` |

---

## 7. Edge Cases & Boundary Conditions

| # | Feature | Input / Condition | Observed / Documented Behavior |
|---|---|---|---|
| 1 | Database Container Startup | PostgreSQL takes > 5 seconds to initialize data directory on first run | Backend waits for `postgres` condition `service_healthy`; healthcheck interval is 5s, timeout 5s, 5 retries (25s window). |
| 2 | Async Database Driver | Backend connects with `postgresql://` instead of `postgresql+asyncpg://` | SQLAlchemy async engine raises `InvalidRequestError` or `ArgumentError` because synchronous `psycopg2` driver is not installed. Must use `postgresql+asyncpg://`. |
| 3 | Alembic Async Migration | Alembic `env.py` executes synchronous engine methods against async driver | Alembic throws `RuntimeError` unless `asyncio.run()` with `engine.connect()` is configured in `run_migrations_online()`. |
| 4 | CORS Configuration | Frontend hosted on different origin (e.g. localhost:3000 calling localhost:8000) | Browser blocks cross-origin requests unless `CORSMiddleware` in FastAPI is explicitly configured with allowed origins or wildcard. |
| 5 | Environment Variables | `DATABASE_URL` or `REDIS_URL` omitted from environment | Backend fails during startup if Pydantic `BaseSettings` has required fields without default values, preventing silent runtime failures. |
| 6 | Empty Frontend Directory | `docker-compose build frontend` executed when `./frontend` has no `package.json` or `Dockerfile` | Docker build fails with missing build context / Dockerfile error. Skeleton must contain valid `package.json` and build artifacts. |

---

## 8. Environmental & Operational Constraints

1. **Permission Sandbox & Blueprint Availability**:
   - Direct filesystem access to external user OneDrive directory (`C:\Users\gurup\OneDrive\tourism`) requires interactive permission prompts. When running unattended or in headless agent execution, external path reads time out.
   - The authoritative specification is synthesized from `ORIGINAL_REQUEST.md`, existing docker and backend manifests, and standard production blueprints for the modular monolith architecture.
2. **Integrity Mode: `demo`**:
   - In demo mode, permissive CORS (`allow_origins=["*"]`) and lightweight Alpine containers are accepted.
   - Database credentials and environment variables are standard development credentials (`tourism_user` / `tourism_password`).
3. **Execution Safety**:
   - As a read-only specification investigator, no source code or configuration files are modified. All findings are output directly to `.agents/spec_miner_blueprints_1/`.
