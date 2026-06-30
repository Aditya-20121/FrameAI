"""
Rule-based automatic annotation.

Assigns face_shape_tags, undertone_tags, and vibe_tags to every catalogue
record without requiring product images or any external API.

Logic:
  undertone_tags  — derived from the frame's colour field
  face_shape_tags — inverted from FACE_SHAPE_RULES (which face shapes does
                    this frame *style* suit?)
  vibe_tags       — style + brand heuristics

Usage:
  from pipeline.rule_annotator import auto_annotate_catalogue
  updated = auto_annotate_catalogue(records)
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ── Undertone map ─────────────────────────────────────────────────────────────
# Derived from RECOMMENDATION_RULES.md UNDERTONE_RULES best_colours lists.
# Colours that appear in multiple undertone buckets get the most specific tag.

_COLOUR_UNDERTONE: dict[str, list[str]] = {
    "tortoiseshell": ["warm"],
    "amber":         ["warm"],
    "brown":         ["warm"],
    "olive":         ["warm"],
    "gold":          ["warm"],
    "rose_gold":     ["warm"],
    "tan":           ["warm"],
    "honey":         ["warm"],
    "cognac":        ["warm"],
    "caramel":       ["warm"],
    "silver":        ["cool"],
    "purple":        ["cool"],
    "burgundy":      ["cool"],
    "gunmetal":      ["cool"],
    "cool_grey":     ["cool"],
    "blue":          ["cool"],
    "deep_green":    ["cool"],
    # These appear in both cool and neutral best_colours lists
    "black":         ["cool", "neutral"],
    "navy":          ["cool", "neutral"],
    # Neutral-only colours
    "clear":         ["neutral"],
    "blush":         ["neutral"],
    "warm_grey":     ["neutral"],
}

# ── Face shape map ────────────────────────────────────────────────────────────
# Inverted from RECOMMENDATION_RULES.md FACE_SHAPE_RULES best_styles.

_STYLE_FACE_SHAPES: dict[str, list[str]] = {
    "rectangular": ["oval", "round"],
    "wayfarer":    ["oval", "round", "heart", "oblong"],
    "square":      ["oval", "round", "oblong"],
    "round":       ["square", "heart", "diamond", "oblong"],
    "aviator":     ["oval", "heart"],
    "browline":    ["oval", "round", "square", "diamond", "oblong"],
    "geometric":   ["round"],
    "oval":        ["square", "heart", "diamond"],
    "cat-eye":     ["square", "diamond"],
    "rimless":     ["square", "heart", "diamond"],
    "oversized":   ["oblong"],
}

# ── Vibe map ──────────────────────────────────────────────────────────────────

_STYLE_VIBES: dict[str, list[str]] = {
    "rectangular": ["professional", "classic"],
    "square":      ["bold", "professional"],
    "round":       ["retro", "minimal"],
    "oval":        ["minimal", "classic"],
    "cat-eye":     ["editorial", "bold"],
    "aviator":     ["classic", "sporty"],
    "wayfarer":    ["retro", "classic"],
    "browline":    ["retro", "classic"],
    "rimless":     ["minimal", "professional"],
    "geometric":   ["editorial", "bold"],
    "oversized":   ["bold", "editorial"],
}

# Brand-name vibes for secondary enrichment
_BRAND_VIBES: dict[str, list[str]] = {
    "vincent chase": ["minimal", "classic"],
    "john jacobs":   ["minimal", "professional"],
    "ray-ban":       ["classic", "sporty"],
    "titan":         ["classic", "professional"],
    "lenskart":      [],
}


def _brand_vibes(name: str) -> list[str]:
    lower = (name or "").lower()
    for brand, vibes in _BRAND_VIBES.items():
        if brand in lower:
            return vibes
    return []


def annotate_record(record: dict) -> dict:
    """
    Return a copy of record with face_shape_tags, undertone_tags, vibe_tags
    filled in from rules. Existing non-empty tags are preserved.
    """
    r = dict(record)
    style  = (r.get("style") or "").lower().strip()
    colour = (r.get("colour") or "").lower().strip()
    name   = r.get("name") or ""

    # undertone_tags
    if not r.get("undertone_tags"):
        r["undertone_tags"] = _COLOUR_UNDERTONE.get(colour, ["neutral"])

    # face_shape_tags
    if not r.get("face_shape_tags"):
        r["face_shape_tags"] = _STYLE_FACE_SHAPES.get(style, [])

    # vibe_tags: primary from style, supplement with brand if < 2 tags
    if not r.get("vibe_tags"):
        style_vibes = list(_STYLE_VIBES.get(style, []))
        brand_vibes = _brand_vibes(name)
        combined = style_vibes[:]
        for v in brand_vibes:
            if v not in combined:
                combined.append(v)
        r["vibe_tags"] = combined[:3]  # cap at 3

    return r


def auto_annotate_catalogue(records: list[dict]) -> list[dict]:
    """Annotate all records and return the updated list."""
    annotated = [annotate_record(r) for r in records]
    tagged   = sum(1 for r in annotated if r.get("face_shape_tags"))
    untagged = sum(1 for r in annotated if not r.get("face_shape_tags"))
    log.info(
        "Rule annotation: %d records tagged, %d have no style → empty face_shape_tags",
        tagged, untagged,
    )
    return annotated


def write_annotations_csv(records: list[dict], csv_path: Path) -> None:
    """Write annotation results to CSV (same format as the manual review tool)."""
    fieldnames = ["frame_id", "face_shape_tags", "undertone_tags", "vibe_tags", "notes"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "frame_id":       r["frame_id"],
                "face_shape_tags": ",".join(r.get("face_shape_tags") or []),
                "undertone_tags":  ",".join(r.get("undertone_tags") or []),
                "vibe_tags":       ",".join(r.get("vibe_tags") or []),
                "notes":           "auto",
            })
    log.info("Annotations written → %s (%d rows)", csv_path, len(records))


def run_auto_annotate(catalogue_path: Path, annotations_csv: Path) -> None:
    """
    Main entry point: load catalogue.json, annotate, overwrite in place,
    and also write annotations.csv so --merge still works.
    """
    if not catalogue_path.exists():
        log.error("catalogue.json not found: %s", catalogue_path)
        return

    records = json.loads(catalogue_path.read_text(encoding="utf-8"))
    log.info("Loaded %d records from %s", len(records), catalogue_path)

    annotated = auto_annotate_catalogue(records)

    catalogue_path.write_text(
        json.dumps(annotated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("catalogue.json updated in place")

    annotations_csv.parent.mkdir(parents=True, exist_ok=True)
    write_annotations_csv(annotated, annotations_csv)

    # Print summary
    style_counts: dict[str, int] = {}
    for r in annotated:
        for s in (r.get("face_shape_tags") or []):
            style_counts[s] = style_counts.get(s, 0) + 1

    log.info("Face shape tag counts: %s", style_counts)

    undertone_counts: dict[str, int] = {}
    for r in annotated:
        for u in (r.get("undertone_tags") or []):
            undertone_counts[u] = undertone_counts.get(u, 0) + 1

    log.info("Undertone tag counts: %s", undertone_counts)
