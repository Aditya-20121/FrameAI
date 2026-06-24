"""
Manual annotation CLI tool.

Usage:
    python annotation/review_tool.py                 # annotate all pending
    python annotation/review_tool.py --batch 50      # annotate next 50
    python annotation/review_tool.py --resume        # skip already annotated

For each frame:
  - Opens the normalised product image in the OS default viewer
  - Displays current auto-tags (style, colour, CLIP confidence)
  - Prompts for face_shape_tags and vibe_tags
  - Saves to annotation/annotations.csv

After running, merge back via:
    python annotation/review_tool.py --merge
"""
import csv
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROCESSED_DIR, IMAGES_NORM_DIR, ANNOTATION_DIR

console = Console() if HAS_RICH else None

ANNOTATIONS_CSV = ANNOTATION_DIR / "annotations.csv"
TO_ANNOTATE_CSV = ANNOTATION_DIR / "to_annotate.csv"
CATALOGUE_JSON = PROCESSED_DIR / "catalogue.json"

VALID_FACE_SHAPES = ["oval", "round", "square", "heart", "diamond", "oblong"]
VALID_VIBES = ["minimal", "editorial", "retro", "bold", "professional", "sporty", "classic"]


def _print(msg: str, style: str = "") -> None:
    if HAS_RICH and console:
        console.print(msg, style=style)
    else:
        print(msg)


def open_image(path: str) -> None:
    """Open image in OS default viewer."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        _print(f"  [Could not auto-open image: {path}]")


def load_catalogue() -> list[dict]:
    if not CATALOGUE_JSON.exists():
        _print("[red]catalogue.json not found. Run the pipeline first.[/red]")
        return []
    return json.loads(CATALOGUE_JSON.read_text(encoding="utf-8"))


def load_existing_annotations() -> dict[str, dict]:
    """Load already-saved annotations keyed by frame_id."""
    if not ANNOTATIONS_CSV.exists():
        return {}
    with open(ANNOTATIONS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["frame_id"]: row for row in reader}


def save_annotation(annotation: dict) -> None:
    """Append one annotation to the CSV file."""
    fieldnames = ["frame_id", "face_shape_tags", "undertone_tags", "vibe_tags", "notes"]
    file_exists = ANNOTATIONS_CSV.exists()
    with open(ANNOTATIONS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(annotation)


def export_to_annotate(catalogue: list[dict], existing: dict[str, dict]) -> None:
    """Export unannotated records to to_annotate.csv for batch review."""
    pending = [r for r in catalogue if r["frame_id"] not in existing]
    with open(TO_ANNOTATE_CSV, "w", newline="", encoding="utf-8") as f:
        if not pending:
            _print("[yellow]All records already annotated.[/yellow]")
            return
        writer = csv.DictWriter(f, fieldnames=pending[0].keys())
        writer.writeheader()
        writer.writerows(pending)
    _print(f"[green]Exported {len(pending)} records → {TO_ANNOTATE_CSV}[/green]")


def merge_annotations(catalogue: list[dict], annotations: dict[str, dict]) -> list[dict]:
    """Merge human annotations back into catalogue records."""
    merged = []
    for record in catalogue:
        ann = annotations.get(record["frame_id"])
        if ann:
            record["face_shape_tags"] = [s.strip() for s in ann.get("face_shape_tags", "").split(",") if s.strip()]
            record["undertone_tags"] = [s.strip() for s in ann.get("undertone_tags", "").split(",") if s.strip()]
            record["vibe_tags"] = [s.strip() for s in ann.get("vibe_tags", "").split(",") if s.strip()]
        merged.append(record)
    return merged


def _prompt_tags(prompt_text: str, valid: list[str]) -> list[str]:
    """Prompt for comma-separated tags, validate against valid list."""
    valid_str = ", ".join(valid)
    while True:
        if HAS_RICH:
            raw = Prompt.ask(f"  [bold]{prompt_text}[/bold] [dim]({valid_str})[/dim]")
        else:
            raw = input(f"  {prompt_text} ({valid_str}): ")

        tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
        invalid = [t for t in tags if t not in valid]
        if invalid:
            _print(f"  [red]Unknown tags: {invalid}. Please use only: {valid_str}[/red]")
            continue
        return tags


def annotate_record(record: dict) -> dict | None:
    """
    Interactive annotation of one record.
    Returns annotation dict or None if user skipped.
    """
    frame_id = record["frame_id"]
    name = record.get("name", "Unknown")
    style = record.get("style", "?")
    colour = record.get("colour", "?")
    retailer = record.get("retailer", "?")
    price = record.get("price_inr")
    clip_conf = record.get("clip_style_confidence")

    _print(f"\n{'='*60}")
    _print(f"[bold cyan]{name}[/bold cyan]")
    _print(f"  Style:   [yellow]{style}[/yellow]" + (f" [dim](CLIP conf: {clip_conf:.2f})[/dim]" if clip_conf else ""))
    _print(f"  Colour:  [yellow]{colour}[/yellow]")
    _print(f"  Retailer: {retailer}  |  Price: ₹{price or '?'}")
    _print(f"  ID: {frame_id}")

    # Open image
    img_path = str(IMAGES_NORM_DIR / f"{record.get('source_id', frame_id)}.webp")
    if Path(img_path).exists():
        _print(f"  [dim]Opening image: {img_path}[/dim]")
        open_image(img_path)
    else:
        _print(f"  [dim]Image not found: {img_path}[/dim]")

    # Skip option
    if HAS_RICH:
        skip = Confirm.ask("  Skip this frame?", default=False)
    else:
        skip = input("  Skip? [y/N]: ").strip().lower() == "y"
    if skip:
        return None

    face_shape_tags = _prompt_tags("Face shape tags", VALID_FACE_SHAPES)
    undertone_tags = _prompt_tags("Undertone tags", ["warm", "cool", "neutral"])
    vibe_tags = _prompt_tags("Vibe tags", VALID_VIBES)

    if HAS_RICH:
        notes = Prompt.ask("  Notes [optional]", default="")
    else:
        notes = input("  Notes (optional): ").strip()

    return {
        "frame_id": frame_id,
        "face_shape_tags": ",".join(face_shape_tags),
        "undertone_tags": ",".join(undertone_tags),
        "vibe_tags": ",".join(vibe_tags),
        "notes": notes,
    }


def run_annotation_session(batch_size: int = 50, resume: bool = True) -> None:
    catalogue = load_catalogue()
    if not catalogue:
        return

    existing = load_existing_annotations() if resume else {}
    pending = [r for r in catalogue if r["frame_id"] not in existing]

    if not pending:
        _print("[green]All records are already annotated.[/green]")
        return

    batch = pending[:batch_size]
    _print(f"\n[bold]Starting annotation session: {len(batch)} records (of {len(pending)} pending)[/bold]")
    _print("Press Ctrl+C at any time — progress is saved after each frame.\n")

    done = 0
    try:
        for record in batch:
            ann = annotate_record(record)
            if ann:
                save_annotation(ann)
                done += 1
    except KeyboardInterrupt:
        _print(f"\n[yellow]Session interrupted. Saved {done} annotations.[/yellow]")
        return

    _print(f"\n[green]Session complete. Annotated {done} frames.[/green]")


def run_merge() -> None:
    catalogue = load_catalogue()
    annotations = load_existing_annotations()
    merged = merge_annotations(catalogue, annotations)
    CATALOGUE_JSON.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    annotated_count = sum(1 for r in merged if r.get("face_shape_tags"))
    _print(f"[green]Merged {len(annotations)} annotations into catalogue.json ({annotated_count} records annotated)[/green]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FrameAI manual annotation tool")
    parser.add_argument("--batch", type=int, default=50, help="Records per session")
    parser.add_argument("--resume", action="store_true", default=True, help="Skip already-annotated records")
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--merge", action="store_true", help="Merge annotations into catalogue.json and exit")
    parser.add_argument("--export", action="store_true", help="Export pending records to to_annotate.csv and exit")
    args = parser.parse_args()

    if args.merge:
        run_merge()
    elif args.export:
        cat = load_catalogue()
        existing = load_existing_annotations()
        export_to_annotate(cat, existing)
    else:
        run_annotation_session(batch_size=args.batch, resume=args.resume)
