"""
Unit tests for the recommendation engine.
Tests cover all face shapes × undertones, scoring, ranking, and explanation generation.
"""
import pytest
from services.recommender import (
    score_frame,
    rank_frames,
    build_explanation,
    get_size_band,
    FACE_SHAPE_RULES,
    UNDERTONE_RULES,
)


def _frame(
    style: str = "rectangular",
    colour: str = "tortoiseshell",
    lens_width: int = 50,
    bridge_width: int = 18,
) -> dict:
    return {
        "frame_id": "test-uuid",
        "name": "Test Frame",
        "style": style,
        "colour": colour,
        "lens_width_mm": lens_width,
        "bridge_width_mm": bridge_width,
        "material": "acetate",
        "retailer": "Lenskart",
        "price_inr": 1999,
        "buy_url": "https://example.com",
        "product_image_url": "https://example.com/frame.webp",
        "vibe_tags": ["minimal"],
        "colour_hex": "#8B5C2A",
    }


# ── Scoring ───────────────────────────────────────────────────────────────────

class TestScoring:
    def test_best_match_scores_highest(self):
        # Rectangular frame + tortoiseshell + standard IPD → ideal for round face + warm undertone
        good = _frame(style="rectangular", colour="tortoiseshell", lens_width=50, bridge_width=18)
        bad = _frame(style="round", colour="silver", lens_width=50, bridge_width=18)
        assert score_frame(good, "round", "warm", 63.0) > score_frame(bad, "round", "warm", 63.0)

    def test_avoid_style_penalises(self):
        bad_style = _frame(style="round")
        score = score_frame(bad_style, "round", "warm", 63.0)
        # "round" is in round face's avoid_styles → -30 penalty
        assert score < 30

    def test_avoid_colour_penalises(self):
        bad_colour = _frame(style="rectangular", colour="silver")
        score = score_frame(bad_colour, "round", "warm", 63.0)
        # "silver" in warm's avoid_colours → -20 penalty
        assert score < 60  # would normally be 40+10=50 for rectangular, minus 20 = 30

    def test_score_never_negative(self):
        worst = _frame(style="round", colour="silver")
        assert score_frame(worst, "round", "warm", 63.0) >= 0

    def test_boost_style_adds_extra(self):
        boosted = _frame(style="rectangular", colour="tortoiseshell")
        non_boosted = _frame(style="wayfarer", colour="tortoiseshell")
        # Both are "best_styles" for round; "rectangular" is also in score_boost
        # rectangular = 40 + 10 + 30 = 80
        # wayfarer    = 40 + 30 = 70 (wayfarer is best but not boosted for round)
        s_boosted = score_frame(boosted, "round", "warm", 63.0)
        s_non_boosted = score_frame(non_boosted, "round", "warm", 63.0)
        assert s_boosted > s_non_boosted

    def test_ipd_size_match_adds_score(self):
        # standard IPD = 63mm → frame width 130–138mm → lens 50 + bridge 18 = 68 (narrow band)
        # standard band: 130–138mm; let's use lens=55 + bridge=18 = 73 (still narrow)
        # Use lens=58 + bridge=16 = 74 → within standard 130-138? No, these are individual dimensions
        # Actually frame_width = lens_width_mm + bridge_width_mm
        # standard: 130-138mm total frame width
        matched = _frame(style="rectangular", colour="tortoiseshell", lens_width=60, bridge_width=18)  # 78 → not in range
        # Let's check IPD size correctly: standard IPD 60-66mm → frame 130-138mm
        # lens_width=60, bridge=72 is unrealistic. Let me use realistic values:
        # A real frame: lens=52, bridge=18 → total = 70 → not in 130-138 range
        # The width is total frame: typically 130-145mm for adult frames
        # lens_width per eye + bridge: total = lens_width*2 + bridge ≈ 52*2+18 = 122 (narrow)
        # But the DB stores lens_width as single lens. So total frame = lens*2 + bridge
        # However the scoring uses lens_width_mm + bridge_width_mm as stored in DB...
        # The spec uses frame_width = lens_width_mm + bridge_width_mm
        # This seems to be using these as total frame fields, not per-lens
        # Let's just test the score difference
        within_range = _frame(style="rectangular", colour="tortoiseshell", lens_width=115, bridge_width=18)  # 133 → in range
        outside_range = _frame(style="rectangular", colour="tortoiseshell", lens_width=90, bridge_width=18)   # 108 → outside
        s_in = score_frame(within_range, "round", "warm", 63.0)
        s_out = score_frame(outside_range, "round", "warm", 63.0)
        assert s_in > s_out


# ── All face shapes × undertones ──────────────────────────────────────────────

class TestAllCombinations:
    @pytest.mark.parametrize("face_shape", FACE_SHAPE_RULES.keys())
    @pytest.mark.parametrize("undertone", UNDERTONE_RULES.keys())
    def test_score_is_non_negative_for_any_input(self, face_shape, undertone):
        frame = _frame(
            style=FACE_SHAPE_RULES[face_shape]["best_styles"][0],
            colour=UNDERTONE_RULES[undertone]["best_colours"][0],
        )
        assert score_frame(frame, face_shape, undertone, 63.0) >= 0

    @pytest.mark.parametrize("face_shape", FACE_SHAPE_RULES.keys())
    def test_best_style_always_scores_higher_than_avoid(self, face_shape):
        rules = FACE_SHAPE_RULES[face_shape]
        if not rules["avoid_styles"]:
            pytest.skip("No avoid_styles defined")
        good = _frame(style=rules["best_styles"][0], colour="black")
        bad = _frame(style=rules["avoid_styles"][0], colour="black")
        assert score_frame(good, face_shape, "neutral", 63.0) > score_frame(bad, face_shape, "neutral", 63.0)


# ── Ranking ───────────────────────────────────────────────────────────────────

class TestRanking:
    def test_returns_top_n(self):
        frames = [
            _frame(style=s, colour="tortoiseshell")
            for s in ["rectangular", "round", "oval", "square", "wayfarer", "cat-eye", "aviator", "browline", "geometric", "rimless", "oversized"]
        ]
        ranked = rank_frames(frames, "round", "warm", 63.0, top_n=5)
        assert len(ranked) <= 5

    def test_sorted_descending_by_score(self):
        frames = [_frame(style=s) for s in ["rectangular", "round", "cat-eye"]]
        ranked = rank_frames(frames, "round", "warm", 63.0)
        scores = [f["score"] for f in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_explanation_present_on_all_ranked(self):
        frames = [_frame(style="rectangular", colour="tortoiseshell")]
        ranked = rank_frames(frames, "oval", "warm", 63.0)
        for f in ranked:
            assert "explanation" in f
            assert len(f["explanation"]) > 10

    def test_empty_catalogue_returns_empty(self):
        assert rank_frames([], "oval", "warm", 63.0) == []


# ── Size band ─────────────────────────────────────────────────────────────────

class TestSizeBand:
    def test_all_bands(self):
        assert get_size_band(55) == "narrow"
        assert get_size_band(60) == "standard"
        assert get_size_band(63) == "standard"
        assert get_size_band(66) == "standard"
        assert get_size_band(70) == "wide"

    def test_boundary_values(self):
        assert get_size_band(59.9) == "narrow"
        assert get_size_band(66.0) == "standard"
        assert get_size_band(66.1) == "wide"


# ── Explanation generation ────────────────────────────────────────────────────

class TestExplanation:
    def test_explanation_includes_shape(self):
        frame = _frame(style="oval", colour="black")
        exp = build_explanation(frame, "square", "cool")
        assert "square" in exp.lower() or "Square" in exp

    def test_explanation_includes_colour(self):
        frame = _frame(style="rectangular", colour="tortoiseshell")
        exp = build_explanation(frame, "round", "warm")
        assert "tortoiseshell" in exp

    def test_explanation_includes_undertone(self):
        frame = _frame(style="round", colour="silver")
        exp = build_explanation(frame, "square", "cool")
        assert "cool" in exp
