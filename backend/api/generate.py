"""
POST /generate          — queue a try-on generation for one frame.
GET  /generate/{task_id} — poll status + get presigned image URL when done.

Generation limit is server-enforced (never trust the client).
Counter increments atomically only on successful generation.
Failed generations do NOT count against the limit.
"""
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from api.session import require_session, COOKIE_NAME
from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    GenerateLimitError,
    GenerationStatus,
)
from db import supabase as db
from services import generation as gen_svc, storage

router = APIRouter()

GENERATION_LIMIT = 3


@router.post("/generate", response_model=GenerateResponse)
async def request_generation(
    body: GenerateRequest,
    session_token: str = Depends(require_session),
):
    # ── Guard: check generation limit ──────────────────────────────────────────
    session = db.get_session(session_token)
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
    job = db.get_job(str(body.job_id))
    if not job or job["session_token"] != session_token:
        raise HTTPException(status_code=403, detail="Invalid job.")

    frame = db.get_frame(str(body.frame_id))
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found.")

    # ── Create generation task ─────────────────────────────────────────────────
    task_id = db.create_generation_task(
        str(body.job_id), str(body.frame_id), session_token
    )

    # ── Run generation (async) — Sprint 3 will move this to Celery ────────────
    import asyncio
    asyncio.create_task(_run_generation(task_id, str(body.job_id), frame, session_token))

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
    task = db.get_generation_task(str(task_id))
    if not task or task["session_token"] != session_token:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task["status"] == "complete":
        image_url = storage.get_presigned_url(task["image_r2_key"])
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


# ── Internal generation runner ─────────────────────────────────────────────────

async def _run_generation(
    task_id: str,
    job_id: str,
    frame: dict,
    session_token: str,
) -> None:
    """
    Runs the actual fal.ai generation call.
    Only increments the session counter on success.
    """
    db.update_generation_task(task_id, status="processing")
    try:
        r2_key = await gen_svc.generate_try_on(job_id, frame, task_id)
        db.update_generation_task(task_id, status="complete", image_r2_key=r2_key)
        # Atomic increment — only on success
        db.increment_generations(session_token)
    except Exception:
        db.update_generation_task(task_id, status="failed")
