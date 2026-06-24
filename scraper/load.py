"""
Load processed catalogue into Supabase + upload images to Cloudflare R2.

Usage:
    python load.py                          # load all records in catalogue.json
    python load.py --limit 500              # load first 500 (annotated v1 set)
    python load.py --annotated-only         # load only records with face_shape_tags
    python load.py --dry-run                # validate without writing
"""
import asyncio
import io
import json
import logging
import sys
from pathlib import Path

import boto3
import httpx
from botocore.config import Config
from supabase import create_client

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY,
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME, R2_PUBLIC_DOMAIN,
    PROCESSED_DIR, IMAGES_NORM_DIR,
)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Fields to write to the frames table (subset of full record — strips scraper metadata)
DB_FIELDS = [
    "frame_id", "name", "style", "colour", "colour_hex", "material",
    "face_shape_tags", "undertone_tags", "gender_tag",
    "lens_width_mm", "bridge_width_mm", "temple_length_mm",
    "vibe_tags", "retailer", "price_inr", "buy_url",
    "product_image_url", "scraped_at",
]


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_image_to_r2(r2, frame_id: str, local_path: str) -> str:
    """Upload a normalised product image. Returns the public URL."""
    key = f"frames/{frame_id}.webp"
    with open(local_path, "rb") as f:
        r2.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=f.read(),
            ContentType="image/webp",
        )
    return f"{R2_PUBLIC_DOMAIN}/{key}"


def load_catalogue(path: Path | None = None) -> list[dict]:
    path = path or PROCESSED_DIR / "catalogue.json"
    if not path.exists():
        log.error("catalogue.json not found at %s. Run the pipeline first.", path)
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def filter_records(
    catalogue: list[dict],
    annotated_only: bool = False,
    limit: int | None = None,
) -> list[dict]:
    records = catalogue
    if annotated_only:
        records = [r for r in records if r.get("face_shape_tags")]
        log.info("Filtered to %d annotated records", len(records))
    if limit:
        records = records[:limit]
    return records


def prepare_db_record(record: dict) -> dict:
    """Strip scraper metadata, keep only DB fields."""
    db_rec = {k: record.get(k) for k in DB_FIELDS}
    # Ensure arrays are lists (not None)
    for arr_field in ("face_shape_tags", "undertone_tags", "vibe_tags"):
        db_rec[arr_field] = db_rec.get(arr_field) or []
    return db_rec


async def run_load(
    records: list[dict],
    r2,
    supabase,
    dry_run: bool = False,
) -> None:
    uploaded = 0
    skipped = 0
    errors = 0
    batch_size = 50

    for i, record in enumerate(records):
        frame_id = record["frame_id"]

        # ── Upload image to R2 ─────────────────────────────────────────────────
        source_id = record.get("source_id", frame_id)
        local_img = IMAGES_NORM_DIR / f"{source_id}.webp"

        if local_img.exists():
            if not dry_run:
                try:
                    public_url = upload_image_to_r2(r2, frame_id, str(local_img))
                    record["product_image_url"] = public_url
                    uploaded += 1
                except Exception as exc:
                    log.warning("R2 upload failed for %s: %s", frame_id, exc)
                    errors += 1
                    continue
        else:
            # No local image — use the scraped URL directly (may expire)
            if not record.get("product_image_url"):
                log.debug("No image for %s — skipping", frame_id)
                skipped += 1
                continue

        # ── Upsert to Supabase ─────────────────────────────────────────────────
        db_record = prepare_db_record(record)
        if not dry_run:
            try:
                supabase.table("frames").upsert(db_record, on_conflict="frame_id").execute()
            except Exception as exc:
                log.warning("DB upsert failed for %s: %s", frame_id, exc)
                errors += 1

        if (i + 1) % batch_size == 0:
            log.info("Progress: %d/%d (uploaded: %d, skipped: %d, errors: %d)",
                     i + 1, len(records), uploaded, skipped, errors)

    log.info(
        "Load complete: %d records processed, %d images uploaded, %d skipped, %d errors",
        len(records), uploaded, skipped, errors,
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Load catalogue to Supabase + R2")
    parser.add_argument("--annotated-only", action="store_true",
                        help="Only load records with face_shape_tags populated")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum records to load")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and log without writing to DB or R2")
    parser.add_argument("--catalogue", type=str, default=None,
                        help="Path to a specific catalogue.json file")
    args = parser.parse_args()

    catalogue = load_catalogue(Path(args.catalogue) if args.catalogue else None)
    if not catalogue:
        return

    records = filter_records(catalogue, args.annotated_only, args.limit)
    log.info("Loading %d records%s...", len(records), " (dry run)" if args.dry_run else "")

    if args.dry_run:
        for r in records[:5]:
            log.info("Sample record: %s | %s | %s | %s",
                     r.get("name"), r.get("style"), r.get("colour"), r.get("retailer"))
        log.info("Dry run complete. No data written.")
        return

    r2 = _r2_client()
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    asyncio.run(run_load(records, r2, supabase, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
