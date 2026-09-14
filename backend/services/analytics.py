"""
Usage analytics — request volume, latency, error rate, and cost-per-call —
written to the `events` table in the project's existing Supabase instance
(see db/migrations/003_events.sql). No PostHog: this project already has
Supabase credentials configured, so reuse that instead of standing up
another free-tier service.

Best-effort: a failed analytics write is logged and swallowed, never raised —
telemetry must not break the request it's attached to.

Cost figures are the real, documented per-call prices already tracked
elsewhere in this repo (services/face_analysis.py docstring, .env.example) —
not estimates:
  - face analysis (Gemini 2.5 Flash Lite via Segmind): $0.00011/call
  - try-on generation (Segmind Nano Banana 2 Lite):     $0.04/call
"""
import asyncio

import structlog

from db import client as db

log = structlog.get_logger(__name__)

COST_FACE_ANALYSIS_USD = 0.00011
COST_GENERATION_USD = 0.04


async def capture(distinct_id: str, event: str, properties: dict | None = None) -> None:
    """Supabase's client is sync/blocking — runs in a thread so it never
    stalls the event loop. Errors are logged and swallowed: telemetry must
    not break the request it's attached to."""
    try:
        await asyncio.to_thread(db.insert_event, event, distinct_id, properties or {})
    except Exception:
        log.error("analytics_capture_failed", event=event)
