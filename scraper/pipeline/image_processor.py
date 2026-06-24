"""
Image processing pipeline.

For each product image URL:
  1. Download the image
  2. Reject if a human face is present (useless for frame compositing)
  3. Auto-crop to the glasses bounding box
  4. Pad to a square with white background
  5. Resize to 512×512
  6. Save as WebP

Output: normalised 512×512 WebP at output/images/normalised/{source_id}.webp
"""
import asyncio
import io
import logging
from pathlib import Path

import cv2
import httpx
import numpy as np
from PIL import Image, ImageOps

log = logging.getLogger(__name__)

TARGET_SIZE = 512
FACE_SCALE_FACTOR = 1.1
FACE_MIN_NEIGHBOURS = 5

# Haar cascade for fast face detection (no GPU needed)
_FACE_CASCADE: cv2.CascadeClassifier | None = None


def _get_face_cascade() -> cv2.CascadeClassifier:
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
    return _FACE_CASCADE


def has_human_face(pil_image: Image.Image) -> bool:
    """Return True if a human face is detected in the image."""
    bgr = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    cascade = _get_face_cascade()
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=FACE_SCALE_FACTOR,
        minNeighbors=FACE_MIN_NEIGHBOURS,
        minSize=(30, 30),
    )
    return len(faces) > 0


def autocrop_to_glasses(pil_image: Image.Image, padding_frac: float = 0.08) -> Image.Image:
    """
    Crop tightly to the non-white content (the glasses), then add padding.
    Works on both RGBA (transparent background) and RGB (white background) images.
    """
    if pil_image.mode == "RGBA":
        # Use alpha channel as mask
        alpha = np.array(pil_image.split()[3])
        mask = alpha > 10
    else:
        # Use colour distance from white as mask
        rgb = np.array(pil_image.convert("RGB"))
        white = np.array([255, 255, 255])
        dist = np.linalg.norm(rgb.astype(int) - white, axis=2)
        mask = dist > 20

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any() or not cols.any():
        return pil_image  # nothing to crop

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    h, w = mask.shape
    pad_r = int((rmax - rmin) * padding_frac)
    pad_c = int((cmax - cmin) * padding_frac)

    rmin = max(0, rmin - pad_r)
    rmax = min(h - 1, rmax + pad_r)
    cmin = max(0, cmin - pad_c)
    cmax = min(w - 1, cmax + pad_c)

    return pil_image.crop((cmin, rmin, cmax + 1, rmax + 1))


def pad_to_square(pil_image: Image.Image, fill: tuple = (255, 255, 255)) -> Image.Image:
    """Pad image to square with a white (or specified) background, centred."""
    w, h = pil_image.size
    side = max(w, h)
    background = Image.new("RGB", (side, side), fill)
    offset = ((side - w) // 2, (side - h) // 2)
    if pil_image.mode == "RGBA":
        background.paste(pil_image, offset, mask=pil_image.split()[3])
    else:
        background.paste(pil_image, offset)
    return background


def normalise_image(raw_bytes: bytes) -> bytes | None:
    """
    Full normalisation pipeline for one product image.
    Returns WebP bytes on success, None if the image should be rejected.
    """
    try:
        pil = Image.open(io.BytesIO(raw_bytes))
    except Exception as exc:
        log.debug("Could not open image: %s", exc)
        return None

    # Reject if resolution is very small (likely a placeholder)
    if pil.width < 100 or pil.height < 100:
        log.debug("Image too small (%dx%d) — skipped", pil.width, pil.height)
        return None

    # Reject if a human face is present
    if has_human_face(pil):
        log.debug("Human face detected — image rejected")
        return None

    # Crop, pad, resize
    pil = autocrop_to_glasses(pil)
    pil = pad_to_square(pil)
    pil = pil.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)

    # Convert to RGB (drop alpha if present)
    pil = pil.convert("RGB")

    # Encode as WebP
    buf = io.BytesIO()
    pil.save(buf, format="WebP", quality=90)
    return buf.getvalue()


async def download_and_process(
    session_id: str,
    image_url: str,
    client: httpx.AsyncClient,
    raw_dir: Path,
    norm_dir: Path,
) -> str | None:
    """
    Download, process, and save one product image.
    Returns the path to the normalised file, or None on failure/rejection.
    """
    norm_path = norm_dir / f"{session_id}.webp"
    if norm_path.exists():
        return str(norm_path)

    try:
        resp = await client.get(image_url, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        raw_bytes = resp.content
    except Exception as exc:
        log.warning("Image download failed for %s: %s", session_id, exc)
        return None

    # Save raw
    raw_path = raw_dir / f"{session_id}.jpg"
    raw_path.write_bytes(raw_bytes)

    # Normalise
    normalised = normalise_image(raw_bytes)
    if normalised is None:
        log.debug("Image rejected: %s", session_id)
        return None

    norm_path.write_bytes(normalised)
    return str(norm_path)


async def process_batch(
    products: list[dict],
    raw_dir: Path,
    norm_dir: Path,
    concurrency: int = 5,
) -> dict[str, str]:
    """
    Process images for a batch of products concurrently.
    Returns {source_id: norm_image_path} for accepted images.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, str] = {}

    async def _one(product: dict) -> None:
        url = product.get("image_url")
        sid = product["source_id"]
        if not url:
            return
        async with semaphore:
            path = await download_and_process(sid, url, client, raw_dir, norm_dir)
            if path:
                results[sid] = path

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[_one(p) for p in products])

    return results
