"""
GET /catalogue — public endpoint to browse the frame catalogue.
No session required.  Used by the home page.
"""
from fastapi import APIRouter, Query

from db import client as db
from services.storage import presign_frame_url

router = APIRouter(prefix="/catalogue", tags=["catalogue"])

VALID_STYLES = {
    "round", "square", "oval", "rectangular", "cat-eye", "aviator",
    "wayfarer", "browline", "geometric", "rimless",
}


@router.get("")
async def browse_catalogue(
    style:    str | None = Query(None, description="Filter by frame style"),
    retailer: str | None = Query(None, description="Filter by retailer name"),
    limit:    int        = Query(20,   ge=1, le=50),
    offset:   int        = Query(0,    ge=0),
):
    frames = db.browse_frames(
        style=style if style in VALID_STYLES else None,
        retailer=retailer,
        limit=limit,
        offset=offset,
    )
    for f in frames:
        f["product_image_url"] = presign_frame_url(f["product_image_url"])
    return {"frames": frames, "limit": limit, "offset": offset, "total": len(frames)}


@router.get("/styles")
async def list_styles():
    """Return all distinct frame styles in the catalogue."""
    styles = db.get_distinct_styles()
    return {"styles": styles}
