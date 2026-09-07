# Production Deployment Guide: AI Tourism Ecosystem

This document provides comprehensive, production-grade deployment instructions for the AI Tourism Ecosystem. The infrastructure architecture decouples the Next.js frontend on Vercel Edge Network from the FastAPI modular monolith backend, PostgreSQL relational database, and Redis cache on Render.

---

## 1. System Architecture Overview

The production environment consists of two isolated hosting tiers connected via secure HTTPS and internal VPC networking:

```
[ Client Browser ]
        |
        | HTTPS (Port 443)
        v
[ Vercel Edge Network ] (frontend/ Next.js 14)
        |
        | HTTPS (Port 443) / CORS
        v
[ Render Web Service ] (backend/ FastAPI + Uvicorn)
        |
        +---> [ Render Private Network ] ---> [ PostgreSQL 15 ] (Port 5432)
        |
        +---> [ Render Private Network ] ---> [ Redis 7 ] (Port 6379)
        |
        +---> HTTPS External API ---> [ Google Gemini AI Studio ]
```

### Component Roles

* **Frontend (Vercel)**: Next.js 14 serverless application, serving client interfaces, responsive dashboards, and client-side state caching with global edge routing.
* **Backend (Render Web Service)**: FastAPI application running on Python 3.11 with Uvicorn ASGI workers (`uvicorn app.main:app --host 0.0.0.0 --port 10000`).
* **Relational Database (Render PostgreSQL)**: Persistent PostgreSQL 15 database storing users, destinations, bookings, operator accounts, and itineraries.
* **Cache & State Store (Render Redis)**: In-memory Redis 7 instance for SlowAPI rate limiting, session management, and ephemeral caching.
* **AI Intelligence Layer (Google Gemini)**: Generates customized multi-day itineraries and contextual recommendations with deterministic heuristic fallback when keys are absent.

---

## 2. Prerequisites

Ensure the following prerequisites are met before initiating deployment:

1. **Version Control**: The project repository pushed to GitHub or GitLab.
2. **Render Account**: Active account at [render.com](https://render.com).
3. **Vercel Account**: Active account at [vercel.com](https://vercel.com).
4. **Google Gemini API Key**: API key generated from [Google AI Studio](https://aistudio.google.com/) (required for generative itinerary planning).
5. **Local Tools (Optional)**: Git, Python 3.11, Node.js 18+, and OpenSSL for secret generation.

---

## 3. Backend Deployment on Render

Render manages the web service, database, and Redis cache declaratively through the `render.yaml` Blueprint located in the project root.

### 3.1 Blueprint Specification (`render.yaml`)

The root `render.yaml` defines three coordinated resources:

```yaml
services:
  - type: web
    name: tourism-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install --no-cache-dir -r requirements.txt
    preDeployCommand: alembic upgrade head
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port 10000
    plan: starter
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: tourism-postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: tourism-redis
          property: connectionString
      - key: PORT
        value: 10000
      - key: PYTHON_VERSION
        value: 3.11.8
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: "false"
      - key: SECRET_KEY
        generateValue: true
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 10080
      - key: CORS_ORIGINS
        value: "*"
      - key: GEMINI_API_KEY
        sync: false
      - key: GEMINI_MODEL
        value: gemini-1.5-flash
      - key: AI_FALLBACK_TO_RULES
        value: "true"

  - type: redis
    name: tourism-redis
    plan: starter
    ipAllowList: []
    maxmemoryPolicy: allkeys-lru

databases:
  - name: tourism-postgres
    databaseName: tourism_db
    user: tourism_user
    plan: starter
    ipAllowList: []
```

### 3.2 Step-by-Step Blueprint Deployment

1. Log into your **Render Dashboard**.
2. Click **New +** at the top right and select **Blueprint**.
3. Connect your Git repository containing the AI Tourism Ecosystem project.
4. Render scans and detects the `render.yaml` file in the root directory.
5. In the blueprint creation review screen, verify the three resources:
   * `tourism-postgres` (Database)
   * `tourism-redis` (Redis)
   * `tourism-backend` (Web Service)
6. Supply the required environment variable values prompted by the dashboard:
   * **`GEMINI_API_KEY`**: Paste your Google Gemini API key. If omitted, the platform operates in rule-based fallback mode.
   * **`CORS_ORIGINS`**: Set to your Vercel deployment URL (e.g., `https://tourism-ecosystem.vercel.app`), comma-separated if multiple domains are used.
7. Click **Apply**.
8. Render automatically provisions the database and Redis first, generates an internal private network connection string for each, and passes them to `tourism-backend`.
9. The build phase executes `pip install --no-cache-dir -r requirements.txt`.
10. The pre-deploy phase executes `alembic upgrade head` to run all database schema migrations against the newly created database.
11. The service boots using `uvicorn app.main:app --host 0.0.0.0 --port 10000` and validates against the `/health` endpoint.
12. Copy the public backend service URL (e.g., `https://tourism-backend.onrender.com`).

---

## 4. Frontend Deployment on Vercel

The Next.js 14 frontend resides in the `frontend/` subdirectory and is configured using `frontend/vercel.json`.

### 4.1 Vercel Configuration (`frontend/vercel.json`)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm install",
  "cleanUrls": true,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=()"
        },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=63072000; includeSubDomains; preload"
        }
      ]
    },
    {
      "source": "/_next/static/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### 4.2 Step-by-Step Vercel Deployment

1. Log into your **Vercel Dashboard**.
2. Click **Add New...** and select **Project**.
3. Import the Git repository.
4. Under **Project Configuration**:
   * **Framework Preset**: Ensure `Next.js` is selected.
   * **Root Directory**: Click **Edit** and choose `frontend`.
5. Under **Environment Variables**, add the following variable:
   * **Key**: `NEXT_PUBLIC_API_URL`
   * **Value**: `https://<your-render-backend-url>/api/v1` (e.g., `https://tourism-backend.onrender.com/api/v1`)
   * Note: Ensure this contains the `/api/v1` suffix and has no trailing slash.
6. Click **Deploy**.
7. Vercel executes `npm install`, followed by `npm run build`, and distributes static and server-rendered assets across edge regions.
8. Once deployment finishes, copy the generated production URL (e.g., `https://tourism-frontend.vercel.app`).

---

## 5. Aligning Cross-Origin Resource Sharing (CORS)

For security, the FastAPI backend restricts browser cross-origin requests.

1. Navigate to your **Render Dashboard** > **Web Service (tourism-backend)** > **Environment**.
2. Update the `CORS_ORIGINS` variable with your actual Vercel domains:
   ```env
   CORS_ORIGINS=https://tourism-frontend.vercel.app,https://your-custom-domain.com
   ```
3. Multiple origins can be specified as a comma-separated string or as a JSON array (`["https://...", "https://..."]`).
4. Click **Save Changes**. Render performs a rolling restart to apply the updated origins.

---

## 6. Database Migrations and Data Initialization

### 6.1 Automated Migrations

Every deployment on Render runs `preDeployCommand: alembic upgrade head` prior to serving traffic. If a migration fails, the deployment halts, preventing partial or corrupt schema updates from reaching live traffic.

### 6.2 Manual Migrations (Render Shell)

If you need to verify migration status or run specific revisions manually:

1. In the Render Dashboard, open `tourism-backend` and navigate to the **Shell** tab.
2. Run:
   ```bash
   alembic current
   alembic upgrade head
   ```

### 6.3 Seeding Initial Data

To populate sample destinations and test datasets in production:

1. Open the **Shell** tab on `tourism-backend` in the Render Dashboard.
2. Execute the seed script:
   ```bash
   python -m app.seed
   ```
3. The script populates initial destinations (such as Bali, Santorini, Kyoto, Reykjavik, and Amalfi Coast) idempotently.

---

## 7. Post-Deployment Verification Checklist

Verify all services and integration points using terminal commands or HTTP clients:

### 7.1 Backend Probes

Check system health probe:
```bash
curl -s https://<your-backend-url>/health | jq .
```
Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "message": "AI Tourism Ecosystem API is running",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

Check API root:
```bash
curl -s https://<your-backend-url>/api/v1 | jq .
```
Expected response:
```json
{
  "message": "AI Tourism Operating System API v1",
  "status": "active",
  "modules": [
    "destinations",
    "itineraries",
    "auth",
    "control-tower",
    "bookings",
    "operators",
    "chat"
  ]
}
```

Check destinations listing:
```bash
curl -s "https://<your-backend-url>/api/v1/destinations?limit=5" | jq .
```

### 7.2 Frontend Verification

1. Open the Vercel production URL in a browser.
2. Verify that destination cards and images load correctly.
3. Open Browser Developer Tools > Console and Network tabs:
   * Ensure no CORS errors (`Access-Control-Allow-Origin`) are present.
   * Verify that API requests target `https://<your-backend-url>/api/v1/...`.
4. Test AI Itinerary Generation:
   * Select a destination and click **Generate Itinerary**.
   * Verify the structured multi-day itinerary returns successfully.

---

## 8. Troubleshooting Reference

| Symptom | Probable Cause | Remediation |
| :--- | :--- | :--- |
| Backend crashes on startup with `NoSuchModuleError` or `ArgumentError` regarding database driver | Database URL begins with `postgres://` instead of `postgresql+asyncpg://` | The backend application automatically transforms `postgres://` to `postgresql+asyncpg://` in `app/core/config.py` and `alembic/env.py`. Verify that the latest version of code containing this handler is deployed. |
| Browser console displays `CORS policy: No 'Access-Control-Allow-Origin' header` | Frontend domain not present in backend `CORS_ORIGINS` | Add the Vercel domain to `CORS_ORIGINS` in Render dashboard environment settings without trailing slashes. |
| Health check reports `database: unreachable` | PostgreSQL instance not finished provisioning or connection pool exhaustion | Check the PostgreSQL service status on Render. Verify `DATABASE_URL` matches the internal connection string of `tourism-postgres`. |
| Health check reports `redis: unreachable` | Redis service inactive or unreachable via internal network | Confirm `tourism-redis` service is active and `REDIS_URL` matches internal connection string. |
| AI Itinerary falls back to default schedule | `GEMINI_API_KEY` is not provided, expired, or quota exceeded | Check Render environment variables for `GEMINI_API_KEY`. When invalid or unset, the system defaults to deterministic heuristic generation (`AI_FALLBACK_TO_RULES=True`). |
| Vercel build fails with `Module not found` | Root directory is not set to `frontend` | In Vercel Project Settings > General, set **Root Directory** to `frontend`. |

---

## 9. Security and Maintenance Best Practices

1. **Secret Generation**: Always generate cryptographically secure random values for `SECRET_KEY`:
   ```bash
   openssl rand -hex 32
   ```
2. **Private Network Isolation**: Both PostgreSQL and Redis have empty IP allowlists (`ipAllowList: []`), preventing any external internet traffic from reaching database or cache ports. Communication occurs solely through the Render private network.
3. **HTTP Security Headers**: The `frontend/vercel.json` applies HTTP Strict Transport Security (HSTS), X-Frame-Options (`DENY`), X-Content-Type-Options (`nosniff`), and strict Referrer-Policy headers to protect against clickjacking and MIME-sniffing.
4. **Rate Limiting**: Rate limits are enforced on the backend via SlowAPI and Redis to mitigate denial-of-service and brute-force authentication attacks.
5. **Database Backups**: Render managed PostgreSQL includes daily automated backups with point-in-time recovery on standard plans.
