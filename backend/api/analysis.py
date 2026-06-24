"""
GET /analysis/{job_id}   — return face shape, undertone, IPD for a completed job.
GET /session             — return generation usage for the current session.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.session import require_session
from models.schemas import AnalysisResult, SessionStatus
from db import supabase as db

router = APIRouter()


@router.get("/analysis/{job_id}", response_model=AnalysisResult)
async def get_analysis(
    job_id: UUID,
    session_token: str = Depends(require_session),
):
    job = db.get_job(str(job_id))

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["session_token"] != session_token:
        raise HTTPException(status_code=403, detail="Access denied.")

    if job["status"] == "processing":
        return AnalysisResult(job_id=job_id, status="processing")

    if job["status"] not in ("complete",):
        return AnalysisResult(job_id=job_id, status="failed")

    return AnalysisResult(
        job_id=job_id,
        status="complete",
        face_shape=job["face_shape"],
        face_shape_confidence=job["face_shape_conf"],
        face_shape_explanation=_shape_explanation(job["face_shape"]),
        undertone=job["undertone"],
        undertone_confidence=job["undertone_conf"],
        undertone_hex=job["undertone_hex"],
        ipd_mm=job["ipd_mm"],
        size_band=job["size_band"],
    )


@router.get("/session", response_model=SessionStatus)
async def get_session_status(
    session_token: str = Depends(require_session),
):
    session = db.get_session(session_token)
    used = session["generations_used"]
    return SessionStatus(
        generations_used=used,
        generations_remaining=max(0, 3 - used),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

from services.face_analysis import FACE_SHAPE_EXPLANATIONS


def _shape_explanation(shape: str | None) -> str | None:
    if not shape:
        return None
    return FACE_SHAPE_EXPLANATIONS.get(shape)
