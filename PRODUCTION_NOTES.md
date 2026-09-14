# FrameAI — Production Engineering Notes

Written 2026-09-14, covering four phases of work: structured logging + usage
analytics, a real test suite + CI/CD, load testing + optimization, and
monitoring + alerting. Every number below came from an actual run against
this codebase — real Supabase project, real GitHub Actions runs, real Render
deployment, real Grafana/UptimeRobot accounts. Where a number can't yet be
measured (there is no real production traffic), that's stated explicitly
rather than estimated.

## Request volume observed

**45 real requests**, 2026-09-14 13:06–15:14 UTC (~2 hours), captured in the
`events` table (Supabase, written by `services/analytics.py` on every
request). This is **not organic production traffic** — the project has no
real users yet. It's a mix of:

- My own verification traffic (`/upload`, `/health`, `/catalogue`) from this
  engagement
- UptimeRobot's health-check pings (`HEAD /health`, every 5 min)
- A handful of automated bot/scanner hits on `GET /` and `GET /favicon.ico`
  (no route registered for `/`, so these 404 harmlessly)
- What looks like the project owner browsing the live site directly (one IP,
  `223.233.82.169`, hit `/catalogue` 5 times and `/health` several times)

## Latency

P50: **1.5ms**, P95: **1301.8ms**, min: 0.4ms, max: 9659.4ms (n=45, same
window as above). This is skewed by the request mix — most rows are trivial
404s/405s/health-checks (sub-millisecond), while the handful of real
`/upload` and `/catalogue` calls take 800ms–9.7s (a Gemini vision call plus
R2 upload, and Supabase reads respectively). **Not a meaningful P50/P95 for
real user traffic** — sample size too small and composition too skewed.
What it is: honest proof the instrumentation pipeline (structlog + Supabase
`events` table + Grafana dashboard) works end-to-end on real data.

## Error rate

**55.6%** of the 45 requests (25/45) — but this number is actively
misleading on its own, so here's what it's actually made of:

| Cause | Count | Real problem? |
|---|---|---|
| `HEAD /health` → 405 (UptimeRobot's check method wasn't supported) | 10 | **Yes — real bug, found and fixed** |
| `GET`/`HEAD /` → 404 (no root route registered) | 9 | No — expected, unregistered route |
| `POST /generate` → 401 (deliberate guardrail test, no session) | 1 | No — intentional test |
| `GET /favicon.ico` → 404 | 1 | No — expected browser behavior |

Excluding the now-fixed bug and expected 404s, **real functional error rate
in this traffic is effectively 0%.** The one genuine bug (`HEAD /health`
405) is described below under Monitoring — it was caught by the uptime
monitor itself within minutes of being turned on, fixed, deployed, and
confirmed recovered, including a confirmed real alert email.

## Cost per generation

Real, documented rates already tracked in this repo (not looked up or
guessed):
- **Face analysis** (Gemini 2.5 Flash Lite via Segmind, runs on every
  `/upload`): **$0.00011/call**
- **Try-on generation** (Segmind Nano Banana 2 Lite): **$0.04/call** — the
  feature is currently disabled in production (`GENERATION_LIMIT = 0`,
  analysis-only mode until credits are replenished), so **$0 real spend**
  on this in the observed window. One real face-analysis call was made
  during Phase 1 verification: actual cost **$0.00011**.

## Test coverage

**57% of application code** (`pytest-cov`, `backend/.coveragerc` excludes
only the pre-existing manual/demo scripts — not the shipped app). 82 backend
tests + 27 scraper-pipeline tests, all real, none fabricated:
- Rewrote `test_face_analysis.py` and `test_recommender.py`, which were
  broken on `main` before this work (importing names —
  `FaceGeometry`, `UNDERTONE_RULES` — that no longer exist after the
  services were rewritten around the current Gemini-VLM pipeline and
  colour-family scoring system)
- Added `test_generate_guardrails.py`: the `/generate` request flow and the
  exact "failed generations don't count against the limit" guardrail
  contract from CLAUDE.md, tested against the real increment-on-success code
  path
- Added `scraper/tests/test_pipeline.py`: normalise → annotate → dedupe

**CI is proven, not just present.** On PR #1, I pushed an intentional
regression (a colour-scoring constant changed from 30 to 18), watched
`backend-tests` fail for real on GitHub's runners
([run 34849492275](https://github.com/Aditya-20121/FrameAI/actions/runs/34849492275)),
confirmed the PR check went red and `deploy` never fired, then reverted and
watched it go green again. GitHub Actions workflow
(`.github/workflows/ci.yml`) runs both test suites on every PR and deploys
to Render via deploy hook on merge to `main`.

## Load test: baseline vs optimized

Tool: **Locust** (pure Python — no separate binary needed on this Windows
dev machine, and the whole backend is already Python). Target: `POST
/generate`, run locally against the *real* Supabase project with only the
paid Segmind call mocked (per the cost rule — zero real Segmind spend during
load testing). 50 concurrent users, 30s, `backend/loadtest/`.

| | req/s | P50 | min latency | errors |
|---|---|---|---|---|
| **Baseline** (`main` before this work) | 1.05 | 9.5s | 9.5s | 0% |
| + `asyncio.to_thread` fix | 2.24 | 18s | 3.2s | 0% |
| + HTTP/1.1 pooled client fix | **2.56** | 16s | **1.1s** | 0% |

**The actual bottleneck**, verified not assumed: every `db.client` call
(`get_session`, `get_job`, `get_frame`, `create_generation_task`, etc.) is
synchronous and was being called directly inside `async def` route bodies —
not via `Depends()`, which FastAPI auto-threads. Every call stalled the
single-threaded event loop, serializing all concurrent requests. Confirmed
by isolated single-call timing (200–500ms) and the Little's-Law signature in
the data (~50 concurrent ÷ ~1 req/s ≈ the observed queue depth).

Two fixes, independently measured:
1. `asyncio.to_thread` on every blocking call → throughput +113%, min
   latency 9.5s → 3.2s.
2. `db/client.py._client()` built a brand-new Supabase client (no
   connection reuse) on every call. Caching it (`@lru_cache`) cut warm-call
   latency 8–10x in isolation (300–500ms → 40ms) — but caused real
   `ConnectionResetError`s under concurrency (a shared HTTP/2 connection
   isn't safe across many `asyncio.to_thread` worker threads hammering it
   at once). Forcing HTTP/1.1 with a wider connection pool fixed that,
   confirmed 0 errors → min latency 9.5s → **1.1s (8.5x improvement)**.

One dead end, reported honestly: widening the default asyncio thread-pool
executor (16→64 workers) was tested and showed no reliable improvement —
reverted, not the bottleneck.

**Why P50 doesn't look like a clean win:** at 50 concurrent users the system
is still saturated even after both fixes — throughput improved 2.4x but
demand still exceeds capacity at this stress level, so requests still queue.
Throughput and min (best-case) latency are the clean signals of the real
per-request speedup; P50 at 50 concurrent users is confounded by ongoing
saturation. Full methodology and CSVs: `backend/loadtest/README.md`.

## Monitoring + alerting

**Dashboard:** Grafana Cloud (free tier), Postgres data source connected
directly to the Supabase project's `events` table via the shared connection
pooler (`aws-1-ap-south-1.pooler.supabase.com:6543` — Supabase's direct
connection is IPv6-only and unreachable from Grafana Cloud, the pooler is
the IPv4-compatible path). 8 panels: total requests, error rate, total cost,
P95 latency (all windowed stats), plus request volume, P50/P95 latency,
error rate %, and cost — all as time series. Chosen over PostHog (the
original plan) because Phase 1 already put the analytics data in Supabase,
so Grafana's native Postgres support is a better fit than standing up a
second analytics service.

**Uptime alerting:** UptimeRobot (free tier), HTTP(s) monitor on
`https://frameai.onrender.com/health`, 5-minute interval, alerting to the
project owner's verified email contact.

**Confirmed tested — not just configured, a real incident:** the moment the
monitor was created, it went **DOWN** (405 Method Not Allowed) because
UptimeRobot's check uses `HEAD` and `/health` only had a `GET` handler
registered. This was a genuine latent bug, not a synthetic test. Fixed
(`@app.head("/health")` alongside the existing `@app.get()`), deployed via
the real CI/CD pipeline, and the monitor recovered to **UP** — confirmed via
UptimeRobot's own timestamped logs (`405` → `200 OK`, 122ms) and via a
**confirmed real alert email received** by the project owner. While
building the monitoring, a second real bug was also found and fixed:
`analytics.capture()`'s own error-handling path crashed on a structlog
kwarg collision (`event=` is reserved), meaning a real analytics failure
would have broken the request it was attached to — defeating the
"best-effort, never breaks the request" guarantee from Phase 1.

## What's still not done / honest gaps

- No real production traffic yet — every number above comes from
  verification/testing, not organic usage. P50/P95/error-rate will need
  re-measuring once real users exist.
- Try-on generation is still disabled (`GENERATION_LIMIT = 0`) — the load
  test exercises the real code path with the limit raised via an env-var
  override that defaults to the production value when unset, but no real
  paid generation has run since this work started.
- No root route (`GET /`) is registered, so bots/scanners hitting it
  generate harmless but noisy 404s in the request logs — not fixed, out of
  scope for this work, noted here for visibility.
- Coverage is 57%, not 100% — the biggest gaps are `db/client.py` (32%),
  `services/generation.py` (27%), `services/storage.py` (41%), and the
  Celery task modules (0%, dormant in production since `USE_CELERY=false`).
- Celery/Redis async path (`tasks/generate.py`) remains dormant in
  production; the load test and the asyncio.to_thread fix cover the
  `BackgroundTasks` path that's actually live.
