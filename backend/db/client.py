"""
Supabase client wrapper — all DB operations go through these functions.
Uses the service role key so calls are not subject to row-level security.
"""
import secrets
from uuid import UUID
from datetime import datetime, timezone, timedelta

from supabase import create_client, Client
from config import settings


def _client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session() -> str:
    """Create a new anonymous session, return the token."""
    token = secrets.token_urlsafe(32)
    _client().table("sessions").insert({
        "token": token,
        "generations_used": 0,
    }).execute()
    return token


def get_session(token: str) -> dict | None:
    result = (
        _client()
        .table("sessions")
        .select("*")
        .eq("token", token)
        .single()
        .execute()
    )
    return result.data


def touch_session(token: str) -> None:
    _client().table("sessions").update({
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }).eq("token", token).execute()


def increment_generations(token: str) -> int:
    """Atomically increment generations_used. Returns new value."""
    result = _client().rpc(
        "increment_generations",
        {"session_token": token},
    ).execute()
    return result.data


# ── Jobs ──────────────────────────────────────────────────────────────────────

def create_job(session_token: str, photo_r2_key: str) -> str:
    """Create a job record, return job_id as string."""
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    result = (
        _client()
        .table("jobs")
        .insert({
            "session_token": session_token,
            "photo_r2_key": photo_r2_key,
            "status": "processing",
            "expires_at": expires_at,
        })
        .execute()
    )
    return result.data[0]["job_id"]


def update_job_r2_key(job_id: str, r2_key: str) -> None:
    _client().table("jobs").update({"photo_r2_key": r2_key}).eq("job_id", job_id).execute()


def update_job_analysis(
    job_id: str,
    *,
    face_shape: str,
    face_shape_conf: float,
    undertone: str,
    undertone_conf: float,
    undertone_hex: str,
    ipd_mm: float,
    size_band: str,
    face_features: dict | None = None,
) -> None:
    payload: dict = {
        "face_shape": face_shape,
        "face_shape_conf": face_shape_conf,
        "undertone": undertone,
        "undertone_conf": undertone_conf,
        "undertone_hex": undertone_hex,
        "ipd_mm": ipd_mm,
        "size_band": size_band,
        "status": "complete",
    }
    if face_features is not None:
        payload["face_features"] = face_features  # JSONB — pass dict directly
    _client().table("jobs").update(payload).eq("job_id", job_id).execute()


def fail_job(job_id: str, reason: str = "analysis_failed") -> None:
    _client().table("jobs").update({
        "status": reason,
    }).eq("job_id", job_id).execute()


def get_job(job_id: str) -> dict | None:
    result = (
        _client()
        .table("jobs")
        .select("*")
        .eq("job_id", job_id)
        .single()
        .execute()
    )
    return result.data


# ── Generation tasks ───────────────────────────────────────────────────────────

def create_generation_task(
    job_id: str,
    frame_id: str,
    session_token: str,
) -> str:
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    result = (
        _client()
        .table("generation_tasks")
        .insert({
            "job_id": job_id,
            "frame_id": frame_id,
            "session_token": session_token,
            "status": "queued",
            "expires_at": expires_at,
        })
        .execute()
    )
    return result.data[0]["task_id"]


def update_generation_task(
    task_id: str,
    *,
    status: str,
    image_r2_key: str | None = None,
    fal_request_id: str | None = None,
) -> None:
    payload: dict = {"status": status}
    if image_r2_key:
        payload["image_r2_key"] = image_r2_key
    if fal_request_id:
        payload["fal_request_id"] = fal_request_id
    if status == "complete":
        payload["completed_at"] = datetime.now(timezone.utc).isoformat()
    _client().table("generation_tasks").update(payload).eq("task_id", task_id).execute()


def get_generation_task(task_id: str) -> dict | None:
    result = (
        _client()
        .table("generation_tasks")
        .select("*")
        .eq("task_id", task_id)
        .single()
        .execute()
    )
    return result.data


# ── Frames ────────────────────────────────────────────────────────────────────

def get_frame(frame_id: str) -> dict | None:
    result = (
        _client()
        .table("frames")
        .select("*")
        .eq("frame_id", frame_id)
        .single()
        .execute()
    )
    return result.data


def query_frames(
    best_styles: list[str],
    limit: int = 500,
) -> list[dict]:
    """
    Pull all candidate frames matching the face-shape style list.
    Colour scoring and all other signals are applied in Python (recommender.py).
    500 limit safely covers our full catalogue (~358 frames).
    """
    result = (
        _client()
        .table("frames")
        .select("*")
        .in_("style", best_styles)
        .not_.is_("product_image_url", "null")
        .limit(limit)
        .execute()
    )
    return result.data or []


def browse_frames(
    style: str | None = None,
    retailer: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    q = (
        _client()
        .table("frames")
        .select("frame_id,name,style,colour,colour_hex,material,retailer,price_inr,buy_url,product_image_url,vibe_tags")
        .not_.is_("product_image_url", "null")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if style:
        q = q.eq("style", style)
    if retailer:
        q = q.eq("retailer", retailer)
    return q.execute().data or []


def get_distinct_styles() -> list[str]:
    result = (
        _client()
        .table("frames")
        .select("style")
        .not_.is_("style", "null")
        .execute()
    )
    return sorted({row["style"] for row in (result.data or []) if row.get("style")})
