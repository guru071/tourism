# Aventis Platform - Complete Architecture Guide

> Last updated: 2026-09-07 | Built with Antigravity AI Multi-Agent Architecture
> Conversation: `46982d1e-1ff8-46aa-953d-cdbfbdafb25c`

## Platform Architecture

The Aventis Platform (formerly AI Tourism Ecosystem) is a true 100% enterprise-grade tourism operating system spanning three core modules: Tourist Booking, Partner Management, and Admin Control Tower.

```text
    [ Tourist App ]     [ Partner Dashboard ]    [ Admin Control Tower ]
       (Next.js)             (Next.js)                 (Next.js)
           |                     |                         |
           +---------------------+-------------------------+
                                 |
                          [ API Gateway ]
                        (FastAPI / Uvicorn)
                                 |
    +------------------+-------------------+------------------+
    |                  |                   |                  |
[ PostgreSQL ]     [ Redis ]     [ Gemini 1.5 Pro ]    [ External APIs ]
 (Core Data)    (Pub/Sub + WS)   (AI Intelligence)     (Stripe, S3, SendGrid)
```

## Database Schema (PostgreSQL 15)

| Model | Table | Key Fields |
|---|---|---|
| `User` | `users` | email, hashed_password, role (tourist/partner/admin) |
| `Destination` | `destinations` | name, slug, country, city, category, lat/lon |
| `Operator` | `operators` | user_id (FK), business_name, business_type, verified |
| `Listing` | `listings` | operator_id, destination_id, title, base_price, lat/lon |
| `Itinerary` | `itineraries` | user_id, destination_id, duration_days, day_plans (JSON) |
| `Booking` | `bookings` | user_id, listing_id, booking_reference, status, total_price |
| `Review` | `reviews` | user_id, listing_id, booking_id, rating (1-5), comment |

---

## Complete API Surface (FastAPI)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | DB + Redis health probe |
| POST | `/api/v1/auth/register` | None | Register (tourist/partner/admin) |
| POST | `/api/v1/auth/token` | None | Swagger UI OAuth2 form token login |
| GET | `/api/v1/destinations` | None | PostgreSQL Full-Text Search (tsvector) |
| GET | `/api/v1/recommendations`| None | Gemini AI personalized recommendations |
| POST | `/api/v1/chat` | None | Floating Assistant chatbot endpoint |
| POST | `/api/v1/itineraries/generate` | None | AI dynamic itinerary generation |
| POST | `/api/v1/listings` | JWT (partner) | Create listings |
| POST | `/api/v1/bookings` | JWT | Create booking |
| POST | `/api/v1/payments/create-checkout-session`| JWT | Stripe Checkout generator |
| POST | `/api/v1/payments/webhook` | None | Stripe cryptographic webhook listener |
| POST | `/api/v1/uploads` | JWT | Generate AWS S3/Cloudflare R2 presigned URLs |
| WS | `/ws/control-tower` | None | Redis Pub/Sub WebSocket broadcasting |
| PATCH | `/api/v1/operators/{id}/verify`| JWT (admin) | Control Tower operator verification |

---

## Running Locally

### Prerequisites
- Docker Desktop
- Node.js 20+

### Start Infrastructure
```bash
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

### Required Environment Variables

Create `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://tourism:tourism@db:5432/tourism
REDIS_URL=redis://redis:6379/0
SECRET_KEY=super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Production Cloud Credentials
GEMINI_API_KEY=your_gemini_api_key_here
STRIPE_SECRET_KEY=your_stripe_secret_key
SENDGRID_API_KEY=your_sendgrid_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=your_bucket_name
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Production Deployment (render.yaml & vercel.json)

The repository contains Infrastructure-as-Code for zero-downtime deployments.
- **Backend**: Connected to Render.com via `render.yaml`. Auto-provisions PostgreSQL and Redis.
- **Frontend**: Connected to Vercel via `frontend/vercel.json`. Configured with strict security headers.
- See `DEPLOYMENT.md` for the exact step-by-step production runbook.

*Built by Antigravity AI - Google DeepMind*
