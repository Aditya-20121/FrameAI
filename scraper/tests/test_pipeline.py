"""
Unit tests for the scrape → normalise → annotate → dedupe pipeline
(pipeline/normalizer.py, pipeline/rule_annotator.py, pipeline/deduplicator.py).

No network, no Playwright, no real images: deduplicator's pHash step is
monkeypatched so grouping/preference logic is tested without real image
files.
"""
import numpy as np
import imagehash

from pipeline.normalizer import normalise, normalise_batch, _safe_int, _normalise_gender
from pipeline.rule_annotator import annotate_record, auto_annotate_catalogue
from pipeline import deduplicator


def _hash(all_true: bool) -> imagehash.ImageHash:
    """A real ImageHash so `h_i - h_j` (Hamming distance) behaves exactly as
    it does in production — non-negative and order-independent, unlike a
    plain int stand-in."""
    return imagehash.ImageHash(np.full((8, 8), all_true, dtype=bool))


# ── normalizer ────────────────────────────────────────────────────────────────

class TestNormalise:
    def test_valid_record_passes_through(self):
        raw = {
            "source": "lenskart", "source_id": "vc-123",
            "name": "Test Frame", "retailer": "Lenskart", "buy_url": "https://x.com/f",
        }
        record = normalise(raw)
        assert record is not None
        assert record["name"] == "Test Frame"
        assert record["retailer"] == "Lenskart"
        assert record["frame_id"]  # deterministic uuid5, always populated

    def test_missing_required_field_dropped(self):
        raw = {"source": "lenskart", "source_id": "vc-123", "name": "Test Frame"}  # no retailer/buy_url
        assert normalise(raw) is None

    def test_blank_required_field_dropped(self):
        raw = {"source": "lenskart", "source_id": "1", "name": "  ", "retailer": "Lenskart", "buy_url": "x"}
        assert normalise(raw) is None

    def test_same_source_and_id_gives_deterministic_frame_id(self):
        raw = {"source": "lenskart", "source_id": "vc-123", "name": "A", "retailer": "Lenskart", "buy_url": "x"}
        assert normalise(raw)["frame_id"] == normalise(raw)["frame_id"]

    def test_unmapped_style_left_null(self):
        raw = {"source": "s", "source_id": "1", "name": "A", "retailer": "R", "buy_url": "x", "style": "nonsense-style"}
        assert normalise(raw)["style"] is None

    def test_batch_drops_invalid_keeps_valid(self):
        raws = [
            {"source": "s", "source_id": "1", "name": "A", "retailer": "R", "buy_url": "x"},
            {"source": "s", "source_id": "2", "name": "", "retailer": "R", "buy_url": "x"},  # dropped
        ]
        result = normalise_batch(raws)
        assert len(result) == 1


class TestSafeInt:
    def test_plain_int_string(self):
        assert _safe_int("1999") == 1999

    def test_comma_formatted_price(self):
        assert _safe_int("1,999") == 1999

    def test_none_returns_none(self):
        assert _safe_int(None) is None

    def test_garbage_returns_none(self):
        assert _safe_int("not a number") is None


class TestNormaliseGender:
    def test_men(self):
        assert _normalise_gender("Men's Eyeglasses") == "men"

    def test_women(self):
        assert _normalise_gender("women") == "women"

    def test_female_maps_to_women(self):
        assert _normalise_gender("female") == "women"

    def test_unrecognised_defaults_unisex(self):
        assert _normalise_gender("kids") == "unisex"

    def test_none_defaults_unisex(self):
        assert _normalise_gender(None) == "unisex"


# ── rule_annotator ────────────────────────────────────────────────────────────

class TestAnnotateRecord:
    def test_undertone_tags_from_colour(self):
        record = {"style": "rectangular", "colour": "gold", "name": "Test"}
        annotated = annotate_record(record)
        assert annotated["undertone_tags"] == ["warm"]

    def test_unknown_colour_defaults_neutral(self):
        record = {"style": "rectangular", "colour": "unknown-shade", "name": "Test"}
        annotated = annotate_record(record)
        assert annotated["undertone_tags"] == ["neutral"]

    def test_face_shape_tags_inverted_from_style(self):
        record = {"style": "cat-eye", "colour": "black", "name": "Test"}
        annotated = annotate_record(record)
        assert set(annotated["face_shape_tags"]) == {"square", "diamond"}

    def test_unrecognised_style_gives_empty_face_shape_tags(self):
        record = {"style": "made-up-style", "colour": "black", "name": "Test"}
        annotated = annotate_record(record)
        assert annotated["face_shape_tags"] == []

    def test_existing_non_empty_tags_preserved(self):
        record = {"style": "round", "colour": "black", "name": "Test", "undertone_tags": ["custom"]}
        annotated = annotate_record(record)
        assert annotated["undertone_tags"] == ["custom"]

    def test_vibe_tags_capped_at_three(self):
        record = {"style": "rectangular", "colour": "black", "name": "Ray-Ban Classic"}
        annotated = annotate_record(record)
        assert len(annotated["vibe_tags"]) <= 3

    def test_batch_annotation_runs_on_all_records(self):
        records = [
            {"style": "round", "colour": "black", "name": "A"},
            {"style": "cat-eye", "colour": "gold", "name": "B"},
        ]
        annotated = auto_annotate_catalogue(records)
        assert len(annotated) == 2
        assert all("face_shape_tags" in r for r in annotated)


# ── deduplicator (pHash monkeypatched — no real images needed) ─────────────────

class TestDeduplicator:
    def _record(self, source_id, retailer="Lenskart", price=None, **extra):
        r = {"source_id": source_id, "retailer": retailer, "buy_url": f"https://x.com/{source_id}",
             "price_inr": price}
        r.update(extra)
        return r

    def test_no_duplicates_when_hashes_differ(self, monkeypatch):
        # Maximal Hamming distance (64 bits) — far past PHASH_THRESHOLD (10).
        fake_hashes = {"img_a.jpg": _hash(False), "img_b.jpg": _hash(True)}
        monkeypatch.setattr(deduplicator, "compute_phash", lambda path: fake_hashes[path])
        records = [self._record("a"), self._record("b")]
        image_paths = {"a": "img_a.jpg", "b": "img_b.jpg"}
        result = deduplicator.deduplicate_catalogue(records, image_paths)
        assert len(result) == 2

    def test_identical_hash_merges_to_one(self, monkeypatch):
        # Same hash for every path → every record is "the same image"
        monkeypatch.setattr(deduplicator, "compute_phash", lambda path: _hash(False))
        records = [self._record("a"), self._record("b"), self._record("c")]
        image_paths = {"a": "img.jpg", "b": "img.jpg", "c": "img.jpg"}
        result = deduplicator.deduplicate_catalogue(records, image_paths)
        assert len(result) == 1

    def test_more_complete_record_wins(self, monkeypatch):
        monkeypatch.setattr(deduplicator, "compute_phash", lambda path: _hash(False))
        sparse = self._record("a")
        complete = self._record("b", style="round", colour="black", material="acetate",
                                 lens_width_mm=50, bridge_width_mm=18, temple_length_mm=140,
                                 gender_tag="unisex")
        result = deduplicator.deduplicate_catalogue([sparse, complete], {"a": "img.jpg", "b": "img.jpg"})
        assert len(result) == 1
        assert result[0]["source_id"] == "b"

    def test_lower_price_wins_when_completeness_tied(self, monkeypatch):
        monkeypatch.setattr(deduplicator, "compute_phash", lambda path: _hash(False))
        cheap = self._record("a", price=1000)
        pricey = self._record("b", price=2000)
        result = deduplicator.deduplicate_catalogue([cheap, pricey], {"a": "img.jpg", "b": "img.jpg"})
        assert result[0]["source_id"] == "a"

    def test_records_without_images_kept_as_is(self, monkeypatch):
        monkeypatch.setattr(deduplicator, "compute_phash", lambda path: _hash(False))
        with_image = self._record("a")
        no_image = self._record("b")
        result = deduplicator.deduplicate_catalogue([with_image, no_image], {"a": "img.jpg"})
        assert len(result) == 2
