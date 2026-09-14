"""
Image generation service.

Model: Segmind Nano Banana 2 Lite
  https://www.segmind.com/models/nano-banana-2-lite/api

Pipeline:
  1. Get presigned URL for user photo (already in R2)
  2. Get presigned URL for frame product image (already in R2)
  3. POST both URLs to Nano Banana 2 Lite via image_urls[]
  4. Convert response to WEBP, upload to R2, return key
"""
import base64
import io
import time

import httpx
import structlog
from PIL import Image

from config import settings
from services import storage, analytics

log = structlog.get_logger(__name__)

SEGMIND_ENDPOINT = "https://api.segmind.com/v1/nano-banana-2-lite"


def build_generation_prompt(frame: dict) -> str:
    colour = (frame.get("colour") or "").strip().lower()
    style  = (frame.get("style")  or "rectangular").strip().lower()
    desc   = f"{colour} {style}" if colour else style
    return (
        f"Generate an image of the person from image 1 wearing the {desc} eyeglasses "
        f"exactly as shown in image 2. "
        f"The glasses should have the same frame colour, material, lens tint, rim thickness, "
        f"bridge shape, and temple design as shown in image 2. "
        f"Do not change the frame colour or style. "
        f"The person's face, hair, skin tone, eye colour, expression, "
        f"clothing, and background are completely unchanged from image 1."
    )


async def generate_try_on(job_id: str, frame: dict, task_id: str, distinct_id: str = "unknown") -> str:
    """
    Full generation pipeline.
    Returns the R2 key of the generated portrait.
    Raises on any failure — caller must NOT count failures against the generation limit.
    """
    photo_url = storage.get_presigned_url(f"photos/{job_id}.webp")
    frame_url = _frame_presigned_url(frame["product_image_url"])
    prompt    = build_generation_prompt(frame)

    start = time.perf_counter()
    try:
        portrait_bytes = await _call_segmind(photo_url, frame_url, prompt)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        log.error("generation_call_failed", task_id=task_id, duration_ms=duration_ms)
        await analytics.capture(distinct_id, "generation_failed", {"task_id": task_id, "duration_ms": duration_ms})
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    log.info("generation_call_completed", task_id=task_id, duration_ms=duration_ms, cost_usd=analytics.COST_GENERATION_USD)
    await analytics.capture(
        distinct_id,
        "generation_completed",
        {"task_id": task_id, "duration_ms": duration_ms, "cost_usd": analytics.COST_GENERATION_USD},
    )
    return storage.upload_generated_image(task_id, portrait_bytes)


def _frame_presigned_url(frame_image_url: str) -> str:
    r2_key = storage.r2_key_from_url(frame_image_url)
    if r2_key:
        return storage.get_presigned_url(r2_key)
    return frame_image_url


async def _call_segmind(person_url: str, frame_url: str, prompt: str) -> bytes:
    """
    POST to Segmind Nano Banana v1.
    Returns portrait as WEBP bytes.
    """
    payload = {
        "prompt":              prompt,
        "image_urls":          [person_url, frame_url],
        "aspect_ratio":        "3:4",
        "response_modalities": "IMAGE",
        "output_format":       "jpg",
        "thinking_level":      "minimal",  # faster for real-time try-on; "high" adds latency
    }
    headers = {
        "x-api-key":    settings.segmind_api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(SEGMIND_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "image" in content_type:
        raw_bytes = resp.content
    else:
        data = resp.json()
        img_b64 = data.get("image") or data.get("output") or data.get("data")
        if not img_b64:
            raise ValueError(f"Unexpected Segmind response keys: {list(data.keys())}")
        raw_bytes = base64.b64decode(img_b64)

    return _to_webp(raw_bytes)


def _to_webp(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=90)
    return buf.getvalue()
