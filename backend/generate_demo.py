"""
One-time script: generates 5 demo try-on images for the DemoSection component.

Run from the backend/ directory (where .env lives):
    python generate_demo.py

Outputs written to frontend/public/demo/:
    person.jpg     — original sample photo (copied from source)
    tryon_1.jpg    — Rectangular · Tortoiseshell
    tryon_2.jpg    — Round · Black Metal
    tryon_3.jpg    — Aviator · Gold
    tryon_4.jpg    — Wayfarer · Navy
    tryon_5.jpg    — Browline · Brown (Clubmaster)
"""

import asyncio
import base64
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Allow imports from backend/ root
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from config import settings
from services import storage

PERSON_PHOTO_PATH = Path(r"C:\Users\aditya kakade\Downloads\sample_01.jpg")
OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "demo"
R2_PERSON_KEY = "demo/sample_person.jpg"

SEGMIND_ENDPOINT = "https://api.segmind.com/v1/nano-banana-2-lite"

FRAMES = [
    {
        "label": "Rectangular · Classic",
        "style": "rectangular",
        "colour": "classic black",
        "url": "https://upload.wikimedia.org/wikipedia/commons/b/b8/Brille_eingeklappt_%28fcm%29.jpg",
    },
    {
        "label": "Round · Tortoiseshell",
        "style": "round",
        "colour": "tortoiseshell",
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/85/Ray-Ban_Round_Icons.jpg",
    },
    {
        "label": "Aviator · Gold",
        "style": "aviator",
        "colour": "gold",
        "url": "https://upload.wikimedia.org/wikipedia/commons/4/4b/RayBanAviator.jpg",
    },
    {
        "label": "Wayfarer · Black",
        "style": "wayfarer",
        "colour": "black",
        "url": "https://upload.wikimedia.org/wikipedia/commons/2/2d/RayBanWayfarer.jpg",
    },
    {
        "label": "Browline · Brown",
        "style": "browline",
        "colour": "brown",
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/04/Browline_glasses.JPG",
    },
]


def build_prompt(style: str, colour: str) -> str:
    return (
        f"Generate an image of the person from image 1 wearing the {colour} {style} eyeglasses "
        f"exactly as shown in image 2. "
        f"The glasses should have the same frame colour, material, lens tint, rim thickness, "
        f"bridge shape, and temple design as shown in image 2. "
        f"Do not change the frame colour or style. "
        f"The person's face, hair, skin tone, eye colour, expression, "
        f"clothing, and background are completely unchanged from image 1."
    )


async def call_segmind(person_url: str, frame_url: str, prompt: str) -> bytes:
    payload = {
        "prompt":              prompt,
        "image_urls":          [person_url, frame_url],
        "aspect_ratio":        "3:4",
        "response_modalities": "IMAGE",
        "output_format":       "jpg",
        "thinking_level":      "minimal",
    }
    headers = {
        "x-api-key":    settings.segmind_api_key,
        "Content-Type": "application/json",
    }

    print(f"       Calling Segmind (this takes ~15–25s)…")
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(SEGMIND_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "image" in content_type:
        return resp.content

    data = resp.json()
    img_b64 = data.get("image") or data.get("output") or data.get("data")
    if not img_b64:
        raise ValueError(f"Unexpected Segmind response keys: {list(data.keys())}")
    return base64.b64decode(img_b64)


async def main() -> None:
    print("=" * 56)
    print("  FrameAI — Demo Image Generator")
    print("=" * 56)

    if not PERSON_PHOTO_PATH.exists():
        print(f"\n✗ ERROR: Sample photo not found at:\n  {PERSON_PHOTO_PATH}")
        sys.exit(1)

    if not settings.segmind_api_key:
        print("\n✗ ERROR: SEGMIND_API_KEY is not set in .env")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Copy original to frontend/public/demo/person.jpg
    dest = OUTPUT_DIR / "person.jpg"
    shutil.copy2(PERSON_PHOTO_PATH, dest)
    print(f"\n✓ Copied person photo → {dest}")

    # Upload to R2 so Segmind can fetch it via HTTPS
    print(f"\nUploading person photo to R2 ({R2_PERSON_KEY})…")
    photo_bytes = PERSON_PHOTO_PATH.read_bytes()
    person_url = storage.upload_temp_and_presign(R2_PERSON_KEY, photo_bytes, content_type="image/jpeg")
    print(f"✓ Uploaded. Presigned URL valid for 1 h.")

    # Download frame images locally and re-upload to R2 (CDNs block Segmind's IP directly)
    print("\nDownloading frame images to R2 (bypassing CDN hotlink protection)…")
    frame_r2_urls: list[str | None] = []
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as client:
        for i, frame in enumerate(FRAMES, 1):
            try:
                resp = await client.get(frame["url"])
                resp.raise_for_status()
                r2_key = f"demo/frame_{i}.jpg"
                r2_url = storage.upload_temp_and_presign(r2_key, resp.content, content_type="image/jpeg")
                frame_r2_urls.append(r2_url)
                print(f"  [{i}/5] ✓ {frame['label']} → R2")
            except Exception as e:
                print(f"  [{i}/5] ✗ {frame['label']} — {e}")
                frame_r2_urls.append(None)

    # Generate 5 try-on images sequentially (respect Segmind rate limits)
    succeeded = 0
    for i, frame in enumerate(FRAMES, 1):
        frame_url = frame_r2_urls[i - 1]
        print(f"\n[{i}/5] {frame['label']}")
        if frame_url is None:
            print(f"  Skipping (frame image download failed).")
            continue
        try:
            prompt = build_prompt(frame["style"], frame["colour"])
            image_bytes = await call_segmind(person_url, frame_url, prompt)
            out_path = OUTPUT_DIR / f"tryon_{i}.jpg"
            out_path.write_bytes(image_bytes)
            print(f"✓ Saved → {out_path}  ({len(image_bytes) // 1024} KB)")
            succeeded += 1
        except httpx.HTTPStatusError as e:
            print(f"✗ HTTP {e.response.status_code} — {e.response.text[:200]}")
            print(f"  Frame {i} skipped.")
        except Exception as e:
            print(f"✗ {e}")
            print(f"  Frame {i} skipped.")

    print(f"\n{'=' * 56}")
    print(f"Done: {succeeded}/5 try-on images generated.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
