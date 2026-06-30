"""
Sprint 3 — E2E test for Segmind Multi Image Kontext Pro.

Uses native two-image input (no composite workaround):
  input_image_1 = person's face (R2 presigned URL)
  input_image_2 = frame product photo (R2 presigned URL)

Compare output quality against the default P-Image-Edit pipeline (test_e2e.py).

Usage:
    cd backend
    D:\\Python311\\python.exe test_e2e_kontext.py --photo path/to/selfie.jpg
"""
import argparse
import asyncio
import io
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path(__file__).parent / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)

ENDPOINT = "https://api.segmind.com/v1/multi-image-kontext-pro"


def _build_prompt(frame: dict) -> str:
    colour = (frame.get("colour") or "").strip().lower()
    style  = (frame.get("style")  or "rectangular").strip().lower()
    desc   = f"{colour} {style}" if colour else style
    return f"Portrait photo of a person wearing {desc} eyeglasses with clear lenses as shown in image 2."


def _check_config() -> None:
    from config import settings
    missing = []
    if not settings.segmind_api_key:
        missing.append("SEGMIND_API_KEY")
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.r2_access_key_id:
        missing.append("R2_ACCESS_KEY_ID")
    if missing:
        print(f"✗  Missing env vars: {', '.join(missing)}")
        sys.exit(1)
    print("✓  Config OK")


def _upload_test_photo(photo_path: Path) -> None:
    from services import storage
    from PIL import Image
    img = Image.open(photo_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=92)
    storage.upload_photo("test-e2e-job", buf.getvalue(), "image/webp")
    print(f"✓  Photo uploaded → R2:photos/test-e2e-job.webp")


def _pick_frame() -> dict:
    from supabase import create_client
    from config import settings
    client = create_client(settings.supabase_url, settings.supabase_service_key)
    result = (
        client.table("frames")
        .select("*")
        .like("product_image_url", f"%{settings.r2_public_domain}%")
        .not_.is_("style", "null")
        .limit(1)
        .execute()
    )
    if not result.data:
        print("✗  No R2-hosted frames found.")
        sys.exit(1)
    frame = result.data[0]
    print(f"✓  Frame  : [{frame['style']}] {frame['name']} ({frame['retailer']})")
    print(f"   Colour : {frame.get('colour') or '—'}")
    return frame


async def _run(photo_path: Path, frame: dict) -> Path:
    import httpx
    import base64
    from services import storage
    from config import settings

    # ── Step 1: Get presigned URLs ────────────────────────────────────────────
    print(f"\n── Step 1: Presigned URLs ───────────────────────────────────────────")
    _upload_test_photo(photo_path)
    person_url = storage.get_presigned_url("photos/test-e2e-job.webp")

    r2_key = storage.r2_key_from_url(frame["product_image_url"])
    frame_url = storage.get_presigned_url(r2_key) if r2_key else frame["product_image_url"]
    print(f"   person_url : generated")
    print(f"   frame_url  : generated")

    # ── Step 2: Call Multi Image Kontext Pro ──────────────────────────────────
    prompt = _build_prompt(frame)
    print(f"\n── Step 2: Multi Image Kontext Pro ──────────────────────────────────")
    print(f"   Endpoint : {ENDPOINT}")
    print(f"   Prompt   : {prompt}")

    payload = {
        "prompt":           prompt,
        "input_image_1":    person_url,
        "input_image_2":    frame_url,
        "aspect_ratio":     "3:4",
        "output_format":    "jpg",
        "safety_tolerance": 2,
        "seed":             42,
    }
    headers = {
        "x-api-key":    settings.segmind_api_key,
        "Content-Type": "application/json",
    }

    t0 = time.time()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()

    print(f"   Time     : {time.time() - t0:.1f}s")
    print(f"   Response : {len(resp.content) // 1024} KB  ({resp.headers.get('content-type')})")

    # Extract image bytes
    content_type = resp.headers.get("content-type", "")
    if "image" in content_type:
        portrait_bytes = resp.content
    else:
        data = resp.json()
        img_b64 = data.get("image") or data.get("output") or data.get("data")
        if not img_b64:
            raise ValueError(f"Unexpected response keys: {list(data.keys())}\n{data}")
        portrait_bytes = base64.b64decode(img_b64)

    portrait_path = OUTPUT_DIR / "result_kontext.jpg"
    portrait_path.write_bytes(portrait_bytes)
    print(f"   Saved    : {portrait_path}")
    return portrait_path


async def main(photo_path: Path) -> None:
    print("=" * 60)
    print("  FrameAI — Multi Image Kontext Pro Test")
    print("=" * 60)

    _check_config()
    frame = _pick_frame()
    result_path = await _run(photo_path, frame)

    print(f"\n{'='*60}")
    print(f"  ✓  Done!  →  {result_path}")
    print(f"{'='*60}\n")

    import subprocess, platform
    if platform.system() == "Windows":
        os.startfile(str(result_path))
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(result_path)])
    else:
        subprocess.Popen(["xdg-open", str(result_path)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True)
    args = parser.parse_args()
    photo_path = Path(args.photo)
    if not photo_path.exists():
        print(f"✗  Not found: {photo_path}")
        sys.exit(1)
    asyncio.run(main(photo_path))
