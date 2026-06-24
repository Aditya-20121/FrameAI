"""
Seed 20 fully-annotated sample frames into Supabase for end-to-end testing.

Frames are carefully chosen to cover:
  - All 6 face shapes (oval, round, square, heart, diamond, oblong)
  - All 3 undertones (warm, cool, neutral)
  - All 4 retailers (Lenskart, Titan Eye+, John Jacobs, Ray-Ban)
  - All major styles (rectangular, round, oval, square, cat-eye, wayfarer, aviator, browline, geometric, rimless)
  - All price tiers (₹800 – ₹14,000)

product_image_url points to publicly available product images from the retailers.
These URLs may expire — replace with your own R2 URLs after running the scraper.

Usage:
    cd backend
    python db/seed.py
    python db/seed.py --dry-run   # print records without inserting
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SEED_FRAMES = [
    # ── 1. Rectangular | Tortoiseshell | Lenskart ──────────────────────────
    {
        "frame_id": "11111111-0001-0000-0000-000000000001",
        "name": "Vincent Chase VC E14662 C1",
        "style": "rectangular",
        "colour": "tortoiseshell",
        "colour_hex": "#8B5C2A",
        "material": "acetate",
        "face_shape_tags": ["oval", "round", "oblong"],
        "undertone_tags": ["warm", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 52,
        "bridge_width_mm": 17,
        "temple_length_mm": 140,
        "vibe_tags": ["classic", "professional"],
        "retailer": "Lenskart",
        "price_inr": 1499,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e14662-c1-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/cache/1/thumbnail/628x301/9df78eab33525d08d6e5fb8d27136e95/v/i/vincent-chase-vc-e14662-c1-eyeglasses.jpg",
    },
    # ── 2. Round | Black | Titan Eye+ ─────────────────────────────────────
    {
        "frame_id": "11111111-0002-0000-0000-000000000002",
        "name": "Titan Eye+ T1203 C1",
        "style": "round",
        "colour": "black",
        "colour_hex": "#1A1A1A",
        "material": "metal",
        "face_shape_tags": ["square", "heart", "oblong"],
        "undertone_tags": ["cool", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 50,
        "bridge_width_mm": 20,
        "temple_length_mm": 145,
        "vibe_tags": ["minimal", "editorial"],
        "retailer": "Titan Eye+",
        "price_inr": 2299,
        "buy_url": "https://www.titaneyeplus.com/product/T1203C1",
        "product_image_url": "https://www.titaneyeplus.com/media/catalog/product/T/1/T1203C1.jpg",
    },
    # ── 3. Cat-eye | Burgundy | John Jacobs ───────────────────────────────
    {
        "frame_id": "11111111-0003-0000-0000-000000000003",
        "name": "John Jacobs JJ E13456 C2",
        "style": "cat-eye",
        "colour": "burgundy",
        "colour_hex": "#800020",
        "material": "acetate",
        "face_shape_tags": ["diamond", "oval", "square"],
        "undertone_tags": ["cool"],
        "gender_tag": "women",
        "lens_width_mm": 50,
        "bridge_width_mm": 18,
        "temple_length_mm": 140,
        "vibe_tags": ["editorial", "bold"],
        "retailer": "John Jacobs",
        "price_inr": 3499,
        "buy_url": "https://www.johnjacobs.com/jj-e13456-c2-eyeglasses.html",
        "product_image_url": "https://static.johnjacobs.com/media/catalog/product/jj-e13456-c2.jpg",
    },
    # ── 4. Browline | Brown | Ray-Ban ──────────────────────────────────────
    {
        "frame_id": "11111111-0004-0000-0000-000000000004",
        "name": "Ray-Ban RB5154 Clubmaster",
        "style": "browline",
        "colour": "brown",
        "colour_hex": "#654321",
        "material": "mixed",
        "face_shape_tags": ["oval", "heart", "diamond"],
        "undertone_tags": ["warm"],
        "gender_tag": "unisex",
        "lens_width_mm": 51,
        "bridge_width_mm": 21,
        "temple_length_mm": 145,
        "vibe_tags": ["retro", "classic", "professional"],
        "retailer": "Ray-Ban",
        "price_inr": 9990,
        "buy_url": "https://www.ray-ban.com/en_IN/p/rb5154-clubmaster/RB5154__2372",
        "product_image_url": "https://www.ray-ban.com/media/catalog/product/R/B/RB5154_2372_001_shad_qt.png",
    },
    # ── 5. Wayfarer | Navy | Lenskart ─────────────────────────────────────
    {
        "frame_id": "11111111-0005-0000-0000-000000000005",
        "name": "Vincent Chase VC E13553 C6",
        "style": "wayfarer",
        "colour": "navy",
        "colour_hex": "#001F5B",
        "material": "acetate",
        "face_shape_tags": ["round", "oblong", "oval"],
        "undertone_tags": ["cool", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 54,
        "bridge_width_mm": 18,
        "temple_length_mm": 145,
        "vibe_tags": ["classic", "bold"],
        "retailer": "Lenskart",
        "price_inr": 1799,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e13553-c6-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/v/c/vc-e13553-c6.jpg",
    },
    # ── 6. Oval | Rose Gold | John Jacobs ─────────────────────────────────
    {
        "frame_id": "11111111-0006-0000-0000-000000000006",
        "name": "John Jacobs JJ E11234 C3",
        "style": "oval",
        "colour": "rose_gold",
        "colour_hex": "#B76E79",
        "material": "metal",
        "face_shape_tags": ["square", "round", "oblong"],
        "undertone_tags": ["warm", "neutral"],
        "gender_tag": "women",
        "lens_width_mm": 51,
        "bridge_width_mm": 16,
        "temple_length_mm": 140,
        "vibe_tags": ["minimal", "editorial"],
        "retailer": "John Jacobs",
        "price_inr": 4299,
        "buy_url": "https://www.johnjacobs.com/jj-e11234-c3-eyeglasses.html",
        "product_image_url": "https://static.johnjacobs.com/media/catalog/product/jj-e11234-c3.jpg",
    },
    # ── 7. Geometric | Gunmetal | Titan Eye+ ──────────────────────────────
    {
        "frame_id": "11111111-0007-0000-0000-000000000007",
        "name": "Titan Eye+ T3112 C5",
        "style": "geometric",
        "colour": "gunmetal",
        "colour_hex": "#545E6B",
        "material": "metal",
        "face_shape_tags": ["oval", "heart"],
        "undertone_tags": ["cool"],
        "gender_tag": "men",
        "lens_width_mm": 53,
        "bridge_width_mm": 18,
        "temple_length_mm": 145,
        "vibe_tags": ["minimal", "professional"],
        "retailer": "Titan Eye+",
        "price_inr": 3199,
        "buy_url": "https://www.titaneyeplus.com/product/T3112C5",
        "product_image_url": "https://www.titaneyeplus.com/media/catalog/product/T/3/T3112C5.jpg",
    },
    # ── 8. Rimless | Clear | Lenskart ─────────────────────────────────────
    {
        "frame_id": "11111111-0008-0000-0000-000000000008",
        "name": "Vincent Chase VC E15234 C1",
        "style": "rimless",
        "colour": "clear",
        "colour_hex": "#E8E8F0",
        "material": "titanium",
        "face_shape_tags": ["heart", "diamond", "oval"],
        "undertone_tags": ["warm", "cool", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 50,
        "bridge_width_mm": 16,
        "temple_length_mm": 140,
        "vibe_tags": ["minimal"],
        "retailer": "Lenskart",
        "price_inr": 2499,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e15234-c1-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/v/c/vc-e15234-c1.jpg",
    },
    # ── 9. Square | Tortoiseshell | Ray-Ban ───────────────────────────────
    {
        "frame_id": "11111111-0009-0000-0000-000000000009",
        "name": "Ray-Ban RB5228 Square",
        "style": "square",
        "colour": "tortoiseshell",
        "colour_hex": "#7B4F2C",
        "material": "acetate",
        "face_shape_tags": ["round", "oval"],
        "undertone_tags": ["warm", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 55,
        "bridge_width_mm": 17,
        "temple_length_mm": 145,
        "vibe_tags": ["classic", "professional"],
        "retailer": "Ray-Ban",
        "price_inr": 10490,
        "buy_url": "https://www.ray-ban.com/en_IN/p/rb5228/RB5228__2144",
        "product_image_url": "https://www.ray-ban.com/media/catalog/product/R/B/RB5228_2144_001_shad_qt.png",
    },
    # ── 10. Rectangular | Silver | John Jacobs ────────────────────────────
    {
        "frame_id": "11111111-0010-0000-0000-000000000010",
        "name": "John Jacobs JJ E12103 C1",
        "style": "rectangular",
        "colour": "silver",
        "colour_hex": "#C0C0C0",
        "material": "metal",
        "face_shape_tags": ["round", "oblong", "oval"],
        "undertone_tags": ["cool"],
        "gender_tag": "men",
        "lens_width_mm": 54,
        "bridge_width_mm": 17,
        "temple_length_mm": 140,
        "vibe_tags": ["professional", "minimal"],
        "retailer": "John Jacobs",
        "price_inr": 3999,
        "buy_url": "https://www.johnjacobs.com/jj-e12103-c1-eyeglasses.html",
        "product_image_url": "https://static.johnjacobs.com/media/catalog/product/jj-e12103-c1.jpg",
    },
    # ── 11. Aviator | Gold | Lenskart ─────────────────────────────────────
    {
        "frame_id": "11111111-0011-0000-0000-000000000011",
        "name": "Vincent Chase VC E14001 C2",
        "style": "aviator",
        "colour": "gold",
        "colour_hex": "#C8A000",
        "material": "metal",
        "face_shape_tags": ["oval", "heart", "round"],
        "undertone_tags": ["warm"],
        "gender_tag": "unisex",
        "lens_width_mm": 58,
        "bridge_width_mm": 14,
        "temple_length_mm": 135,
        "vibe_tags": ["classic", "bold", "retro"],
        "retailer": "Lenskart",
        "price_inr": 1299,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e14001-c2-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/v/c/vc-e14001-c2.jpg",
    },
    # ── 12. Round | Amber | Titan Eye+ ────────────────────────────────────
    {
        "frame_id": "11111111-0012-0000-0000-000000000012",
        "name": "Titan Eye+ T4221 C3",
        "style": "round",
        "colour": "amber",
        "colour_hex": "#C89600",
        "material": "acetate",
        "face_shape_tags": ["square", "diamond", "oblong"],
        "undertone_tags": ["warm"],
        "gender_tag": "unisex",
        "lens_width_mm": 49,
        "bridge_width_mm": 20,
        "temple_length_mm": 145,
        "vibe_tags": ["retro", "editorial"],
        "retailer": "Titan Eye+",
        "price_inr": 2699,
        "buy_url": "https://www.titaneyeplus.com/product/T4221C3",
        "product_image_url": "https://www.titaneyeplus.com/media/catalog/product/T/4/T4221C3.jpg",
    },
    # ── 13. Browline | Olive | Lenskart ───────────────────────────────────
    {
        "frame_id": "11111111-0013-0000-0000-000000000013",
        "name": "Vincent Chase VC E16789 C4",
        "style": "browline",
        "colour": "olive",
        "colour_hex": "#6B8E23",
        "material": "mixed",
        "face_shape_tags": ["oval", "diamond"],
        "undertone_tags": ["warm"],
        "gender_tag": "men",
        "lens_width_mm": 52,
        "bridge_width_mm": 19,
        "temple_length_mm": 145,
        "vibe_tags": ["retro", "classic"],
        "retailer": "Lenskart",
        "price_inr": 1899,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e16789-c4-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/v/c/vc-e16789-c4.jpg",
    },
    # ── 14. Cat-eye | Navy | John Jacobs ──────────────────────────────────
    {
        "frame_id": "11111111-0014-0000-0000-000000000014",
        "name": "John Jacobs JJ E13445 C5",
        "style": "cat-eye",
        "colour": "navy",
        "colour_hex": "#001F5B",
        "material": "acetate",
        "face_shape_tags": ["diamond", "oval"],
        "undertone_tags": ["cool"],
        "gender_tag": "women",
        "lens_width_mm": 51,
        "bridge_width_mm": 17,
        "temple_length_mm": 140,
        "vibe_tags": ["editorial", "bold", "professional"],
        "retailer": "John Jacobs",
        "price_inr": 3799,
        "buy_url": "https://www.johnjacobs.com/jj-e13445-c5-eyeglasses.html",
        "product_image_url": "https://static.johnjacobs.com/media/catalog/product/jj-e13445-c5.jpg",
    },
    # ── 15. Wayfarer | Black | Titan Eye+ ─────────────────────────────────
    {
        "frame_id": "11111111-0015-0000-0000-000000000015",
        "name": "Titan Eye+ T5123 C1",
        "style": "wayfarer",
        "colour": "black",
        "colour_hex": "#1A1A1A",
        "material": "acetate",
        "face_shape_tags": ["round", "oblong", "oval"],
        "undertone_tags": ["cool", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 54,
        "bridge_width_mm": 18,
        "temple_length_mm": 145,
        "vibe_tags": ["classic", "bold"],
        "retailer": "Titan Eye+",
        "price_inr": 2499,
        "buy_url": "https://www.titaneyeplus.com/product/T5123C1",
        "product_image_url": "https://www.titaneyeplus.com/media/catalog/product/T/5/T5123C1.jpg",
    },
    # ── 16. Rectangular | Blue | Ray-Ban ──────────────────────────────────
    {
        "frame_id": "11111111-0016-0000-0000-000000000016",
        "name": "Ray-Ban RB5362 New Wayfarer",
        "style": "rectangular",
        "colour": "blue",
        "colour_hex": "#4169E1",
        "material": "acetate",
        "face_shape_tags": ["round", "oblong", "oval"],
        "undertone_tags": ["cool"],
        "gender_tag": "unisex",
        "lens_width_mm": 55,
        "bridge_width_mm": 18,
        "temple_length_mm": 145,
        "vibe_tags": ["bold", "sporty"],
        "retailer": "Ray-Ban",
        "price_inr": 11490,
        "buy_url": "https://www.ray-ban.com/en_IN/p/rb5362/RB5362__8197",
        "product_image_url": "https://www.ray-ban.com/media/catalog/product/R/B/RB5362_8197_001_shad_qt.png",
    },
    # ── 17. Geometric | Cognac | Lenskart ────────────────────────────────
    {
        "frame_id": "11111111-0017-0000-0000-000000000017",
        "name": "Vincent Chase VC E17234 C5",
        "style": "geometric",
        "colour": "cognac",
        "colour_hex": "#9C6114",
        "material": "acetate",
        "face_shape_tags": ["oval", "heart"],
        "undertone_tags": ["warm"],
        "gender_tag": "unisex",
        "lens_width_mm": 52,
        "bridge_width_mm": 17,
        "temple_length_mm": 140,
        "vibe_tags": ["editorial", "bold"],
        "retailer": "Lenskart",
        "price_inr": 2099,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e17234-c5-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/v/c/vc-e17234-c5.jpg",
    },
    # ── 18. Oval | Warm Grey | John Jacobs ────────────────────────────────
    {
        "frame_id": "11111111-0018-0000-0000-000000000018",
        "name": "John Jacobs JJ E14556 C2",
        "style": "oval",
        "colour": "warm_grey",
        "colour_hex": "#968C82",
        "material": "titanium",
        "face_shape_tags": ["round", "square", "oblong"],
        "undertone_tags": ["neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 52,
        "bridge_width_mm": 17,
        "temple_length_mm": 140,
        "vibe_tags": ["minimal", "professional"],
        "retailer": "John Jacobs",
        "price_inr": 6999,
        "buy_url": "https://www.johnjacobs.com/jj-e14556-c2-eyeglasses.html",
        "product_image_url": "https://static.johnjacobs.com/media/catalog/product/jj-e14556-c2.jpg",
    },
    # ── 19. Square | Caramel | Titan Eye+ ─────────────────────────────────
    {
        "frame_id": "11111111-0019-0000-0000-000000000019",
        "name": "Titan Eye+ T6234 C4",
        "style": "square",
        "colour": "caramel",
        "colour_hex": "#C47F41",
        "material": "acetate",
        "face_shape_tags": ["oval", "round"],
        "undertone_tags": ["warm"],
        "gender_tag": "unisex",
        "lens_width_mm": 53,
        "bridge_width_mm": 18,
        "temple_length_mm": 145,
        "vibe_tags": ["retro", "classic"],
        "retailer": "Titan Eye+",
        "price_inr": 2899,
        "buy_url": "https://www.titaneyeplus.com/product/T6234C4",
        "product_image_url": "https://www.titaneyeplus.com/media/catalog/product/T/6/T6234C4.jpg",
    },
    # ── 20. Rimless | Silver | Lenskart ───────────────────────────────────
    {
        "frame_id": "11111111-0020-0000-0000-000000000020",
        "name": "Vincent Chase VC E18123 C3",
        "style": "rimless",
        "colour": "silver",
        "colour_hex": "#C0C0C0",
        "material": "titanium",
        "face_shape_tags": ["oval", "heart", "diamond"],
        "undertone_tags": ["cool", "neutral"],
        "gender_tag": "unisex",
        "lens_width_mm": 52,
        "bridge_width_mm": 15,
        "temple_length_mm": 140,
        "vibe_tags": ["minimal", "professional"],
        "retailer": "Lenskart",
        "price_inr": 3299,
        "buy_url": "https://www.lenskart.com/vincent-chase-vc-e18123-c3-eyeglasses.html",
        "product_image_url": "https://static.lenskart.com/media/catalog/product/v/c/vc-e18123-c3.jpg",
    },
]


def insert_seed_frames(dry_run: bool = False) -> None:
    if dry_run:
        print(f"[dry-run] Would insert {len(SEED_FRAMES)} frames:")
        for f in SEED_FRAMES:
            print(f"  {f['name']:45s} | {f['style']:12s} | {f['colour']:15s} | {f['retailer']}")
        return

    from supabase import create_client
    import os
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(supabase_url, supabase_key)

    result = client.table("frames").upsert(SEED_FRAMES, on_conflict="frame_id").execute()
    inserted = len(result.data) if result.data else 0
    print(f"Inserted/updated {inserted} seed frames.")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Load .env from backend/
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

    parser = argparse.ArgumentParser(description="Seed test frames into Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Print without inserting")
    args = parser.parse_args()

    insert_seed_frames(dry_run=args.dry_run)
