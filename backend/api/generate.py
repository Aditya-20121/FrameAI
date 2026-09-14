"""
POST /generate          — queue a try-on generation for one frame.
GET  /generate/{task_id} — poll status + get presigned image URL when done.

Generation limit is server-enforced (never trust the client).
Counter increments atomically only on successful completion.
Failed generations do NOT count against the limit.

Worker strategy:
  - Production (ENVIRONMENT=production): Celery + Redis (Upstash)
  - Development (default):               FastAPI BackgroundTasks (no worker needed)
"""
import asyncio
import logging
import os
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from api.session import require_session
from limiter import limiter
from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    GenerateLimitError,
    GenerationStatus,
)
from db import client as db
from services import storage, generation as gen_svc

log = logging.getLogger(__name__)
router = APIRouter()

# try-on generation disabled — analysis-only mode until credits are replenished.
# GENERATION_LIMIT_OVERRIDE / GENERATE_RATE_LIMIT_OVERRIDE exist solely for local
# load testing (see backend/loadtest/) — unset in every real deployment, so
# production behaviour is unchanged.
GENERATION_LIMIT = int(os.getenv("GENERATION_LIMIT_OVERRIDE", "0"))
_GENERATE_RATE_LIMIT = os.getenv("GENERATE_RATE_LIMIT_OVERRIDE", "10/hour")
_IS_PROD    = os.getenv("ENVIRONMENT", "development").lower() == "production"
_USE_CELERY = os.getenv("USE_CELERY", "false").lower() == "true"


async def _run_generation_bg(task_id: str, job_id: str, frame_id: str, session_token: str) -> None:
    """Async background function — awaited by FastAPI BackgroundTasks (dev mode).

    Every db.client call is blocking (sync Supabase client) — wrapped in
    asyncio.to_thread so it doesn't stall the event loop for other requests
    being served concurrently. See PRODUCTION_NOTES.md for the load test that
    found this serializing all concurrent /generate traffic.
    """
    await asyncio.to_thread(db.update_generation_task, task_id, status="processing")
    try:
        frame = await asyncio.to_thread(db.get_frame, frame_id)
        if not frame:
            log.error("Frame %s not found for task %s", frame_id, task_id)
            await asyncio.to_thread(db.update_generation_task, task_id, status="failed")
            return
        r2_key = await gen_svc.generate_try_on(job_id, frame, task_id, distinct_id=session_token)
        from config import settings as _settings
        image_url = f"{_settings.r2_public_domain}/{r2_key}"
        await asyncio.to_thread(
            db.update_generation_task,
            task_id,
            status="complete",
            image_r2_key=r2_key,
            generated_image_url=image_url,
        )
        await asyncio.to_thread(db.increment_generations, session_token)
    except Exception as exc:
        log.exception("Generation failed for task %s: %s", task_id, exc)
        await asyncio.to_thread(db.update_generation_task, task_id, status="failed")


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit(_GENERATE_RATE_LIMIT)
async def request_generation(
    request: Request,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    session_token: str = Depends(require_session),
):
    # ── Guard: check generation limit ──────────────────────────────────────────
    session = await asyncio.to_thread(db.get_session, session_token)
    used = session["generations_used"]
    if used >= GENERATION_LIMIT:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "generation_limit_reached",
                "message": "You've used all 3 free generations. Sign up to get more.",
                "generations_used": used,
                "generations_remaining": 0,
            },
        )

    # ── Validate job + frame belong to this session ────────────────────────────
    job = await asyncio.to_thread(db.get_job, str(body.job_id))
    if not job or job["session_token"] != session_token:
        raise HTTPException(status_code=403, detail="Invalid job.")

    if not await asyncio.to_thread(db.get_frame, str(body.frame_id)):
        raise HTTPException(status_code=404, detail="Frame not found.")

    # ── Create generation task row, dispatch to worker ────────────────────────
    task_id = await asyncio.to_thread(
        db.create_generation_task, str(body.job_id), str(body.frame_id), session_token
    )

    if _USE_CELERY:
        from tasks.generate import generate_try_on as celery_generate
        celery_generate.delay(task_id, str(body.job_id), str(body.frame_id), session_token)
    else:
        background_tasks.add_task(
            _run_generation_bg, task_id, str(body.job_id), str(body.frame_id), session_token
        )

    return GenerateResponse(
        task_id=UUID(task_id),
        status="queued",
        generations_remaining=GENERATION_LIMIT - used - 1,
    )


@router.get("/generate/{task_id}", response_model=GenerationStatus)
async def get_generation_status(
    task_id: UUID,
    session_token: str = Depends(require_session),
):
    task = await asyncio.to_thread(db.get_generation_task, str(task_id))
    if not task or task["session_token"] != session_token:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task["status"] == "complete":
        image_url = await asyncio.to_thread(storage.get_presigned_url, task["image_r2_key"])
        return GenerationStatus(
            task_id=task_id,
            status="complete",
            image_url=image_url,
            expires_at=task["expires_at"],
        )

    if task["status"] == "failed":
        return GenerationStatus(
            task_id=task_id,
            status="failed",
            error="generation_failed",
            message="Something went wrong. This try has not been counted. Please try again.",
        )

    return GenerationStatus(task_id=task_id, status=task["status"])
