"""
POST /upload — validate photo, store in R2, kick off face analysis, return job_id.

The face analysis runs synchronously within the request for now (< 3s on CPU).
Sprint 3 will move heavy work to a Celery task.
"""
import io
import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File

from api.session import get_or_create_session
from models.schemas import UploadResponse
from services import face_analysis, undertone, storage
from db import supabase as db

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/upload", response_model=UploadResponse)
async def upload_photo(
    response: Response,
    photo: UploadFile = File(...),
    session_token: str = Depends(get_or_create_session),
):
    # ── Basic validation ───────────────────────────────────────────────────────
    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail={"error": "unsupported_format", "message": "Only JPG, PNG, and WEBP are accepted."},
        )

    image_bytes = await photo.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail={"error": "file_too_large", "message": "Photo must be under 10 MB."},
        )

    # ── Image + face validation ────────────────────────────────────────────────
    try:
        bgr = face_analysis.validate_image(image_bytes)
        face_analysis.validate_faces(bgr)
    except ValueError as exc:
        error_code = str(exc)
        _MESSAGES = {
            "unsupported_format": "The file could not be read as an image.",
            "resolution_too_low": "Photo must be at least 512×512 pixels.",
            "image_too_blurry": "Photo is too blurry. Please take a sharper photo in good light.",
            "no_face_detected": "We couldn't find a face in this photo. Use a front-facing photo with good lighting.",
            "multiple_faces": "We found more than one face. Please use a solo photo.",
            "face_too_small": "Your face is too small in the frame. Move closer to the camera.",
        }
        raise HTTPException(
            status_code=400,
            detail={
                "error": error_code,
                "message": _MESSAGES.get(error_code, "Photo validation failed."),
            },
        )

    # ── Store photo in R2 ──────────────────────────────────────────────────────
    job_id = db.create_job(session_token, photo_r2_key="pending")
    r2_key = storage.upload_photo(job_id, image_bytes, photo.content_type or "image/jpeg")
    # Update key now that we have it (job was pre-created for the UUID)
    db._client().table("jobs").update({"photo_r2_key": r2_key}).eq("job_id", job_id).execute()

    # ── Run analysis pipeline (sync, ~2s on CPU) ───────────────────────────────
    try:
        h, w = bgr.shape[:2]
        landmarks = face_analysis.extract_landmarks(bgr)
        geometry = face_analysis.compute_geometry(landmarks, w, h)
        shape_result = face_analysis.classify_face_shape(geometry)
        ipd_mm = face_analysis.compute_ipd_mm(geometry)
        size_band = face_analysis.get_size_band(ipd_mm)
        tone_result = undertone.analyze_undertone(bgr, landmarks)

        db.update_job_analysis(
            job_id,
            face_shape=shape_result.shape,
            face_shape_conf=shape_result.confidence,
            undertone=tone_result.undertone,
            undertone_conf=tone_result.confidence,
            undertone_hex=tone_result.hex_color,
            ipd_mm=ipd_mm,
            size_band=size_band,
        )
    except Exception:
        db.fail_job(job_id)
        raise HTTPException(
            status_code=500,
            detail={"error": "analysis_failed", "message": "Face analysis failed. Please try again."},
        )

    return UploadResponse(job_id=UUID(job_id))
