"""
Sprint 3 — Nano Banana comparison test (v1 + v2).

Runs both Nano Banana models and saves named outputs so you can compare
side-by-side against P-Image-Edit (result_portrait.webp) and
Multi Image Kontext (result_kontext.jpg).

Outputs:
  test_output/result_nanobanana.jpg    — Nano Banana v1  ($0.04)
  test_output/result_nanobanana2.jpg   — Nano Banana 2   ($0.06 at 512px)

Usage:
    cd backend
    D:\\Python311\\python.exe test_e2e_nanobanana.py --photo path/to/selfie.jpg
    D:\\Python311\\python.exe test_e2e_nanobanana.py --photo path/to/selfie.jpg --model v2
    D:\\Python311\\python.exe test_e2e_nanobanana.py --photo path/to/selfie.jpg --model both
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

ENDPOINT_V1 = "https://api.segmind.com/v1/nano-banana"
ENDPOINT_V2 = "https://api.segmind.com/v1/nano-banana-2"


def _build_prompt(frame: dict) -> str:
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


async def _call_model(
    endpoint: str,
    payload: dict,
    label: str,
    out_path: Path,
) -> None:
    import httpx
    from config import settings

    headers = {
        "x-api-key":    settings.segmind_api_key,
        "Content-Type": "application/json",
    }

    print(f"\n── {label} ──────────────────────────────────────────────────────────")
    print(f"   Endpoint : {endpoint}")
    print(f"   Prompt   : {payload['prompt'][:120]}...")

    t0 = time.time()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(endpoint, json=payload, headers=headers)
        resp.raise_for_status()

    elapsed = time.time() - t0
    content_type = resp.headers.get("content-type", "")
    inference_ms = "?"
    if "image" in content_type:
        image_bytes = resp.content
    else:
        data = resp.json()
        inference_ms = data.get("metrics", {}).get("inference_time", "?")
        output_url = data.get("output") or data.get("image") or data.get("data")
        if not output_url:
            raise ValueError(f"Unexpected response keys: {list(data.keys())}\n{data}")
        if output_url.startswith("http"):
            async with httpx.AsyncClient(timeout=30) as client:
                img_resp = await client.get(output_url)
                img_resp.raise_for_status()
                image_bytes = img_resp.content
        else:
            import base64
            image_bytes = base64.b64decode(output_url)

    out_path.write_bytes(image_bytes)
    print(f"   Time     : {elapsed:.1f}s  (inference: {inference_ms}ms)")
    print(f"   Size     : {len(image_bytes) // 1024} KB")
    print(f"   Saved    : {out_path}")


async def _run(photo_path: Path, frame: dict, model: str) -> None:
    from services import storage

    _upload_test_photo(photo_path)
    person_url = storage.get_presigned_url("photos/test-e2e-job.webp")
    r2_key     = storage.r2_key_from_url(frame["product_image_url"])
    frame_url  = storage.get_presigned_url(r2_key) if r2_key else frame["product_image_url"]

    prompt = _build_prompt(frame)

    if model in ("v1", "both"):
        await _call_model(
            endpoint=ENDPOINT_V1,
            payload={
                "prompt":               prompt,
                "image_urls":           [person_url, frame_url],
                "aspect_ratio":         "3:4",
                "response_modalities":  "IMAGE",
            },
            label="Nano Banana v1  ($0.04)",
            out_path=OUTPUT_DIR / "result_nanobanana.jpg",
        )

    if model in ("v2", "both"):
        await _call_model(
            endpoint=ENDPOINT_V2,
            payload={
                "prompt":               prompt,
                "image_urls":           [person_url, frame_url],
                "aspect_ratio":         "3:4",
                "output_format":        "jpg",
                "output_resolution":    "512px",
                "response_modalities":  "IMAGE",
                "thinking_level":       "minimal",
                "safety_tolerance":     4,
                "seed":                 42,
            },
            label="Nano Banana 2   ($0.06 @ 512px)",
            out_path=OUTPUT_DIR / "result_nanobanana2.jpg",
        )


async def main(photo_path: Path, model: str) -> None:
    print("=" * 60)
    print(f"  FrameAI — Nano Banana Test  (model={model})")
    print("=" * 60)

    _check_config()
    frame = _pick_frame()
    await _run(photo_path, frame, model)

    print(f"\n{'='*60}")
    print(f"  ✓  Done! Compare outputs in backend/test_output/:")
    print(f"     result_portrait.webp      — P-Image-Edit     ($0.01)")
    print(f"     result_kontext.jpg        — Multi Kontext Pro ($0.05)")
    print(f"     result_nanobanana.jpg     — Nano Banana v1    ($0.04)")
    print(f"     result_nanobanana2.jpg    — Nano Banana 2     ($0.06 @ 512px)")
    print(f"{'='*60}\n")

    import subprocess, platform
    # Open whichever files exist
    for fname in ["result_nanobanana.jpg", "result_nanobanana2.jpg"]:
        p = OUTPUT_DIR / fname
        if p.exists():
            if platform.system() == "Windows":
                os.startfile(str(p))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True)
    parser.add_argument(
        "--model",
        choices=["v1", "v2", "both"],
        default="both",
        help="v1=$0.04, v2=$0.08, both=run both",
    )
    args = parser.parse_args()

    photo_path = Path(args.photo)
    if not photo_path.exists():
        print(f"✗  Not found: {photo_path}")
        sys.exit(1)

    asyncio.run(main(photo_path, args.model))
