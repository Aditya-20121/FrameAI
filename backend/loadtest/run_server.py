"""
Runs the real FastAPI app locally for load testing, with only the paid
Segmind call mocked (per ground rule: don't burn real API quota under load).
Everything else — session/job/frame lookups, generation_tasks inserts,
the atomic generations_used increment — hits the real (free-tier) Supabase
project for real, so the load test measures the actual infrastructure.

Usage: python loadtest/run_server.py [port]
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["GENERATION_LIMIT_OVERRIDE"] = "999999"
os.environ["GENERATE_RATE_LIMIT_OVERRIDE"] = "100000/second"

import services.generation as gen_svc


async def _fake_call_segmind(person_url: str, frame_url: str, prompt: str) -> bytes:
    # No real network call. A small sleep keeps this an async-realistic stand-in
    # for "some I/O happens" without claiming a specific real Segmind latency
    # (we don't have one measured — generation is disabled in production).
    await asyncio.sleep(0.05)
    return b"\xff\xd8\xff\xe0fake-jpeg-bytes-for-load-test"


gen_svc._call_segmind = _fake_call_segmind

import uvicorn
import main

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8125
    uvicorn.run(main.app, host="127.0.0.1", port=port, log_level="warning")
