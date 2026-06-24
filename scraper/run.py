"""
FrameAI Data Pipeline — main entry point.

Commands:
  scrape    — run source scrapers, save raw JSON to output/raw/
  process   — normalise, image-process, CLIP-annotate, deduplicate → catalogue.json
  annotate  — interactive manual annotation CLI
  load      — upload images to R2, upsert frames to Supabase
  all       — run all steps end-to-end

Usage:
  python run.py scrape  --source all
  python run.py scrape  --source lenskart
  python run.py process
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
