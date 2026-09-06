# Phase 0 Data Store & Schema Specification: AI Tourism Ecosystem

## Executive Summary
This document provides the authoritative data store, schema, migration, caching, and health verification specification for Phase 0 (Product Foundation) of the **AI Tourism Operating System / Ecosystem**.

It defines the exact database topology, PostgreSQL 15 configuration, Redis 7 caching semantics, SQLAlchemy 2.0 async domain models, entity relationship diagrams (ERD), column constraints, foreign key cascades, Alembic migration architecture, `.env` parameter contracts, and FastAPI integration pipelines.

---

## 1. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Infrastructure | PostgreSQL 15 Service | Relational storage for all core business entities, users, listings, bookings, and itineraries. | Docker env: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, port `5432` | Running PostgreSQL daemon with persistent volume `postgres_data` | Restart on failure, health check retry 5x via `pg_isready` | `docker-compose.yml:4-19` |
| 2 | Infrastructure | Redis 7 Service | In-memory key-value cache for session management, destination query caching, rate limiting, and pub/sub. | Docker image `redis:7-alpine`, port `6379` | Running Redis server with persistent volume `redis_data` | Exits on fatal failure; requires compose healthcheck | `docker-compose.yml:20-26` |
| 3 | Core Config | Environment Variables (.env) | Unified environment configuration via Pydantic `BaseSettings`. | `.env` file or environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, etc.) | Validated `Settings` object injected across FastAPI app | `ValidationError` on missing or malformed required config | `backend/requirements.txt:6-7`, `docker-compose.yml:32-34` |
| 4 | Data Layer | SQLAlchemy 2.0 Async Engine | Asynchronous DB session management and engine pooling. | Connection string `postgresql+asyncpg://...` | `AsyncEngine`, `async_sessionmaker`, `AsyncSession` | `SQLAlchemyError` / `ConnectionRefusedError` on connection loss | `backend/requirements.txt:3-4` |
| 5 | Migrations | Alembic Async Migration Suite | Version-controlled schema migrations for SQLAlchemy models. | `alembic.ini`, `alembic/env.py`, `target_metadata = Base.metadata` | Versioned migration files in `alembic/versions/` | Halts execution on mismatch or failed migration transaction | `backend/requirements.txt:5` |
| 6 | Domain Model | User Entity (`users`) | Accounts, identity, role-based access (tourist, operator, admin). | Email, hashed password, full name, role, status flags | UUID primary key, timestamps, user record | Unique constraint violation on duplicate email | Canonical Domain Architecture |
| 7 | Domain Model | Destination Entity (`destinations`) | Geographic POIs, cities, regions, and countries for tourism discovery. | Name, slug, country, coordinates, tags, media URLs | UUID primary key, indexed slug | Unique constraint violation on duplicate slug | Canonical Domain Architecture |
| 8 | Domain Model | Operator Entity (`operators`) | Verified tourism vendors, hotels, tour agencies, guides. | User ID, business name, business type, contact info | UUID primary key, 1-to-1 relationship with `users` | Foreign key violation if `user_id` does not exist | Canonical Domain Architecture |
| 9 | Domain Model | Listing Entity (`listings`) | Tourism services, tours, hotel stays, experiences, dining. | Operator ID, destination ID, title, pricing, category | UUID primary key, indexed category/destination | Foreign key violation if operator/destination missing | Canonical Domain Architecture |
| 10 | Domain Model | Itinerary Entity (`itineraries`) | AI-generated and user-customized multi-day trip plans. | User ID, destination ID, dates, budget limit, status | UUID primary key, trip plan record | Date check constraint (`start_date <= end_date`) | Canonical Domain Architecture |
| 11 | Domain Model | Itinerary Item (`itinerary_items`) | Sequential schedule items within an itinerary (day, time, activity). | Itinerary ID, optional listing ID, day number, order | UUID primary key, ordered activity item | Foreign key cascade delete if parent itinerary is removed | Canonical Domain Architecture |
| 12 | Domain Model | Booking Entity (`bookings`) | Reservation and transaction state for listings/services. | User ID, listing ID, dates, guest count, price | UUID primary key, unique booking reference | Check constraint on guests (`>= 1`), positive price | Canonical Domain Architecture |
| 13 | Domain Model | Review Entity (`reviews`) | Tourist reviews and ratings for verified listings and bookings. | User ID, listing ID, optional booking ID, rating 1-5 | UUID primary key, review record | Check constraint on rating (`1 <= rating <= 5`) | Canonical Domain Architecture |
| 14 | API Monitoring | Health Check (`/health`) | Probes FastAPI liveness and deep readiness of Postgres and Redis. | HTTP GET request to `/health` | JSON payload with system and dependency statuses | Returns HTTP 503 if Postgres or Redis is down | `backend/app/main.py:19-21` & Acceptance Criteria |
| 15 | Middleware | CORS Configuration | Cross-origin resource sharing allowing Next.js frontend calls. | Allowed origins, credentials, methods, headers | CORS headers on HTTP responses | Disallows unauthorized origins if configured | `backend/app/main.py:10-17` |

---

## 2. Edge Cases

| # | Feature | Input | Observed / Specified Behavior |
|---|---------|-------|-------------------------------|
| 1 | Database Connection Pool | High concurrent load exceeding `pool_size` (10) | Uses `max_overflow` (up to 20); raises `TimeoutError` if pool exhausted after `pool_timeout` (30s). |
| 2 | Asyncpg Connection Drop | Database container restarts or network blips | `pool_pre_ping=True` detects disconnected connections before executing queries and re-establishes socket. |
| 3 | Alembic URL Async/Sync Conflict | Alembic default sync driver vs `postgresql+asyncpg` URL | In `alembic/env.py`, the URL is converted via `DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")` for sync runners, or run through `connectable.run_sync` using `async_engine_from_config`. |
| 4 | Duplicate User Registration | POST user with existing email | Raises `IntegrityError` from database; mapped in API layer to HTTP 409 Conflict. |
| 5 | Cascade Deletion of User | DELETE user having active listings or bookings | `ondelete="CASCADE"` on `operators`, `itineraries`, `reviews`; `ondelete="RESTRICT"` on `bookings` prevents accidental data loss for financial audits. |
| 6 | Invalid Rating Range | Review submitted with rating = 0 or 6 | Table-level check constraint `CHECK (rating >= 1 AND rating <= 5)` triggers `IntegrityError`. |
| 7 | Itinerary Date Inversion | Itinerary submitted where `start_date > end_date` | Table-level check constraint `CHECK (start_date <= end_date)` rejects insertion. |
| 8 | Redis Connection Outage during Health Check | Redis container stopped while FastAPI running | `/health` catches connection exception, sets `services.redis: "unhealthy"`, and returns HTTP 503 Service Unavailable. |
| 9 | Database Outage during Health Check | Postgres container stopped while FastAPI running | `/health` catches asyncpg connection exception, sets `services.database: "unhealthy"`, returns HTTP 503. |
| 10 | Empty JSONB Fields | Listing or destination created without tags/amenities | Default column values set to SQL `DEFAULT '[]'::jsonb`, returning empty Python lists instead of `None`. |

---

## 3. Entity Relationship Diagram (ERD)

```text
       +-------------------+
       |       users       |
       +-------------------+
       | PK id (UUID)      |<--------------------+
       |    email          |                     |
       |    hashed_password|                     |
       |    role           |                     |
       +-------------------+                     |
         | 1             | 1                     | 1
         |               |                       |
         | 1             | M                     | M
       +-------------+ +--------------------+ +-------------------+
       |  operators  | |    itineraries     | |      reviews      |
       +-------------+ +--------------------+ +-------------------+
       | PK id (UUID)| | PK id (UUID)       | | PK id (UUID)      |
       | FK user_id  | | FK user_id         | | FK user_id        |
       +-------------+ | FK destination_id  | | FK listing_id     |
         | 1           +--------------------+ | FK booking_id     |
         |               | 1                  +-------------------+
         |               |                              ^
         | M             | M                            | 0..1
       +-------------------+                  +-------------------+
       |     listings      |<-----------------|     bookings      |
       +-------------------+ 1              M +-------------------+
       | PK id (UUID)      |                  | PK id (UUID)      |
       | FK operator_id    |<----+            | FK user_id        |
       | FK destination_id |     |            | FK listing_id     |
       +-------------------+     |            | FK itinerary_id   |
         | 1                     |            +-------------------+
         |                       |                      ^
         | 0..M                  |                      |
       +-------------------+     |                      |
       |  itinerary_items  |     |                      |
       +-------------------+     |                      |
       | PK id (UUID)      |     |                      |
       | FK itinerary_id   |-----+                      |
       | FK listing_id     |----------------------------+
       +-------------------+
```

---

## 4. Comprehensive Schema Definitions & Table Specifications

### 4.1 Table: `users`
Represents all system actors (tourists, tour operators, platform administrators, AI concierge agents).
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'tourist',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    phone_number VARCHAR(50),
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_users_email ON users (email);
CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_users_is_active ON users (is_active);
```

### 4.2 Table: `destinations`
Represents geographical anchors for travel, including countries, regions, and cities.
```sql
CREATE TABLE destinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    city VARCHAR(100),
    description TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    image_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_destinations_slug ON destinations (slug);
CREATE INDEX ix_destinations_country ON destinations (country);
CREATE INDEX ix_destinations_region ON destinations (region);
CREATE INDEX ix_destinations_is_active ON destinations (is_active);
```

### 4.3 Table: `operators`
Represents registered businesses providing accommodations, excursions, or transit.
```sql
CREATE TABLE operators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    business_type VARCHAR(50) NOT NULL,
    registration_number VARCHAR(100),
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    website_url VARCHAR(255),
    verification_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_operators_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX uq_operators_user_id ON operators (user_id);
CREATE INDEX ix_operators_business_type ON operators (business_type);
CREATE INDEX ix_operators_verification_status ON operators (verification_status);
```

### 4.4 Table: `listings`
Catalog of bookable tourism services, experiences, stays, and guided activities.
```sql
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL,
    destination_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    base_price NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    capacity INTEGER,
    duration_hours NUMERIC(5, 2),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    amenities JSONB NOT NULL DEFAULT '[]'::jsonb,
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    rating_average NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
    review_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_listings_operator_id FOREIGN KEY (operator_id) REFERENCES operators (id) ON DELETE CASCADE,
    CONSTRAINT fk_listings_destination_id FOREIGN KEY (destination_id) REFERENCES destinations (id) ON DELETE RESTRICT,
    CONSTRAINT ck_listings_base_price CHECK (base_price >= 0),
    CONSTRAINT ck_listings_rating_average CHECK (rating_average >= 0 AND rating_average <= 5)
);

CREATE UNIQUE INDEX uq_listings_slug ON listings (slug);
CREATE INDEX ix_listings_operator_id ON listings (operator_id);
CREATE INDEX ix_listings_destination_id ON listings (destination_id);
CREATE INDEX ix_listings_category ON listings (category);
CREATE INDEX ix_listings_is_active ON listings (is_active);
```

### 4.5 Table: `itineraries`
User travel schedules, whether generated via AI or composed manually.
```sql
CREATE TABLE itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    destination_id UUID,
    title VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget_limit NUMERIC(12, 2),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    ai_prompt_context JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_itineraries_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_itineraries_destination_id FOREIGN KEY (destination_id) REFERENCES destinations (id) ON DELETE SET NULL,
    CONSTRAINT ck_itineraries_dates CHECK (start_date <= end_date)
);

CREATE INDEX ix_itineraries_user_id ON itineraries (user_id);
CREATE INDEX ix_itineraries_destination_id ON itineraries (destination_id);
CREATE INDEX ix_itineraries_status ON itineraries (status);
```

### 4.6 Table: `itinerary_items`
Individual sequential events and stops assigned to itinerary days.
```sql
CREATE TABLE itinerary_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    itinerary_id UUID NOT NULL,
    listing_id UUID,
    day_number INTEGER NOT NULL,
    order_index INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    start_time TIME,
    end_time TIME,
    estimated_cost NUMERIC(12, 2),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_itinerary_items_itinerary_id FOREIGN KEY (itinerary_id) REFERENCES itineraries (id) ON DELETE CASCADE,
    CONSTRAINT fk_itinerary_items_listing_id FOREIGN KEY (listing_id) REFERENCES listings (id) ON DELETE SET NULL,
    CONSTRAINT ck_itinerary_items_day_number CHECK (day_number >= 1),
    CONSTRAINT ck_itinerary_items_order_index CHECK (order_index >= 0)
);

CREATE INDEX ix_itinerary_items_itinerary_id ON itinerary_items (itinerary_id);
CREATE INDEX ix_itinerary_items_listing_id ON itinerary_items (listing_id);
```

### 4.7 Table: `bookings`
Booking transactions and reservations across listings.
```sql
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    listing_id UUID NOT NULL,
    itinerary_id UUID,
    booking_reference VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    guests_count INTEGER NOT NULL DEFAULT 1,
    total_price NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_status VARCHAR(50) NOT NULL DEFAULT 'unpaid',
    payment_transaction_id VARCHAR(100),
    special_requests TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bookings_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_bookings_listing_id FOREIGN KEY (listing_id) REFERENCES listings (id) ON DELETE RESTRICT,
    CONSTRAINT fk_bookings_itinerary_id FOREIGN KEY (itinerary_id) REFERENCES itineraries (id) ON DELETE SET NULL,
    CONSTRAINT ck_bookings_dates CHECK (start_date <= end_date),
    CONSTRAINT ck_bookings_guests CHECK (guests_count >= 1),
    CONSTRAINT ck_bookings_price CHECK (total_price >= 0)
);

CREATE UNIQUE INDEX uq_bookings_reference ON bookings (booking_reference);
CREATE INDEX ix_bookings_user_id ON bookings (user_id);
CREATE INDEX ix_bookings_listing_id ON bookings (listing_id);
CREATE INDEX ix_bookings_status ON bookings (status);
```

### 4.8 Table: `reviews`
User ratings and textual feedback for completed experiences.
```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    listing_id UUID NOT NULL,
    booking_id UUID,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reviews_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_listing_id FOREIGN KEY (listing_id) REFERENCES listings (id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_booking_id FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE SET NULL,
    CONSTRAINT ck_reviews_rating CHECK (rating >= 1 AND rating <= 5)
);

CREATE UNIQUE INDEX uq_reviews_booking_id ON reviews (booking_id);
CREATE INDEX ix_reviews_listing_id ON reviews (listing_id);
CREATE INDEX ix_reviews_user_id ON reviews (user_id);
```

---

## 5. SQLAlchemy 2.0 Async Implementation Specifications

### 5.1 Base Declarative Model (`backend/app/models/base.py`)
```python
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
```

### 5.2 Model Export Manifest (`backend/app/models/__init__.py`)
Alembic requires all models to be imported before inspecting `Base.metadata`:
```python
from app.models.base import Base
from app.models.user import User
from app.models.destination import Destination
from app.models.operator import Operator
from app.models.listing import Listing
from app.models.itinerary import Itinerary, ItineraryItem
from app.models.booking import Booking
from app.models.review import Review

__all__ = [
    "Base",
    "User",
    "Destination",
    "Operator",
    "Listing",
    "Itinerary",
    "ItineraryItem",
    "Booking",
    "Review",
]
```

---

## 6. Alembic Migration Configuration Requirements

### 6.1 `backend/alembic.ini`
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://tourism_user:tourism_password@localhost:5432/tourism_db

[logging]
default_level = INFO
```

### 6.2 `backend/alembic/env.py` (Async Execution Strategy)
```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_database_url() -> str:
    url = str(settings.DATABASE_URL)
    # Ensure alembic uses asyncpg driver
    if not url.startswith("postgresql+asyncpg://") and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

config.set_main_option("sqlalchemy.url", get_database_url())

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
```

---

## 7. Redis Caching Architecture

### 7.1 Client Factory (`backend/app/core/redis.py`)
```python
from redis.asyncio import Redis, from_url
from app.core.config import settings

redis_client: Redis | None = None

async def get_redis_pool() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
    return redis_client

async def close_redis_pool() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
```

### 7.2 Cache Key Namespaces & TTL Policy
- `destinations:list:{query_hash}` — TTL: 3600s (1 hour)
- `destinations:detail:{slug}` — TTL: 7200s (2 hours)
- `listings:destination:{dest_id}:{category}` — TTL: 1800s (30 mins)
- `auth:blacklist:{token_jti}` — TTL: Remaining token lifetime
- `rate_limit:ip:{client_ip}` — TTL: 60s (sliding window)

---

## 8. Environment Variables Specification (`.env`)

| Variable Name | Type | Default Value (Dev/Docker) | Purpose |
|---------------|------|---------------------------|---------|
| `PROJECT_NAME` | string | `AI Tourism Operating System` | FastAPI API Docs Title |
| `VERSION` | string | `1.0.0` | API SemVer version |
| `ENVIRONMENT` | string | `development` | Runtime environment (`development`, `test`, `production`) |
| `DEBUG` | boolean | `true` | Detailed stacktraces |
| `POSTGRES_SERVER` | string | `postgres` | Host of PostgreSQL service |
| `POSTGRES_PORT` | integer | `5432` | Port of PostgreSQL service |
| `POSTGRES_USER` | string | `tourism_user` | Database user |
| `POSTGRES_PASSWORD` | string | `tourism_password` | Database password |
| `POSTGRES_DB` | string | `tourism_db` | Main database name |
| `DATABASE_URL` | string | `postgresql+asyncpg://tourism_user:tourism_password@postgres:5432/tourism_db` | Async SQLAlchemy connection string |
| `REDIS_URL` | string | `redis://redis:6379/0` | Redis client connection string |
| `SECRET_KEY` | string | `phase0-super-secret-key-change-in-production-min-32-chars` | JWT signature token secret |
| `ALGORITHM` | string | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| integer | `10080` (7 days) | Access token validity duration |
| `CORS_ORIGINS` | json list | `["http://localhost:3000", "http://127.0.0.1:3000"]` | Allowed CORS origins for Next.js frontend |

---

## 9. FastAPI Integration & Health Check Endpoints

### 9.1 FastAPI Lifecycle Connection (`backend/app/main.py`)
FastAPI connects to Postgres and Redis using the modern async `lifespan` context manager:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import get_db, async_engine
from app.core.redis import get_redis_pool, close_redis_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connections
    yield
    # Shutdown: clean release
    await async_engine.dispose()
    await close_redis_pool()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)
```

### 9.2 Deep Health Check Specification (`/health`)
The `/health` endpoint must verify both internal server responsiveness and live ping connectivity to PostgreSQL and Redis:
```python
@app.get("/health", tags=["Monitoring"])
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_pool)
):
    health_details = {
        "status": "ok",
        "version": settings.VERSION,
        "services": {
            "database": "unreachable",
            "redis": "unreachable"
        }
    }
    
    # Check Database
    try:
        res = await db.execute(text("SELECT 1"))
        if res.scalar() == 1:
            health_details["services"]["database"] = "healthy"
    except Exception as e:
        health_details["services"]["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        pong = await redis.ping()
        if pong is True:
            health_details["services"]["redis"] = "healthy"
    except Exception as e:
        health_details["services"]["redis"] = f"unhealthy: {str(e)}"

    all_healthy = all(
        status_val == "healthy" 
        for status_val in health_details["services"].values()
    )
    
    if all_healthy:
        return health_details
    else:
        health_details["status"] = "degraded"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_details
        )
```

### 9.3 Expected Responses

#### HTTP 200 OK (Healthy State)
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

#### HTTP 503 Service Unavailable (Database Failure State)
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "services": {
    "database": "unhealthy: connection refused",
    "redis": "healthy"
  }
}
```
