"""
Sprint 3 — Live end-to-end generation test (Segmind Nano Banana v1).

Tests the full pipeline directly (no HTTP server or Celery needed):
  selfie → R2 presigned URL + frame presigned URL → Nano Banana v1 → saved portrait

Usage:
    cd backend
    D:\\Python311\\python.exe test_e2e.py --photo path/to/selfie.jpg
"""
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path(__file__).parent / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)


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
    print("✓  Config OK (Segmind + Supabase + R2)")


def _upload_test_photo(photo_path: Path) -> str:
    """Upload the test selfie to R2 under a fixed test job_id, return the key."""
    from services import storage
    from PIL import Image
    import io

    img = Image.open(photo_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=92)
    key = storage.upload_photo("test-e2e-job", buf.getvalue(), "image/webp")
    print(f"✓  Photo uploaded → R2:{key}")
    return key


def _pick_frame() -> dict:
    """Pick a frame whose image is already in R2 (guaranteed downloadable)."""
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
    frames = result.data
    if not frames:
        print("✗  No R2-hosted frames found.")
        print("   Run: cd scraper && python run.py download-images && python run.py load --limit 409")
        sys.exit(1)
    frame = frames[0]
    print(f"✓  Frame  : [{frame['style']}] {frame['name']} ({frame['retailer']})")
    print(f"   Colour : {frame.get('colour') or '—'}")
    print(f"   Image  : {frame['product_image_url'][:70]}")
    return frame


async def _run(photo_path: Path, frame: dict) -> Path:
    from services.generation import (
        _call_segmind, _frame_presigned_url, build_generation_prompt, SEGMIND_ENDPOINT
    )
    from services import storage

    # ── Step 1: Upload test photo to R2, get presigned URL ────────────────────
    print(f"\n── Step 1: Upload photo → R2 ────────────────────────────────────────")
    _upload_test_photo(photo_path)
    person_url = storage.get_presigned_url("photos/test-e2e-job.webp")
    print(f"   Presigned URL generated")

    # ── Step 2: Get presigned URL for frame image ─────────────────────────────
    print(f"\n── Step 2: Frame image URL ──────────────────────────────────────────")
    frame_url = _frame_presigned_url(frame["product_image_url"])
    print(f"   Presigned URL generated")

    # ── Step 3: Call Nano Banana v1 ───────────────────────────────────────────
    prompt = build_generation_prompt(frame)
    print(f"\n── Step 3: Segmind Nano Banana v1 (~15–20s) ─────────────────────────")
    print(f"   Endpoint : {SEGMIND_ENDPOINT}")
    print(f"   Prompt   : {prompt}")
    t0 = time.time()
    portrait_bytes = await _call_segmind(person_url, frame_url, prompt)
    print(f"   Response : {len(portrait_bytes) // 1024} KB")
    print(f"   Time     : {time.time() - t0:.1f}s")

    # ── Save result ────────────────────────────────────────────────────────────
    portrait_path = OUTPUT_DIR / "result_portrait.webp"
    portrait_path.write_bytes(portrait_bytes)
    print(f"   Saved    : {portrait_path}")

    return portrait_path


async def main(photo_path: Path) -> None:
    print("=" * 60)
    print("  FrameAI — Sprint 3 E2E Test  (Nano Banana v1)")
    print("=" * 60)

    _check_config()
    frame = _pick_frame()
    result_path = await _run(photo_path, frame)

    print(f"\n{'='*60}")
    print(f"  ✓  Done!")
    print(f"  Frame  : {frame['name']}")
    print(f"  Style  : {frame['style']}   Colour: {frame.get('colour')}")
    print(f"  Result : {result_path}")
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
    parser.add_argument("--photo", required=True, help="Path to a frontal face photo (no glasses)")
    args = parser.parse_args()

    photo_path = Path(args.photo)
    if not photo_path.exists():
        print(f"✗  Not found: {photo_path}")
        sys.exit(1)

    asyncio.run(main(photo_path))
