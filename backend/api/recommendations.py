"""
GET /recommendations/{job_id} — return top 10 ranked frame recommendations.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.session import require_session
from models.schemas import RecommendationsResponse, FrameRecommendation
from services.recommender import FACE_SHAPE_RULES, rank_frames
from db import client as db
from services.storage import presign_frame_url

router = APIRouter()


@router.get("/recommendations/{job_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    job_id: UUID,
    session_token: str = Depends(require_session),
):
    job = db.get_job(str(job_id))

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["session_token"] != session_token:
        raise HTTPException(status_code=403, detail="Access denied.")
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail="Analysis not complete yet.")

    face_shape: str = job["face_shape"]
    undertone: str  = job["undertone"]
    ipd_mm: float   = job["ipd_mm"] or 63.0

    # Pull extra features from face_features JSONB (may be None for older jobs)
    ff = job.get("face_features") or {}
    if isinstance(ff, str):
        import json as _json
        ff = _json.loads(ff)

    skin_depth: str | None = ff.get("skin_depth")
    jawline:    str | None = ff.get("jawline")
    cheekbones: str | None = ff.get("cheekbones")
    eye_set:    str | None = ff.get("eye_set")

    shape_rules = FACE_SHAPE_RULES[face_shape]

    # Broad candidate pool filtered by face-shape styles only.
    # Colour scoring + all other signals applied in Python below.
    raw_frames = db.query_frames(
        best_styles=shape_rules["best_styles"],
    )

    ranked = rank_frames(
        raw_frames,
        face_shape=face_shape,
        undertone=undertone,
        ipd_mm=ipd_mm,
        skin_depth=skin_depth,
        jawline=jawline,
        cheekbones=cheekbones,
        eye_set=eye_set,
        top_n=10,
    )

    recommendations = [
        FrameRecommendation(
            frame_id=f["frame_id"],
            rank=i + 1,
            name=f["name"],
            style=f["style"],
            colour=f["colour"],
            colour_hex=f.get("colour_hex"),
            material=f.get("material"),
            retailer=f["retailer"],
            price_inr=f.get("price_inr"),
            buy_url=f["buy_url"],
            product_image_url=presign_frame_url(f["product_image_url"]),
            vibe_tags=f.get("vibe_tags") or [],
            score=f["score"],
            explanation=f["explanation"],
        )
        for i, f in enumerate(ranked)
    ]

    return RecommendationsResponse(
        job_id=job_id,
        total=len(recommendations),
        frames=recommendations,
    )
