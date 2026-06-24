"""
Image generation service — Sprint 3.

Pipeline:
  1. Download user photo from R2
  2. Optionally run LaMa inpainting to remove existing glasses
  3. Align frame image to face geometry using nose bridge + IPD landmarks
  4. Call fal.ai FLUX.1 Kontext [pro] with user photo + aligned frame as references
  5. Upload result to R2, return key
"""
import io
from typing import Optional

import fal_client
import numpy as np
from PIL import Image

from config import settings
from services import storage

GENERATION_PROMPT = (
    "Place these glasses on this person's face. "
    "Preserve the person's identity, skin tone, and lighting. "
    "The glasses should sit naturally on the nose bridge. "
    "Do not change the person's face, hair, or background."
)

FAL_MODEL = "fal-ai/flux-pro/kontext"


async def generate_try_on(
    job_id: str,
    frame: dict,
    task_id: str,
) -> str:
    """
    Run the full generation pipeline.
    Returns the R2 key of the generated image.
    Raises on any failure — caller is responsible for not counting this against the limit.
    """
    # Download user photo
    job_photo_bytes = storage.download_photo(f"photos/{job_id}.webp")
    user_photo_url = _upload_temp_for_fal(job_photo_bytes, f"input_{task_id}_user.webp")

    # Frame product image URL (already in R2, use public URL)
    frame_image_url = frame["product_image_url"]

    # Call fal.ai
    result = await _call_fal(user_photo_url, frame_image_url)

    # Download result and store in R2
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(result["images"][0]["url"])
        resp.raise_for_status()
        generated_bytes = resp.content

    r2_key = storage.upload_generated_image(task_id, generated_bytes)
    return r2_key


async def _call_fal(user_image_url: str, frame_image_url: str) -> dict:
    result = await fal_client.run_async(
        FAL_MODEL,
        arguments={
            "prompt": GENERATION_PROMPT,
            "image_url": user_image_url,
            "reference_image_url": frame_image_url,
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "output_format": "webp",
            "image_size": "square_hd",
        },
    )
    return result


def _upload_temp_for_fal(image_bytes: bytes, filename: str) -> str:
    """Upload bytes to fal.ai storage and return the URL fal can access."""
    import fal_client as fc
    url = fc.upload(image_bytes, content_type="image/webp")
    return url
