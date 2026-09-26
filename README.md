# FastURL

Production-style URL shortener built to handle high-throughput redirect
traffic by decoupling write-heavy click tracking from the hot redirect path.

**Stack:** FastAPI (async) · PostgreSQL (`asyncpg`) · Upstash Redis ·
React + Vite + Tailwind · Docker · Render + Vercel

---

## Table of contents

- [Architecture](#architecture)
- [Why Redis](#why-redis-the-stateless-tradeoff)
- [Background click flushing](#background-click-flushing-idempotent)
- [Redis eviction policy](#redis-eviction-policy)
- [Short code generation](#short-code-generation-strategy)
- [Authentication](#authentication-stateless--secure-rotation)
- [Deliberate omissions](#deliberate-omissions-tradeoffs-accepted)
- [Database schema](#database-schema)
- [Setup & deployment](#setup--deployment)

---

## Architecture

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI, async routes | high concurrency, low I/O wait overhead |
| Primary DB | PostgreSQL via SQLAlchemy + `asyncpg` | source of truth, ACID writes |
| Cache / write buffer | Upstash Redis (serverless) | absorbs click-write load off Postgres |
| Frontend | React + Vite + Tailwind | fast dev loop, small bundle |
| Deployment | Docker, Render (API) + Vercel (frontend) | container parity between local/prod |

```
Browser → Vercel (React SPA) → Render (FastAPI, Docker)
                                     ├── PostgreSQL (source of truth)
                                     └── Redis (cache + write buffer)
```

---

## Why Redis? (The "stateless" tradeoff)

If every `302` redirect ran `UPDATE urls SET no_of_clicks = no_of_clicks + 1`
directly against Postgres, the database would become a write bottleneck under
real traffic. Redis sits in front of that path as both a **read-through
cache** and a **write-behind buffer**:

1. **Cache** — lookups check Redis (`url:{code}`) first; misses fall back to
   Postgres and get written into Redis with a TTL (default 1 hour).
2. **Write buffer** — redirects never touch Postgres directly. They increment
   an in-memory hash counter: `HINCRBY click_buffer {short_code} 1`.
3. **Fallback** — if Redis is unreachable, the API catches `RedisError` and
   falls back to reading/writing Postgres directly. This is a deliberate
   choice to prioritize availability over performance during a cache outage,
   rather than failing the redirect.

---

## Background click flushing (idempotent)

A background worker runs every `CLICK_FLUSH_INTERVAL_SECONDS` (default 60s):

1. Renames `click_buffer` to an inflight key: `click_buffer_inflight:{batch_id}`.
2. Reads the aggregated counts and bulk-updates Postgres in one transaction.
3. Records the `batch_id` in `click_flush_batches`.

**Crash safety:** if the worker dies before deleting the inflight key, the
next loop retries it. The `click_flush_batches` table guarantees a batch is
only ever applied to Postgres once, even on retry.

---

## Redis eviction policy

Configured in `redis.conf` as `maxmemory-policy volatile-lru`.

| Key type | TTL | Evictable |
|---|---|---|
| Read cache (`url:{code}`) | yes (default 1h) | yes |
| Click buffer (`click_buffer`) | none | **no** — must survive until flushed |
| Deletion tombstones | none | **no** — must survive until purge worker runs |

---

## Short code generation strategy

- 7-character Base62 (`A–Z`, `a–z`, `0–9`) → ~3.5 trillion possible codes.
- Generated with `secrets.choice` (cryptographically secure, not `random`).
- On a Postgres `IntegrityError` collision, retries up to
  `MAX_GENERATION_ATTEMPTS` (8) times. Custom aliases are rejected
  immediately on collision instead of retried.

---

## Authentication (stateless + secure rotation)

| Token | Lifetime | Transport | Notes |
|---|---|---|---|
| Access token | 15 min | JWT in `Authorization` header | held in frontend memory only |
| Refresh token | 7 days | random token, `HttpOnly` + `Secure` cookie | rotated on every use |

**Rotation & replay detection:** every refresh issues a new token and
revokes the old one. Tokens share a `family_id`. If a *revoked* token is
reused — the signature of a stolen/replayed token — the backend detects the
replay and revokes the entire family immediately, forcing re-login.

---

## Deliberate omissions (tradeoffs accepted)

| Decision | Reasoning |
|---|---|
| No anonymous URL shortening | keeps creation behind an auth boundary — simpler abuse tracking, smaller attack surface |
| Eventual consistency on click counts | Postgres can lag up to 60s behind real clicks; `/api/urls/{code}/stats` reads Postgres **and** the live Redis buffer to return an accurate count regardless |
| No hard deletes | delete sets `deleted_at`; a background worker purges rows after `DELETED_URL_RETENTION_SECONDS` (default 24h) |

---

## Database schema

```mermaid
erDiagram
    USERS ||--o{ URLS : creates
    USERS ||--o{ REFRESH_SESSIONS : has

    USERS {
        UUID user_id PK
        VARCHAR user_name UK
        VARCHAR password_hash
        TIMESTAMPTZ created_at
    }
    URLS {
        VARCHAR short_code PK
        UUID user_id FK
        TEXT original_url
        BIGINT no_of_clicks
        TIMESTAMPTZ created_at
        TIMESTAMPTZ deleted_at
    }
    REFRESH_SESSIONS {
        UUID session_id PK
        UUID family_id
        UUID user_id FK
        VARCHAR token_hash UK
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ created_at
        TIMESTAMPTZ last_used_at
        TIMESTAMPTZ revoked_at
    }
    CLICK_FLUSH_BATCHES {
        VARCHAR batch_id PK
        TIMESTAMPTZ applied_at
    }
```

<details>
<summary>Table definitions</summary>

**`users`**

| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID, PK | |
| `user_name` | VARCHAR(30), UNIQUE, indexed | |
| `password_hash` | VARCHAR(255) | |
| `created_at` | TIMESTAMPTZ | |

**`urls`**

| Column | Type | Notes |
|---|---|---|
| `short_code` | VARCHAR(32), PK | hot lookup path for every redirect |
| `user_id` | UUID, FK → `users.user_id`, indexed | |
| `original_url` | TEXT | |
| `no_of_clicks` | BIGINT, default 0 | eventually consistent — see above |
| `created_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ, nullable | soft-delete tombstone |

**`refresh_sessions`**

| Column | Type | Notes |
|---|---|---|
| `session_id` | UUID, PK | |
| `family_id` | UUID, indexed | groups rotated tokens for replay detection |
| `user_id` | UUID, FK → `users.user_id` | |
| `token_hash` | VARCHAR(64), UNIQUE | |
| `expires_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |
| `last_used_at` | TIMESTAMPTZ, nullable | |
| `revoked_at` | TIMESTAMPTZ, nullable | |

**`click_flush_batches`**

| Column | Type | Notes |
|---|---|---|
| `batch_id` | VARCHAR(64), PK | idempotency key for the flush worker |
| `applied_at` | TIMESTAMPTZ, default now() | |

</details>

---

## Setup & deployment

### Run locally

```bash
cd backend
docker build -t fasturl-api .
docker run --name fasturl-api -p 8000:8000 --env-file .env fasturl-api
```

### Environment variables

Read dynamically via Pydantic Settings.

**Required**

| Variable | Example |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL` | `rediss://default:pass@host:6379` |
| `JWT_SECRET_KEY` | — |

**Required for production**

| Variable | Notes |
|---|---|
| `APP_DOMAIN` | base URL for generated short links |
| `FRONTEND_ORIGIN` | drives CORS |
| `REFRESH_COOKIE_SECURE` | `true` — requires HTTPS |
| `REFRESH_COOKIE_SAMESITE` | `none` — required for Render ↔ Vercel cross-origin |

**Optional tunables**

| Variable | Default |
|---|---|
| `DB_POOL_SIZE` | 10 |
| `REDIS_CACHE_TTL_SECONDS` | 3600 |
| `REDIS_SOCKET_TIMEOUT_SECONDS` | 10 |
| `CLICK_FLUSH_INTERVAL_SECONDS` | 60 |
| `DELETED_URL_RETENTION_SECONDS` | 86400 |