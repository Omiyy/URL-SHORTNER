# Load Testing Report — FastURL

This folder documents the load testing performed on FastURL using [Locust](https://locust.io/), including a real production-style bug that was found and fixed along the way, a measurement of Redis's cache impact, and a full capacity curve for the redirect endpoint under increasing concurrent load.

**Setup:** 4 horizontally-scaled FastAPI backend replicas behind an nginx reverse proxy (`least_conn` load balancing), PostgreSQL, and Redis — all running locally via Docker Compose. Locust was run with 8 worker processes to generate load, on a 12-core machine.

- [1. Bug found: Postgres connection pool exhaustion](#1-bug-found-postgres-connection-pool-exhaustion)
- [2. Redis cache impact](#2-redis-cache-impact)
- [3. Capacity curve](#3-capacity-curve)
- [How to reproduce](#how-to-reproduce)

---

## 1. Bug found: Postgres connection pool exhaustion

### The problem

Each backend replica was configured with `DB_POOL_SIZE=20` and `DB_MAX_OVERFLOW=40`, allowing up to **60 connections per replica**. With 4 replicas running, that's a possible **240 concurrent connections to Postgres** — while Postgres's default `max_connections` is **100**.

Under load, replicas collectively opened more connections than Postgres would accept, and the excess was rejected outright rather than queued.

### Evidence

| Metric | Result |
|---|---|
| Total requests | 757,214 |
| Failed requests | 344,943 |
| **Failure rate** | **45.6%** |
| Error types | `status 500`, `status 502` |
| p99 latency | 750ms |
| Max latency | 5,520ms |

See [`pool_bug_before_fix.html`](./pool_bug_before_fix.html) for the full report.

### The fix

Reduced per-replica pool size to `DB_POOL_SIZE=10` and `DB_MAX_OVERFLOW=10` → 20 connections per replica → **80 total across 4 replicas**, safely under Postgres's 100-connection ceiling.

**Result:** zero failures across every subsequent load test, from 100 up to 300 concurrent users (see [Section 3](#3-capacity-curve)).

---

## 2. Redis cache impact

Ran the full mixed API workload (auth, create, list, delete, stats, redirect together) twice, isolating the redirect endpoint's latency as the cache state varied:

| Run | Redirect avg latency | Redirect RPS |
|---|---|---|
| Less cache-warm | 35.21ms | 35.64 |
| Cache-warm | 9.52ms | 34.85 |

**~3.7x latency improvement** on the redirect (read) path once Redis is warm, at the same throughput — confirming the cache-first read strategy is doing real, measurable work. All other endpoints (auth, create, list, delete, stats) stayed consistent across both runs, isolating the effect to the cached path specifically.

Full reports: [`cache_test_v2_cold.html`](./cache_test_v2_cold.html), [`cache_test_v2_warm.html`](./cache_test_v2_warm.html).

---

## 3. Capacity curve

With the connection pool fix in place, tested the redirect endpoint alone at increasing concurrent user counts. Each run was measured after Locust's stat counters were reset post-ramp-up, to report clean steady-state numbers (excluding setup/ramp-up dilution).

| Users | RPS (steady-state) | Avg latency | p50 | p95 | p99 | Max | Failures | Backend CPU |
|---|---|---|---|---|---|---|---|---|
| 100 | 3,014.9 | 31.5ms | 32ms | 37ms | 42ms | 87ms | 0 | — |
| 150 | 2,308.9 | 63.6ms | 61ms | 83ms | 140ms | 369ms | 0 | — |
| 200 | 1,664.3 | 118.0ms | 100ms | 220ms | 310ms | 569ms | 0 | ~95% |
| 300 | 1,611.9 | 183.7ms | 170ms | 290ms | 390ms | 803ms | 0 | ~95% |

Full reports: [`capacity_100_users.html`](./capacity_100_users.html), [`capacity_150_users.html`](./capacity_150_users.html), [`capacity_200_users.html`](./capacity_200_users.html), [`capacity_300_users.html`](./capacity_300_users.html).

### Findings

- Throughput scales down and latency scales up predictably as concurrency increases — no anomalies, no instability.
- **Backend CPU saturates (~95% across all 4 replicas) by 200 concurrent users**, which is also where the RPS curve visibly flattens (200→300 users drops throughput only ~3%, vs. much steeper drops at lower user counts).
- **Zero failed requests at every tested load (100–300 users)** — the system degrades gracefully under overload (increasing latency) rather than failing outright, a direct result of the connection pool fix in Section 1.
- Postgres and Redis stayed well under capacity throughout (Postgres ~55% CPU, Redis ~8% CPU at peak load), confirming the **application layer, not the database, is the bottleneck** at this scale.

---

## How to reproduce

```bash
# 1. Bring up the full stack
docker compose up -d

# 2. Install Locust (in a virtualenv)
python -m venv venv && source venv/bin/activate
pip install locust

# 3. Capacity test (manual Start button, enter user count in the dashboard)
locust -f locustfile_capacity.py --host http://localhost:8000 --processes 8
# open http://localhost:8089, enter users/ramp rate, click Start
# once the RPS chart flattens, click "Reset" to zero counters, wait ~60-90s, then read Statistics

# 4. Cache impact test
python cache_test.py

# 5. Full mixed-workload test
locust -f locustfile.py --host http://localhost:8000
```

While tests run, watch `docker stats` in a separate terminal to monitor per-container CPU/memory.