"""
FrameAI Data Pipeline — main entry point.

Commands:
  scrape         — run source scrapers, save raw JSON to output/raw/
  process        — normalise, image-process, CLIP-annotate, deduplicate → catalogue.json
  auto-annotate  — rule-based annotation (face_shape/undertone/vibe) — no images needed
  annotate       — interactive manual annotation CLI (to review/override auto tags)
  load           — upload images to R2, upsert frames to Supabase
  all            — run all steps end-to-end

Usage:
  python run.py scrape  --source all
  python run.py scrape  --source lenskart
  python run.py process
  python run.py auto-annotate
  python run.py annotate --batch 50
  python run.py load  --annotated-only --limit 500
  python run.py all
"""
import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from config import RAW_DIR, PROCESSED_DIR, IMAGES_RAW_DIR, IMAGES_NORM_DIR


# ── Scrape ─────────────────────────────────────────────────────────────────────

async def cmd_scrape(source: str) -> None:
    from sources.lenskart import LenskartScraper
    from sources.johnjacobs import JohnJacobsScraper
    from sources.titan import TitanScraper
    from sources.rayban import RayBanScraper

    scrapers = {
        "lenskart": LenskartScraper(RAW_DIR),
        "johnjacobs": JohnJacobsScraper(RAW_DIR),
        "titan": TitanScraper(RAW_DIR),
        "rayban": RayBanScraper(RAW_DIR),
    }

    if source == "all":
        targets = list(scrapers.values())
    elif source in scrapers:
        targets = [scrapers[source]]
    else:
        log.error("Unknown source: %s. Choose: all, lenskart, johnjacobs, titan, rayban", source)
        return

    all_raw: list[dict] = []
    for scraper in targets:
        log.info("=== Scraping %s ===", scraper.retailer)
        try:
            records = await scraper.scrape_all()
            all_raw.extend(records)
            log.info("%s: %d records scraped", scraper.retailer, len(records))
        except Exception as exc:
            log.error("Scraper %s failed: %s", scraper.retailer, exc)

    out = RAW_DIR / "all_raw.json"
    out.write_text(json.dumps(all_raw, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Total: %d raw records saved → %s", len(all_raw), out)


# ── Process ────────────────────────────────────────────────────────────────────

async def cmd_process() -> None:
    from pipeline.normalizer import normalise_batch
    from pipeline.image_processor import process_batch
    from pipeline.auto_annotator import annotate_batch
    from pipeline.deduplicator import deduplicate_catalogue

    raw_path = RAW_DIR / "all_raw.json"
    if not raw_path.exists():
        log.error("all_raw.json not found. Run 'scrape' first.")
        return

    raw_records = json.loads(raw_path.read_text(encoding="utf-8"))
    log.info("Loaded %d raw records", len(raw_records))

    # Step 1: Normalise fields
    log.info("=== Step 1: Normalising fields ===")
    normalised = normalise_batch(raw_records)

    # Step 2: Download + process images
    log.info("=== Step 2: Processing images (%d records) ===", len(normalised))
    image_paths = await process_batch(normalised, IMAGES_RAW_DIR, IMAGES_NORM_DIR)
    log.info("Images processed: %d accepted, %d rejected/missing",
             len(image_paths), len(normalised) - len(image_paths))

    # Step 3: CLIP auto-annotation
    log.info("=== Step 3: Auto-annotation ===")
    annotated = annotate_batch(normalised, image_paths)

    # Step 4: Deduplication
    log.info("=== Step 4: Deduplication ===")
    deduplicated = deduplicate_catalogue(annotated, image_paths)

    # Save catalogue
    out = PROCESSED_DIR / "catalogue.json"
    out.write_text(json.dumps(deduplicated, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Catalogue saved: %d records → %s", len(deduplicated), out)



# ── Download images ────────────────────────────────────────────────────────────

async def _cmd_download_images(limit: int | None, dry_run: bool) -> None:
    """
    Download frame images via Playwright (bypasses Lenskart CDN blocking),
    save to IMAGES_NORM_DIR, then upload to R2 and update product_image_url
    in catalogue.json.
    """
    import boto3
    from botocore.config import Config
    from pipeline.image_downloader_playwright import download_images_playwright
    from config import (
        R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
        R2_BUCKET_NAME, R2_PUBLIC_DOMAIN,
    )

    catalogue_path = PROCESSED_DIR / "catalogue.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))

    # Only records still pointing to external CDN URLs (not yet on R2)
    pending = [
        r for r in catalogue
        if r.get("product_image_url") and R2_PUBLIC_DOMAIN not in r["product_image_url"]
    ]
    if limit:
        pending = pending[:limit]

    log.info("%d frames need images downloaded", len(pending))
    if dry_run:
        for r in pending[:5]:
            log.info("  Would download: %s", r["product_image_url"][:70])
        return

    # Build url → local path map (skip already downloaded)
    url_map: dict[str, Path] = {}
    for r in pending:
        src_id = r.get("source_id") or r["frame_id"]
        dest   = IMAGES_NORM_DIR / f"{src_id}.webp"
        if not dest.exists():
            url_map[r["product_image_url"]] = dest

    if url_map:
        log.info("Downloading %d images via Playwright...", len(url_map))
        results = await download_images_playwright(url_map)
        ok = sum(v for v in results.values())
        log.info("Downloaded: %d/%d", ok, len(url_map))
    else:
        log.info("All images already on disk — uploading to R2.")

    # Upload to R2 and update catalogue URLs
    r2 = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    uploaded = 0
    for r in pending:
        src_id    = r.get("source_id") or r["frame_id"]
        local_img = IMAGES_NORM_DIR / f"{src_id}.webp"
        if not local_img.exists():
            continue
        key = f"frames/{r['frame_id']}.webp"
        try:
            r2.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=key,
                Body=local_img.read_bytes(),
                ContentType="image/webp",
            )
            r["product_image_url"] = f"{R2_PUBLIC_DOMAIN}/{key}"
            uploaded += 1
        except Exception as exc:
            log.warning("R2 upload failed for %s: %s", r["frame_id"], exc)

    catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Uploaded %d images to R2. catalogue.json updated.", uploaded)
    log.info("Now run:  python run.py load --limit 409  to push R2 URLs to Supabase.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FrameAI data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # scrape
    p_scrape = sub.add_parser("scrape", help="Run source scrapers")
    p_scrape.add_argument("--source", default="all",
                          choices=["all", "lenskart", "johnjacobs", "titan", "rayban"])

    # process
    sub.add_parser("process", help="Normalise, image-process, annotate, deduplicate")

    # auto-annotate
    sub.add_parser("auto-annotate", help="Rule-based annotation (no images needed)")

    # download-images
    p_dl = sub.add_parser(
        "download-images",
        help="Download all frame images via Playwright and upload to R2 (fixes Lenskart CDN blocking)"
    )
    p_dl.add_argument("--limit", type=int, default=None, help="Max images to download")
    p_dl.add_argument("--dry-run", action="store_true")

    # export-nostyle
    sub.add_parser("export-nostyle", help="Export records with no style to annotation/no_style_records.json (for Colab)")

    # apply-style-predictions
    p_asp = sub.add_parser("apply-style-predictions", help="Merge Colab style_predictions.csv back into catalogue.json")
    p_asp.add_argument("--csv", default=None, help="Path to style_predictions.csv (default: annotation/style_predictions.csv)")

    # annotate
    p_ann = sub.add_parser("annotate", help="Interactive manual annotation CLI")
    p_ann.add_argument("--batch", type=int, default=50)
    p_ann.add_argument("--merge", action="store_true")
    p_ann.add_argument("--export", action="store_true")

    # load
    p_load = sub.add_parser("load", help="Upload to R2 and load to Supabase")
    p_load.add_argument("--annotated-only", action="store_true")
    p_load.add_argument("--limit", type=int, default=None)
    p_load.add_argument("--dry-run", action="store_true")

    # all
    p_all = sub.add_parser("all", help="Run full pipeline end-to-end")
    p_all.add_argument("--source", default="all")
    p_all.add_argument("--limit", type=int, default=500)

    args = parser.parse_args()

    if args.command == "scrape":
        asyncio.run(cmd_scrape(args.source))

    elif args.command == "process":
        asyncio.run(cmd_process())

    elif args.command == "auto-annotate":
        from pipeline.rule_annotator import run_auto_annotate
        from config import ANNOTATION_DIR
        run_auto_annotate(
            catalogue_path=PROCESSED_DIR / "catalogue.json",
            annotations_csv=ANNOTATION_DIR / "annotations.csv",
        )

    elif args.command == "download-images":
        asyncio.run(_cmd_download_images(args.limit, args.dry_run))

    elif args.command == "export-nostyle":
        from config import ANNOTATION_DIR
        catalogue = json.loads((PROCESSED_DIR / "catalogue.json").read_text(encoding="utf-8"))
        no_style = [r for r in catalogue if not r.get("style")]
        out = ANNOTATION_DIR / "no_style_records.json"
        out.write_text(json.dumps(no_style, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Exported %d no-style records → %s", len(no_style), out)

    elif args.command == "apply-style-predictions":
        import csv as _csv
        from config import ANNOTATION_DIR
        from pipeline.rule_annotator import auto_annotate_catalogue

        csv_path = Path(args.csv) if args.csv else ANNOTATION_DIR / "style_predictions.csv"
        if not csv_path.exists():
            log.error("CSV not found: %s", csv_path)
            sys.exit(1)

        # Load predictions — only accept rows that downloaded and classified OK
        predictions: dict[str, str] = {}
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                if row.get("status", "ok") not in ("ok", ""):
                    continue
                style = (row.get("predicted_style") or "").strip()
                if style:
                    predictions[row["frame_id"]] = style

        log.info("Loaded %d style predictions from %s", len(predictions), csv_path)

        # Apply to catalogue
        catalogue_path = PROCESSED_DIR / "catalogue.json"
        catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
        applied = 0
        for r in catalogue:
            if not r.get("style") and r["frame_id"] in predictions:
                r["style"] = predictions[r["frame_id"]]
                applied += 1

        log.info("Applied %d style predictions to catalogue", applied)

        # Re-run rule annotation to fill face_shape_tags for newly styled records
        catalogue = auto_annotate_catalogue(catalogue)
        catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("catalogue.json updated — %d records now have style", sum(1 for r in catalogue if r.get("style")))

    elif args.command == "annotate":
        from annotation.review_tool import run_annotation_session, run_merge, export_to_annotate, load_catalogue, load_existing_annotations
        if args.merge:
            run_merge()
        elif args.export:
            cat = load_catalogue()
            existing = load_existing_annotations()
            export_to_annotate(cat, existing)
        else:
            run_annotation_session(batch_size=args.batch)

    elif args.command == "load":
        from load import main as load_main
        sys.argv = [sys.argv[0]]
        if args.annotated_only:
            sys.argv.append("--annotated-only")
        if args.limit:
            sys.argv += ["--limit", str(args.limit)]
        if args.dry_run:
            sys.argv.append("--dry-run")
        load_main()

    elif args.command == "all":
        async def _all():
            await cmd_scrape(args.source)
            await cmd_process()
        asyncio.run(_all())
        log.info("\nNext steps:")
        log.info("  1. python run.py annotate --batch 50")
        log.info("  2. python run.py annotate --merge")
        log.info("  3. python run.py load --annotated-only --limit 500")


if __name__ == "__main__":
    main()
