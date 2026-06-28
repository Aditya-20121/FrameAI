"""
GET /recommendations/{job_id} — return top 10 ranked frame recommendations.
Sprint 2: requires seed catalogue in Supabase frames table.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.session import require_session
from models.schemas import RecommendationsResponse, FrameRecommendation
from services.recommender import (
    rank_frames,
    FACE_SHAPE_RULES,
    UNDERTONE_RULES,
    IPD_SIZE_RULES,
    get_size_band,
)
from db import client as db

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
    tone: str = job["undertone"]
    ipd_mm: float = job["ipd_mm"] or 63.0

    shape_rules = FACE_SHAPE_RULES[face_shape]
    colour_rules = UNDERTONE_RULES[tone]
    size_band = get_size_band(ipd_mm)
    min_w, max_w = IPD_SIZE_RULES[size_band]["frame_width_mm"]

    raw_frames = db.query_frames(
        best_styles=shape_rules["best_styles"],
        best_colours=colour_rules["best_colours"],
        boost_styles=shape_rules["score_boost"],
        min_width=min_w - 10,   # ±10mm tolerance so we always get results
        max_width=max_w + 10,
        limit=30,
    )

    ranked = rank_frames(raw_frames, face_shape, tone, ipd_mm, top_n=10)

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
            product_image_url=f["product_image_url"],
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
