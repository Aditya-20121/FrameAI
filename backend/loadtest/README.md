# Load test harness — POST /generate

Local-only. Runs the real app against the real (free-tier) Supabase project,
with only the paid Segmind call mocked — per the project's cost rule, never
pay for real generations just to load-test infrastructure.

## Run

```bash
pip install locust
python loadtest/seed.py                 # creates one real session/job/frame, writes seed_data.json
python loadtest/run_server.py 8125       # runs main.app with _call_segmind mocked + limits raised
# in another terminal:
locust -f loadtest/locustfile.py --host http://127.0.0.1:8125 --headless -u 50 -r 10 -t 30s
python loadtest/cleanup.py               # deletes the disposable seeded rows afterward
```

`GENERATION_LIMIT_OVERRIDE` and `GENERATE_RATE_LIMIT_OVERRIDE` (set by
run_server.py, read by api/generate.py) only exist so this harness can drive
real concurrent traffic through the guardrail-disabled/rate-limited route —
both default to the real production values when unset, so they don't affect
any real deployment.

## Real results (see PRODUCTION_NOTES.md for the full writeup)

50 concurrent users, 30s, against `main` before this load-testing work:

| | req/s | P50 | min latency | errors |
|---|---|---|---|---|
| baseline | 1.05 | 9.5s | 9.5s | 0% |
| + asyncio.to_thread fix | 2.24 | 18s | 3.2s | 0% |
| + HTTP/1.1 pooled client | 2.56 | 16s | 1.1s | 0% |

P50 looks worse after the fixes because more requests are being admitted per
second into a system that's still saturated at 50 concurrent users (Little's
Law: ~50 concurrent ÷ ~2.5 req/s ≈ 20s average wait) — min latency (best case,
no queuing) is the cleaner signal of the actual per-request speedup: 9.5s → 1.1s.

An intermediate attempt (bare `@lru_cache` on the Supabase client, still
HTTP/2) hit real `ConnectionResetError`s under concurrency — a shared HTTP/2
connection isn't safe across many `asyncio.to_thread` worker threads. Forcing
HTTP/1.1 with a wider connection pool fixed it. Widening the default asyncio
thread-pool executor (16 → 64 workers) was also tried and showed no reliable
improvement — not the bottleneck.
