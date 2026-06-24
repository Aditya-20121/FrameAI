"""
Record normaliser: maps raw scraped fields to the DB schema.

All records must pass through this before being written to the catalogue JSON.
Drops records that cannot be mapped to the minimum required fields.
"""
import logging
import re
import uuid

from config import STYLE_MAP, COLOUR_MAP

log = logging.getLogger(__name__)

# Minimum required fields for a record to enter the DB
REQUIRED_FIELDS = ["name", "style", "colour", "retailer", "buy_url"]

VALID_STYLES = {
    "rectangular", "round", "oval", "square", "cat-eye",
    "aviator", "wayfarer", "browline", "geometric", "rimless", "oversized",
}

VALID_GENDERS = {"men", "women", "unisex"}


def normalise(raw: dict) -> dict | None:
    """
    Map a raw scraped record to the DB schema.
    Returns None if the record fails minimum quality checks.
    """
    record: dict = {}

    # source_id → deterministic frame_id
    source_id = str(raw.get("source_id") or "")
    source = str(raw.get("source") or "")
    record["frame_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}:{source_id}"))

    # Required text fields
    record["name"] = _clean(raw.get("name"))
    record["retailer"] = _clean(raw.get("retailer"))
    record["buy_url"] = _clean(raw.get("buy_url"))

    # Style
    raw_style = str(raw.get("style") or raw.get("raw_style") or "").lower().strip()
    record["style"] = STYLE_MAP.get(raw_style, raw_style if raw_style in VALID_STYLES else None)

    # Colour
    raw_colour = str(raw.get("colour") or raw.get("raw_colour") or "").lower().strip()
    record["colour"] = COLOUR_MAP.get(raw_colour, raw_colour if raw_colour else None)
    record["colour_hex"] = _clean(raw.get("colour_hex"))

    # Check minimum required fields
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            log.debug("Record %s dropped: missing %s", source_id, field)
            return None

    # Optional fields
    record["material"] = _clean(raw.get("material"))
    record["gender_tag"] = _normalise_gender(raw.get("gender_tag"))
    record["price_inr"] = _safe_int(raw.get("price_inr"))
    record["lens_width_mm"] = _safe_int(raw.get("lens_width_mm"))
    record["bridge_width_mm"] = _safe_int(raw.get("bridge_width_mm"))
    record["temple_length_mm"] = _safe_int(raw.get("temple_length_mm"))
    record["product_image_url"] = _clean(raw.get("product_image_url") or raw.get("image_url"))

    # Array fields — populated by manual annotation later
    record["face_shape_tags"] = raw.get("face_shape_tags") or []
    record["undertone_tags"] = raw.get("undertone_tags") or []
    record["vibe_tags"] = raw.get("vibe_tags") or []

    # Metadata
    record["scraped_at"] = raw.get("scraped_at")
    record["source"] = source
    record["source_id"] = source_id

    return record


def normalise_batch(raw_records: list[dict]) -> list[dict]:
    """Normalise a batch. Returns only valid records."""
    result = []
    dropped = 0
    for r in raw_records:
        norm = normalise(r)
        if norm:
            result.append(norm)
        else:
            dropped += 1
    log.info("Normalised %d records, dropped %d", len(result), dropped)
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        digits = re.sub(r"[^\d]", "", str(val))
        return int(digits) if digits else None


def _normalise_gender(val) -> str:
    v = str(val or "").lower().strip()
    if v in VALID_GENDERS:
        return v
    if "men" in v and "women" not in v:
        return "men"
    if "women" in v or "female" in v:
        return "women"
    return "unisex"
