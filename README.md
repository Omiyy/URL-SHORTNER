# FastURL: Production-Ready URL Shortener

FastURL is a mini Bitly-like service designed for high throughput with low database write pressure.

## Why PostgreSQL

- Strong consistency for URL mappings and analytics records.
- Mature indexing and transactional guarantees (critical for unique short code enforcement).
- Reliable operational tooling and easy horizontal scaling via read replicas.

## Architecture Summary

- Backend: FastAPI (async routes).
- Frontend: React + Vite + Tailwind CSS.
- Cache and write buffering: Redis.
- Primary database: PostgreSQL.
- Reverse proxy and rate limiting: Nginx.
- Deployment: Docker Compose.

## Folder Structure

```text
URL-SHORTNER/
  backend/
    app/
      core/
      db/
      models/
      routers/
      schemas/
      services/
      main.py
    .env.example
    Dockerfile
    requirements.txt
  frontend/
    src/
      api/
      components/
      pages/
      App.jsx
      index.css
      main.jsx
    .env.example
    Dockerfile
    index.html
    nginx.conf
    package.json
    postcss.config.js
    tailwind.config.js
    vite.config.js
  nginx/
    nginx.conf
  docker-compose.yml
  README.md
```

## API Endpoints

- `POST /api/shorten`
  - Input: `{ "url": "https://example.com" }`
  - Optional bonus fields: `custom_alias`, `expires_in_days`
  - Output: `{ "short_url": "http://domain/abc123", "short_code": "abc123" }`
- `GET /{short_code}`
  - Redirects with HTTP `302`
- `GET /api/stats/{short_code}`
  - Returns URL metadata and click count
- `GET /health`
  - Liveness and dependency checks (DB + Redis)

## Redis Buffering Strategy (Low DB Writes)

1. Redirect requests do **not** increment Postgres directly.
2. Each redirect runs `HINCRBY click_buffer {short_code} 1` in Redis.
3. Every 60 seconds, the worker:
   - Moves `click_buffer` to an inflight hash key (`click_buffer_inflight:{batch_id}`).
   - Flushes aggregated counts into Postgres in one transaction.
   - Stores `batch_id` in `click_flush_batches` to make the flush idempotent.
4. Inflight batches left from crashes are retried safely.

Redis AOF persistence (`appendonly yes`) reduces loss risk for buffered counts.

## Database Schema

### `urls`

- `id` (PK)
- `short_code` (unique indexed)
- `original_url`
- `clicks` (aggregated persisted count)
- `created_at`
- `last_accessed`
- `expires_at` (bonus feature)

### `click_flush_batches`

- `batch_id` (PK)
- `applied_at`

Used to ensure each batch of buffered clicks is applied at most once.

## Performance Notes (10,000 RPM / ~166 RPS)

- FastAPI async endpoints reduce I/O wait overhead.
- SQLAlchemy async engine with pooling (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`).
- Redis cache-first read path for redirects.
- Aggregated click writes every 60 seconds instead of per request.
- Nginx handles edge rate limiting and keeps backend focused on app logic.

## Nginx Rate Limiting

- Configured via:
  - `limit_req_zone $binary_remote_addr zone=api_limit:10m rate=4r/10s;`
- Applied on API routes (`/api/`) with burst control.

## Setup Instructions

1. Clone or open this repository.
2. Ensure Docker and Docker Compose are installed.
3. (Optional) Tune env values in `backend/.env.example` and `frontend/.env.example`.
4. Build and run all services:

```bash
docker compose up -d --build
```

5. Access application:
   - Frontend + public endpoint: `http://localhost`
   - Health check: `http://localhost/health`
   - FastAPI docs (direct backend): `http://localhost:8000/docs` (if backend port is exposed separately)

6. Stop services:

```bash
docker compose down
```

7. Stop and remove volumes (optional reset):

```bash
docker compose down -v
```

## Horizontal Scaling Strategy

- Scale FastAPI replicas behind Nginx (or migrate to Kubernetes + ingress).
- Keep Redis as a shared cache/buffer layer (single primary with replica/sentinel for HA).
- Use Postgres read replicas for analytics-heavy read traffic.
- Add CDN in front of Nginx for static frontend and edge caching.
- Move background flush logic to a dedicated worker container if traffic spikes significantly.

## Auto Deploy (GitHub -> Docker Hub -> Server)

This repo includes CI/CD workflow in `.github/workflows/deploy.yml`.

On every push to `main`, it:

1. Builds backend and frontend Docker images.
2. Pushes tags to Docker Hub:
  - `omsinghal852/url-shortner:backend-latest`
  - `omsinghal852/url-shortner:frontend-latest`
3. SSHes into your server and runs:
  - `docker compose -f docker-compose.prod.yml pull`
  - `docker compose -f docker-compose.prod.yml up -d --remove-orphans`

### One-Time Server Setup

1. Install Docker and Docker Compose plugin.
2. Clone this repo on the server, for example:

```bash
mkdir -p /opt/url-shortner
cd /opt/url-shortner
git clone https://github.com/Omiyy/URL-SHORTNER .
```

3. Create `backend/.env` on the server with production values (Neon, Upstash, domain, CORS).
4. Run once manually:

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Required GitHub Secrets

Add these in GitHub repo -> Settings -> Secrets and variables -> Actions:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_SSH_KEY`
- `SERVER_PORT` (optional, default 22)
- `APP_DIR` (example: `/opt/url-shortner`)

### Notes

- Use branch protection on `main` so only reviewed code auto deploys.
- Rotate secrets regularly.
- Keep `backend/.env` only on server, never commit real credentials.
