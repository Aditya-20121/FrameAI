"""
Auto-annotation pipeline.

Two tasks:
  1. CLIP style classifier  — predict frame style from product image
  2. Dominant colour extractor — K-means on non-white pixels → hex → colour name

CLIP model is loaded once and reused across the batch.
Requires: torch, transformers, scikit-learn
"""
import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from config import CLIP_STYLE_LABELS, COLOUR_CENTROIDS, COLOUR_MAP, STYLE_MAP

log = logging.getLogger(__name__)


# ── CLIP style classifier ─────────────────────────────────────────────────────

_clip_model = None
_clip_processor = None


def _load_clip():
    global _clip_model, _clip_processor
    if _clip_model is None:
        log.info("Loading CLIP model (first call)...")
        from transformers import CLIPProcessor, CLIPModel
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _clip_model.eval()
        log.info("CLIP model loaded.")
    return _clip_model, _clip_processor


def classify_style_clip(image_path: str) -> tuple[str, float]:
    """
    Classify eyeglass style using CLIP zero-shot classification.
    Returns (style_name, confidence) where style_name matches our schema.
    """
    import torch

    model, processor = _load_clip()
    image = Image.open(image_path).convert("RGB")

    inputs = processor(
        text=CLIP_STYLE_LABELS,
        images=image,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = outputs.logits_per_image.softmax(dim=1)[0]
    best_idx = int(probs.argmax())
    raw_label = CLIP_STYLE_LABELS[best_idx]
    confidence = float(probs[best_idx])

    # Map "rectangular eyeglasses frame" → "rectangular"
    style = raw_label.split(" eyeglasses")[0].strip()
    return style, round(confidence, 3)


# ── Dominant colour extractor ─────────────────────────────────────────────────

def extract_dominant_colour(image_path: str, n_clusters: int = 3) -> tuple[str, str]:
    """
    Extract dominant non-white colour from a normalised product image.
    Returns (colour_name, hex_string) using K-means clustering.
    """
    from sklearn.cluster import KMeans

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).reshape(-1, 3).astype(float)

    # Mask out near-white background pixels
    white_dist = np.sqrt(np.sum((arr - 255) ** 2, axis=1))
    foreground = arr[white_dist > 50]

    if len(foreground) < 100:
        return "black", "#000000"

    k = min(n_clusters, len(foreground))
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    kmeans.fit(foreground)

    # Pick the cluster with the most pixels that is furthest from white
    centres = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = np.bincount(labels)

    # Score each cluster: weight by count, penalise white-ish centres
    scores = []
    for i, centre in enumerate(centres):
        white_d = np.sqrt(np.sum((centre - 255) ** 2))
        scores.append(counts[i] * min(white_d / 50.0, 1.0))

    best = int(np.argmax(scores))
    dominant_rgb = centres[best].astype(int)
    hex_colour = "#{:02X}{:02X}{:02X}".format(*dominant_rgb)

    colour_name = _rgb_to_colour_name(tuple(dominant_rgb))
    return colour_name, hex_colour


def _rgb_to_colour_name(rgb: tuple[int, int, int]) -> str:
    """Map an RGB value to the nearest named colour from COLOUR_CENTROIDS."""
    best_name = "black"
    best_dist = float("inf")

    for name, centroid in COLOUR_CENTROIDS.items():
        dist = math.sqrt(
            (rgb[0] - centroid[0]) ** 2
            + (rgb[1] - centroid[1]) ** 2
            + (rgb[2] - centroid[2]) ** 2
        )
        if dist < best_dist:
            best_dist = dist
            best_name = name

    return best_name


# ── Normaliser pipeline ───────────────────────────────────────────────────────

def extract_style_from_url(image_url: str) -> str | None:
    """
    Extract frame style from the product image URL filename.
    Lenskart filenames contain the shape, e.g.:
      '...full-rim-rectangle-vincent-chase...jpg'  → 'rectangular'
    """
    if not image_url:
        return None
    fname = image_url.split("/")[-1].lower()
    for kw, style in STYLE_MAP.items():
        if kw in fname:
            return style
    return None


def normalise_record(raw: dict, image_path: str | None = None) -> dict:
    """
    Apply all normalisation to a raw scraped record:
      - Normalise style and colour strings using maps
      - If style still unknown, try extracting from image URL filename
      - If style/colour still unknown and image_path given, use CLIP + colour extractor
    """
    record = dict(raw)

    # Style normalisation
    raw_style = str(record.get("raw_style") or "").lower().strip()
    record["style"] = STYLE_MAP.get(raw_style)

    # Fallback: scan image URL filename AND product URL for shape keywords.
    # Lenskart image filenames embed shape (e.g. '...full-rim-rectangle-...').
    # Some product buy_urls also contain the shape as part of the slug.
    if not record["style"]:
        for url_field in ("product_image_url", "image_url", "buy_url", "product_url"):
            url_style = extract_style_from_url(record.get(url_field) or "")
            if url_style:
                record["style"] = url_style
                log.debug(
                    "URL-extracted style for %s from %s: %s",
                    record.get("source_id"), url_field, url_style,
                )
                break

    # If style unknown and we have an image, try CLIP
    if not record["style"] and image_path:
        try:
            style, conf = classify_style_clip(image_path)
            record["style"] = style
            record["clip_style_confidence"] = conf
            log.debug("CLIP style for %s: %s (%.2f)", record["source_id"], style, conf)
        except Exception as exc:
            log.debug("CLIP failed for %s: %s", record.get("source_id"), exc)

    # Colour normalisation: try exact match first, then substring scan for
    # compound values like "black gold" or "blue gunmetal".
    raw_colour = str(record.get("raw_colour") or "").lower().strip()
    colour = COLOUR_MAP.get(raw_colour)
    if not colour and raw_colour:
        for kw, mapped in COLOUR_MAP.items():
            if kw in raw_colour:
                colour = mapped
                break
    # Fall back to whatever the normaliser already set
    if not colour:
        colour = record.get("colour")
    record["colour"] = colour

    # If colour unknown and we have an image, extract dominant
    if not record["colour"] and image_path:
        try:
            colour_name, hex_colour = extract_dominant_colour(image_path)
            record["colour"] = colour_name
            record["colour_hex"] = hex_colour
            log.debug("Extracted colour for %s: %s %s", record["source_id"], colour_name, hex_colour)
        except Exception as exc:
            log.debug("Colour extract failed for %s: %s", record.get("source_id"), exc)
    elif not record.get("colour_hex") and image_path:
        try:
            _, hex_colour = extract_dominant_colour(image_path)
            record["colour_hex"] = hex_colour
        except Exception:
            pass

    return record


def annotate_batch(
    records: list[dict],
    image_paths: dict[str, str],  # {source_id: norm_image_path}
) -> list[dict]:
    """
    Annotate a batch of records. Uses CLIP only for records missing style/colour.
    """
    annotated = []
    for r in records:
        img = image_paths.get(r["source_id"])
        annotated.append(normalise_record(r, img))
    return annotated
