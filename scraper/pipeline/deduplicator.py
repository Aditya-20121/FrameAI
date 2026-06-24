"""
Cross-source deduplication using perceptual image hashing.

Two frames are considered duplicates if their product images have a
perceptual hash (pHash) distance ≤ 10. This catches the same physical
frame appearing on both Lenskart and Titan Eye+.

For duplicates:
  - Keep the record with the most complete data
  - Prefer: more fields populated > lower price > Lenskart > JJ > Titan > Ray-Ban
  - Merge buy_url as a secondary URL on the surviving record
"""
import logging
from pathlib import Path

import imagehash
from PIL import Image

log = logging.getLogger(__name__)

PHASH_THRESHOLD = 10  # Hamming distance — frames with dist ≤ this are duplicates

# Retailer priority (lower = preferred)
RETAILER_PRIORITY = {
    "Lenskart": 1,
    "John Jacobs": 2,
    "Titan Eye+": 3,
    "Ray-Ban": 4,
}


def compute_phash(image_path: str) -> imagehash.ImageHash | None:
    try:
        return imagehash.phash(Image.open(image_path))
    except Exception as exc:
        log.debug("pHash failed for %s: %s", image_path, exc)
        return None


def _completeness_score(record: dict) -> int:
    """Count how many important fields are populated."""
    fields = ["style", "colour", "material", "lens_width_mm", "bridge_width_mm",
              "temple_length_mm", "gender_tag", "price_inr"]
    return sum(1 for f in fields if record.get(f) is not None)


def _preferred_record(a: dict, b: dict) -> tuple[dict, dict]:
    """Return (winner, loser) based on completeness + retailer priority."""
    score_a = _completeness_score(a)
    score_b = _completeness_score(b)
    if score_a != score_b:
        return (a, b) if score_a > score_b else (b, a)

    # Same completeness: compare price (lower = preferred)
    price_a = a.get("price_inr") or 9999999
    price_b = b.get("price_inr") or 9999999
    if price_a != price_b:
        return (a, b) if price_a <= price_b else (b, a)

    # Same price: prefer by retailer
    pri_a = RETAILER_PRIORITY.get(a.get("retailer", ""), 99)
    pri_b = RETAILER_PRIORITY.get(b.get("retailer", ""), 99)
    return (a, b) if pri_a <= pri_b else (b, a)


def deduplicate_catalogue(
    records: list[dict],
    image_paths: dict[str, str],  # {source_id: norm_image_path}
) -> list[dict]:
    """
    Deduplicate records using pHash. Returns a deduplicated list.
    Records without images are kept as-is (no image to compare).
    """
    # Build hash index for records that have images
    hash_index: list[tuple[imagehash.ImageHash, dict]] = []
    no_image: list[dict] = []

    for record in records:
        img = image_paths.get(record["source_id"])
        if not img:
            no_image.append(record)
            continue
        h = compute_phash(img)
        if h is None:
            no_image.append(record)
            continue
        hash_index.append((h, record))

    log.info("Deduplicating %d records with images + %d without...", len(hash_index), len(no_image))

    # Union-Find style deduplication
    n = len(hash_index)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            h_i, _ = hash_index[i]
            h_j, _ = hash_index[j]
            if (h_i - h_j) <= PHASH_THRESHOLD:
                union(i, j)

    # Group by root
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    # For each group, keep the best record, merge buy_urls
    survivors: list[dict] = []
    for indices in groups.values():
        if len(indices) == 1:
            survivors.append(dict(hash_index[indices[0]][1]))
            continue

        # Find the best among duplicates
        group_records = [dict(hash_index[i][1]) for i in indices]
        winner = group_records[0]
        losers = group_records[1:]
        for loser in losers:
            winner, _ = _preferred_record(winner, loser)

        # Merge alternate buy URLs
        alternate_urls = [
            r["buy_url"] for r in group_records
            if r["buy_url"] != winner.get("buy_url") and r.get("buy_url")
        ]
        if alternate_urls:
            winner["alternate_buy_urls"] = alternate_urls

        log.debug(
            "Dedup: merged %d records → kept %s (%s)",
            len(group_records),
            winner["source_id"],
            winner.get("retailer"),
        )
        survivors.append(winner)

    result = survivors + no_image
    log.info(
        "Deduplication complete: %d → %d records (removed %d duplicates)",
        len(records),
        len(result),
        len(records) - len(result),
    )
    return result
