"""
One-time script: regenerates the 5 demo try-on images for DemoSection using
frames actually in the FrameAI catalogue (R2), per the user's selection.

Run from the backend/ directory (where .env lives):
    python generate_demo2.py

Outputs written to frontend/public/demo/ (overwrites tryon_1..5.jpg):
    tryon_1.jpg — Square · Clear      (Lenskart Air LA E14362-N)
    tryon_2.jpg — Geometric · Brown   (Vincent Chase VC E13788)
    tryon_3.jpg — Rectangular · Blush (Vincent Chase VC E13447)
    tryon_4.jpg — Rimless · Purple    (Vincent Chase VC E14324)
    tryon_5.jpg — Aviator · Silver    (Vincent Chase VC E12422, sunglasses)
"""

import asyncio
import base64
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from config import settings
from services import storage

OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "demo"
R2_PERSON_KEY = "demo/sample_person.jpg"
SEGMIND_ENDPOINT = "https://api.segmind.com/v1/nano-banana-2-lite"

FRAMES = [
    {
        "n": 1,
        "id": "35ac5395-ef79-5afa-ba2d-a0f6373c122d",
        "label": "Square · Clear",
        "style": "square",
        "colour": "clear / transparent",
    },
    {
        "n": 2,
        "id": "b2e39c51-0b9e-5b49-b870-04d81507854e",
        "label": "Geometric · Brown",
        "style": "geometric",
        "colour": "brown",
    },
    {
        "n": 3,
        "id": "c5531447-09f1-5361-8213-045d894094ac",
        "label": "Rectangular · Blush",
        "style": "rectangular",
        "colour": "blush pink",
    },
    {
        "n": 4,
        "id": "bb2ca23c-30ee-5668-b0c5-eeaeb756c42d",
        "label": "Rimless · Purple",
        "style": "rimless",
        "colour": "purple",
    },
    {
        "n": 5,
        "id": "aa08adab-1d79-5b4b-81cc-19036ad4c5aa",
        "label": "Aviator · Silver",
        "style": "aviator sunglasses",
        "colour": "silver metal with dark tinted lenses",
    },
]


def build_prompt(style: str, colour: str) -> str:
    return (
        f"Generate an image of the person from image 1 wearing the {colour} {style} eyewear "
        f"exactly as shown in image 2. "
        f"The eyewear should have the same frame colour, material, lens tint, rim thickness, "
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

    print("       Calling Segmind (this takes ~15-25s)...")
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
    print("  FrameAI - Demo Image Generator (catalogue frames)")
    print("=" * 56)

    if not settings.segmind_api_key:
        print("\nERROR: SEGMIND_API_KEY is not set in .env")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Re-presign the already-uploaded person photo
    print(f"\nPresigning person photo ({R2_PERSON_KEY})...")
    person_url = storage.get_presigned_url(R2_PERSON_KEY, expiry=3600)
    print("Done.")

    # Presign each catalogue frame directly from R2 (no re-upload needed)
    print("\nPresigning catalogue frame images...")
    frame_urls: list[str] = []
    for f in FRAMES:
        key = f"frames/{f['id']}.webp"
        url = storage.get_presigned_url(key, expiry=3600)
        frame_urls.append(url)
        print(f"  [{f['n']}] {f['label']} -> presigned")

    # Generate 5 try-on images sequentially (respect Segmind rate limits)
    succeeded = 0
    for i, frame in enumerate(FRAMES, 1):
        frame_url = frame_urls[i - 1]
        print(f"\n[{i}/5] {frame['label']}")
        try:
            prompt = build_prompt(frame["style"], frame["colour"])
            image_bytes = await call_segmind(person_url, frame_url, prompt)
            out_path = OUTPUT_DIR / f"tryon_{i}.jpg"
            out_path.write_bytes(image_bytes)
            print(f"Saved -> {out_path}  ({len(image_bytes) // 1024} KB)")
            succeeded += 1
        except httpx.HTTPStatusError as e:
            print(f"HTTP {e.response.status_code} - {e.response.text[:200]}")
            print(f"  Frame {i} skipped.")
        except Exception as e:
            print(f"{e}")
            print(f"  Frame {i} skipped.")

    print(f"\n{'=' * 56}")
    print(f"Done: {succeeded}/5 try-on images generated.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
