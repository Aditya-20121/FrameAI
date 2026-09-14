"""
POST /upload — validate photo, store in R2, run face analysis, return job_id.

Analysis pipeline:
  1. Basic validation (file size, MIME type)
  2. MediaPipe face detection (validate count, size)
  3. Store photo in R2
  4. Qwen3 VL Flash → face shape + undertone (with geometric fallback)
  5. Write results to jobs table
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File

log = logging.getLogger(__name__)

from api.session import get_or_create_session
from limiter import limiter
from models.schemas import UploadResponse
from services import face_analysis, storage
from db import client as db

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

_ERROR_MESSAGES = {
    "unsupported_format": "The file could not be read as an image.",
    "resolution_too_low": "Photo must be at least 512×512 pixels.",
    "image_too_blurry": "Photo is too blurry. Please take a clearer photo in good lighting.",
    "no_face_detected": "We couldn't find a face. Use a front-facing photo with good lighting.",
    "multiple_faces": "We found more than one face. Please use a solo photo.",
    "face_too_small": "Your face is too small in the frame. Move closer to the camera.",
}


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("5/hour")
async def upload_photo(
    request: Request,
    response: Response,
    photo: UploadFile = File(...),
    session_token: str = Depends(get_or_create_session),
):
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

    # Stage 1: Validate image and face count (fast, local). Also downscales —
    # resized_bytes (not the original, potentially 12MP+ phone photo) is what
    # gets used for the rest of this request to stay within Render's 512MB cap.
    try:
        bgr, resized_bytes = face_analysis.validate_image(image_bytes)
        face_analysis.validate_faces(bgr)
    except ValueError as exc:
        code = str(exc)
        raise HTTPException(
            status_code=400,
            detail={"error": code, "message": _ERROR_MESSAGES.get(code, "Photo validation failed.")},
        )

    # Create job + store the ORIGINAL full-resolution photo (R2 storage, no decode needed)
    job_id = db.create_job(session_token, photo_r2_key="pending")
    r2_key = storage.upload_photo(job_id, image_bytes, photo.content_type or "image/jpeg")
    db.update_job_r2_key(job_id, r2_key)

    # Stage 2: Full analysis (Qwen3 VL Flash) — runs on the downscaled copy
    try:
        result = await face_analysis.run_face_analysis(resized_bytes, distinct_id=session_token)
        db.update_job_analysis(
            job_id,
            face_shape=result.face_shape,
            face_shape_conf=result.face_shape_confidence,
            undertone=result.undertone,
            undertone_conf=result.undertone_confidence,
            undertone_hex=result.undertone_hex,
            ipd_mm=result.ipd_mm,
            size_band=result.size_band,
            face_features={
                "jawline": result.jawline,
                "cheekbones": result.cheekbones,
                "eye_set": result.eye_set,
                "skin_depth": result.skin_depth,
                "face_shape_explanation": result.face_shape_explanation,
                "face_shape_label": result.face_shape_label,
            },
        )
    except Exception:
        import traceback; traceback.print_exc()
        log.exception("Face analysis failed for job %s", job_id)
        db.fail_job(job_id)
        raise HTTPException(
            status_code=500,
            detail={"error": "analysis_failed", "message": "Face analysis failed. Please try again."},
        )

    return UploadResponse(job_id=UUID(job_id), session_token=session_token)
