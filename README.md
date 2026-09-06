# 🌍 AI Tourism Ecosystem

> A production-grade AI-powered tourism platform built with **FastAPI + Next.js 14 + PostgreSQL 15 + Redis 7**

[![Built with Antigravity AI](https://img.shields.io/badge/Built%20with-Antigravity%20AI-emerald)](https://antigravity.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://postgresql.org)

---

## ✨ Features

| Module | Features |
|---|---|
| 🧳 **Tourist Portal** | Search destinations, AI itinerary generation (4 styles × 3 budgets), printable day-by-day plans |
| 🏨 **Partner Dashboard** | Register as operator, create listings/experiences, manage bookings |
| 🔐 **Auth System** | JWT authentication, role-based access (tourist / partner / admin) |
| 📊 **Control Tower** | Admin analytics, congestion alerts, revenue charts, destination health |
| 🤖 **AI Generator** | Rule-based engine with 4 travel styles, 3 budget levels, up to 30-day itineraries |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git

### 1. Clone & Start
```bash
git clone https://github.com/guru071/tourism.git
cd tourism
docker compose up -d
```

### 2. Run Migrations
```bash
# Wait ~30 seconds for PostgreSQL to be ready
docker compose exec backend alembic upgrade head
```

### 3. Seed Sample Data (12 destinations)
```bash
docker compose exec backend python -m app.seed
```

### 4. Open the App
| Service | URL |
|---|---|
| 🌐 Frontend | http://localhost:3000 |
| ⚡ API | http://localhost:8000 |
| 📚 API Docs | http://localhost:8000/docs |
| 💓 Health | http://localhost:8000/health |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Frontend    │  │   Backend    │  │   PostgreSQL 15  │  │
│  │  Next.js 14  │◄─►  FastAPI     │◄─►   Port 5432      │  │
│  │  Port 3000   │  │  Port 8000   │  └─────────────────┘  │
│  └──────────────┘  └──────┬───────┘  ┌─────────────────┐  │
│                            └─────────►│    Redis 7      │  │
│                                       │    Port 6379    │  │
│                                       └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
tourism/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # All REST endpoints
│   │   │   ├── auth.py          # Register, login, /me
│   │   │   ├── destinations.py  # Search + CRUD
│   │   │   ├── itineraries.py   # AI generation
│   │   │   ├── operators.py     # Partner profiles
│   │   │   ├── listings.py      # Tour listings
│   │   │   ├── bookings.py      # Booking engine
│   │   │   ├── reviews.py       # Reviews
│   │   │   └── control_tower.py # Analytics
│   │   ├── core/
│   │   │   ├── config.py        # Env settings
│   │   │   ├── database.py      # Async SQLAlchemy
│   │   │   ├── redis.py         # Redis client
│   │   │   └── security.py      # JWT + bcrypt
│   │   ├── models/              # 8 SQLAlchemy models
│   │   ├── schemas/             # Pydantic v2 schemas
│   │   ├── services/
│   │   │   └── itinerary_generator.py  # AI engine
│   │   ├── main.py              # App factory
│   │   └── seed.py              # 12 destinations
│   ├── alembic/                 # DB migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx                    # Landing/search
│       │   ├── destinations/[id]/page.tsx  # Destination + generator
│       │   ├── itineraries/[id]/page.tsx   # Itinerary view
│       │   ├── auth/login/page.tsx         # Login
│       │   ├── auth/register/page.tsx      # Register
│       │   ├── partner/page.tsx            # Partner dashboard
│       │   └── control-tower/page.tsx      # Admin dashboard
│       ├── components/
│       │   └── Navbar.tsx
│       └── lib/
│           └── api.ts                      # Typed API client
├── docker-compose.yml
├── STATUS.md                    # ✅ Done / 🔴 Pending tracker
└── ANTIGRAVITY.md               # AI dev continuation guide
```

---

## ⚙️ Environment Variables

### `backend/.env`
```env
DATABASE_URL=postgresql+asyncpg://tourism:tourism@db:5432/tourism
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### `frontend/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📊 Phase Status

| Phase | Status | Description |
|---|---|---|
| Phase 0 — Foundation | ✅ Complete | Docker, DB models, Alembic, FastAPI/Next.js skeleton |
| Phase 1 — Tourist Features | ✅ Complete | Search, AI itinerary generator, tourist UI |
| Phase 2 — Partner Module | ✅ Complete | Auth, operators, listings, bookings, reviews, partner dashboard |
| Phase 3 — Control Tower | 🟡 Partial | Analytics done; forecasting + heatmap pending |
| Phase 4 — AI Intelligence | 🔴 Pending | Gemini LLM, recommendations, NL search |
| Phase 5 — Scale/Production | 🔴 Pending | Stripe, email, CDN, CI/CD, monitoring |

See [STATUS.md](STATUS.md) for the full task breakdown.

---

## 🤖 Continuing Development with Antigravity AI

See [ANTIGRAVITY.md](ANTIGRAVITY.md) for the complete guide to resume building on any computer using Antigravity AI — includes architecture notes, next steps for each phase, and the exact prompts to use.

---

## 🗄️ Database Models

8 domain models: `User` · `Destination` · `Operator` · `Listing` · `Itinerary` · `ItineraryItem` · `Booking` · `Review`

---

## 📄 License

MIT — Built with ❤️ using [Antigravity AI](https://antigravity.dev)
