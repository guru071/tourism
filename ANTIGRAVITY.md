# Antigravity AI — Development Continuation Guide

> This file tells Antigravity AI everything it needs to continue building this project on any computer.
> **Conversation ID to resume:** `46982d1e-1ff8-46aa-953d-cdbfbdafb25c`

---

## 🚀 What Is This Project?

A full-stack **AI Tourism Ecosystem** — a production-grade multi-module platform for:
- Tourists to search destinations and generate AI-powered day-by-day itineraries
- Partners (tour operators, hotels) to list experiences and manage bookings
- Admins to monitor platform health via a Control Tower dashboard

**Stack:** FastAPI (Python 3.11) + Next.js 14 + PostgreSQL 15 + Redis 7 + Docker

---

## 📁 Project Location (on original machine)
```
C:\Users\gurup\.gemini\antigravity\scratch\tourism-ecosystem\
```

**On a new machine**, clone from GitHub:
```bash
git clone https://github.com/guru071/tourism.git
cd tourism
```

---

## 🧠 Antigravity: How to Continue Building

### Step 1 — Set workspace
In Antigravity IDE, set your workspace to the cloned folder:
```
/path/to/tourism
```

### Step 2 — Tell Antigravity to resume
Paste this prompt into Antigravity chat:

```
Read the STATUS.md file carefully. Then read ANTIGRAVITY.md.
Read all files in backend/app/ and frontend/src/ to understand the full codebase.
Then continue building the PENDING items from STATUS.md, starting with Phase 3 (Control Tower remaining features), then Phase 4 (AI Intelligence Layer), then Phase 5 (Scale & Production).
Build real, working code — no blueprints, no plans. Go directly to implementation.
```

### Step 3 — Boost mode (optional, for complex phases)
Use the `/boost` command for Phase 4 AI integration and Phase 5 production work.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Frontend    │  │   Backend    │  │   PostgreSQL 15  │  │
│  │  Next.js 14  │  │   FastAPI    │  │   Port 5432      │  │
│  │  Port 3000   │◄─►  Port 8000   │◄─►                  │  │
│  └──────────────┘  └──────┬───────┘  └─────────────────┘  │
│                            │          ┌─────────────────┐  │
│                            └─────────►│    Redis 7      │  │
│                                       │    Port 6379    │  │
│                                       └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Files to Read First
| File | Purpose |
|---|---|
| `STATUS.md` | ✅ Done / 🔴 Pending tracker |
| `backend/app/core/config.py` | All settings, env variables |
| `backend/app/core/security.py` | JWT auth, bcrypt, `get_current_user` |
| `backend/app/main.py` | FastAPI app factory |
| `backend/app/api/v1/router.py` | All registered endpoints |
| `backend/app/services/itinerary_generator.py` | Rule-based AI (to be replaced by Gemini) |
| `backend/app/seed.py` | Seed 12 destinations |
| `frontend/src/lib/api.ts` | Full typed API client |
| `frontend/src/app/layout.tsx` | Root layout (Navbar) |

---

## 🗄️ Database Schema (8 models)

| Model | Table | Key Fields |
|---|---|---|
| `User` | `users` | email, hashed_password, role (tourist/partner/admin) |
| `Destination` | `destinations` | name, slug, country, city, category, lat/lon, image_urls (JSON), tags (JSON) |
| `Operator` | `operators` | user_id (FK), business_name, business_type, verified |
| `Listing` | `listings` | operator_id, destination_id, title, category, base_price, availability |
| `Itinerary` | `itineraries` | user_id (nullable), destination_id, duration_days, travel_style, budget_level, day_plans (JSON) |
| `Booking` | `bookings` | user_id, listing_id, booking_reference, status, start_date, end_date, total_price |
| `Review` | `reviews` | user_id, listing_id, booking_id (nullable), rating (1-5), comment |
| `ItineraryItem` | `itinerary_items` | itinerary_id, listing_id, day_number, title, start_time |

---

## 🔑 API Endpoints (all built)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | DB + Redis health probe |
| POST | `/api/v1/auth/register` | — | Register (tourist/partner/admin) |
| POST | `/api/v1/auth/login` | — | Login → JWT token |
| GET | `/api/v1/auth/me` | JWT | Current user |
| GET | `/api/v1/destinations` | — | Search + filter destinations |
| GET | `/api/v1/destinations/{id}` | — | Destination detail |
| POST | `/api/v1/destinations` | — | Create destination |
| POST | `/api/v1/itineraries/generate` | — | AI itinerary generation |
| GET | `/api/v1/itineraries/{id}` | — | Get itinerary |
| GET | `/api/v1/operators` | — | List operators |
| GET | `/api/v1/operators/{id}` | — | Operator detail + listings |
| POST | `/api/v1/operators` | JWT (partner) | Create operator profile |
| GET | `/api/v1/listings` | — | List listings with filters |
| POST | `/api/v1/listings` | JWT (partner) | Create listing |
| PUT | `/api/v1/listings/{id}` | JWT (owner) | Update listing |
| POST | `/api/v1/bookings` | JWT | Create booking |
| GET | `/api/v1/bookings/my` | JWT | My bookings |
| PATCH | `/api/v1/bookings/{id}/status` | JWT (partner) | Update status |
| POST | `/api/v1/reviews` | JWT | Submit review |
| GET | `/api/v1/reviews` | — | List reviews |
| GET | `/api/v1/control-tower/dashboard` | JWT (admin) | Dashboard stats |
| GET | `/api/v1/control-tower/congestion` | JWT (admin) | Congestion alerts |
| GET | `/api/v1/control-tower/revenue` | JWT (admin) | Revenue by month |

---

## 🖥️ Frontend Pages (all built)

| Route | Description |
|---|---|
| `/` | Tourist landing: hero + search + category filters + destination cards |
| `/destinations/[id]` | Destination detail + AI itinerary generator |
| `/itineraries/[id]` | Printable day-by-day itinerary view |
| `/auth/login` | JWT login with role-based redirect |
| `/auth/register` | Register as Tourist or Partner |
| `/partner` | Partner dashboard (stats, listings, bookings) |
| `/control-tower` | Admin analytics (stats, congestion, revenue chart) |

---

## 🚢 Running Locally

### Prerequisites
- Docker Desktop installed and running
- Git

### Start Everything
```bash
git clone https://github.com/guru071/tourism.git
cd tourism
docker compose up -d

# Wait ~30 seconds for DB to be ready, then run migrations:
docker compose exec backend alembic upgrade head

# Seed 12 sample destinations:
docker compose exec backend python -m app.seed

# Access:
# Frontend → http://localhost:3000
# API Docs → http://localhost:8000/docs
# Health   → http://localhost:8000/health
```

### Environment Variables
Create `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://tourism:tourism@db:5432/tourism
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-this-to-a-random-secret-key-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🤖 Itinerary Generator Design

Located at `backend/app/services/itinerary_generator.py`

- Entry point: `generate_itinerary(destination_name, destination_id, duration_days, travel_style, budget_level) → dict`
- **4 travel styles:** Relaxed, Cultural, Adventure, Luxury
- **3 budget levels:** Budget, Mid-range, Luxury
- **Generates:** up to 30-day itineraries with morning/afternoon/evening activities, costs, tips
- **Future:** Replace with Google Gemini API call (Phase 4)

---

## 🔮 Next Steps for Antigravity (Phase 3→5)

### Phase 3 — Control Tower (remaining)
```
Build:
1. Demand forecasting endpoint: GET /api/v1/control-tower/forecast?destination_id=&days=30
   - Use simple moving average from booking history
2. Destination health score: composite of (avg_rating × 0.4) + (booking_rate × 0.4) + (congestion_inverse × 0.2)
3. Frontend: add interactive map to control-tower page using react-leaflet
4. Frontend: add CSV export button for booking data
```

### Phase 4 — AI Intelligence Layer
```
Build:
1. Install google-generativeai in requirements.txt
2. Create backend/app/services/gemini_generator.py:
   - Call Gemini 1.5 Flash with a structured prompt
   - Parse JSON response into ItineraryRead schema
   - Fall back to rule-based generator if API fails
3. Add GEMINI_API_KEY to config.py
4. Natural language search: POST /api/v1/destinations/search-nl {"query": "beach in Asia under $50/day"}
5. Recommendation endpoint: GET /api/v1/recommendations?user_id=&limit=5
```

### Phase 5 — Production
```
Build:
1. Stripe integration: POST /api/v1/payments/checkout, POST /api/v1/payments/webhook
2. Email service: SendGrid or Resend for booking confirmations
3. Image upload: POST /api/v1/upload → Cloudflare R2 presigned URL
4. GitHub Actions: .github/workflows/ci.yml (test + build on push)
5. Rate limiting: slowapi middleware in main.py
```

---

## 📦 Dependencies

### Backend (requirements.txt)
```
fastapi==0.110.0
uvicorn==0.27.1
sqlalchemy==2.0.28
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.6.4
pydantic-settings==2.2.1
redis==5.0.3
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
email-validator==2.1.1
pytest==9.1.1
pytest-asyncio==0.23.5
httpx==0.28.1
```

### Frontend (package.json key deps)
```
next: 14.x
react: 18.x
typescript: 5.x
tailwindcss: 3.x
lucide-react: latest
```

---

## 🔐 Test Accounts (after seeding)

Register these via the API or `/auth/register` page:
- **Admin:** `admin@tourism.ai` / any password → role: `admin`
- **Partner:** `partner@tours.com` / any password → role: `partner`
- **Tourist:** `tourist@example.com` / any password → role: `tourist`

---

*Built by Antigravity AI — Google DeepMind*
*Conversation: `46982d1e-1ff8-46aa-953d-cdbfbdafb25c`*
