"""
Unit tests for the recommendation engine (services/recommender.py — v2,
colour-family scoring system). Covers all face shapes, the colour-family
scoring table, ranking/dedup/diversity, and explanation generation.
"""
import pytest
from services.recommender import (
    score_frame,
    rank_frames,
    build_explanation,
    get_size_band,
    get_colour_score,
    get_feature_modifier,
    FACE_SHAPE_RULES,
    COLOUR_FAMILY,
    IPD_SIZE_RULES,
)


def _frame(
    style: str = "rectangular",
    colour: str = "tortoiseshell",
    lens_width: int = 60,
    bridge_width: int = 18,
    name: str = "Test Frame",
) -> dict:
    return {
        "frame_id": "test-uuid",
        "name": name,
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


# ── Colour scoring ───────────────────────────────────────────────────────────

class TestColourScoring:
    def test_warm_undertone_prefers_warm_earth(self):
        assert get_colour_score("tortoiseshell", "warm", None) == 30

    def test_cool_undertone_penalises_warm_earth(self):
        assert get_colour_score("tortoiseshell", "cool", None) == 0

    def test_cool_undertone_prefers_cool_neutral(self):
        assert get_colour_score("black", "cool", None) == 30

    def test_unknown_colour_gets_low_default(self):
        assert get_colour_score("neon-pink", "warm", None) == 5

    def test_score_never_negative(self):
        # warm_bold on cool undertone is -10 base, must clamp to 0
        assert get_colour_score("amber", "cool", None) == 0

    def test_score_capped_at_30(self):
        for colour in COLOUR_FAMILY:
            for undertone in ("warm", "cool", "neutral"):
                assert 0.0 <= get_colour_score(colour, undertone, None) <= 30.0

    def test_deep_skin_boosts_cool_jewel(self):
        base = get_colour_score("navy", "cool", None)
        deep = get_colour_score("navy", "cool", "deep")
        assert deep > base

    def test_fair_skin_boosts_universal(self):
        base = get_colour_score("clear", "warm", None)
        fair = get_colour_score("clear", "warm", "fair")
        assert fair == base + 4


# ── Face shape rules — all 6 branches ──────────────────────────────────────────

class TestAllFaceShapes:
    @pytest.mark.parametrize("face_shape", FACE_SHAPE_RULES.keys())
    def test_best_style_scores_higher_than_avoid_style(self, face_shape):
        rules = FACE_SHAPE_RULES[face_shape]
        if not rules["avoid_styles"]:
            pytest.skip(f"{face_shape} has no avoid_styles defined")
        good = _frame(style=rules["best_styles"][0], colour="black")
        bad = _frame(style=rules["avoid_styles"][0], colour="black")
        assert score_frame(good, face_shape, "neutral", 63.0) > score_frame(bad, face_shape, "neutral", 63.0)

    @pytest.mark.parametrize("face_shape", FACE_SHAPE_RULES.keys())
    def test_boosted_style_scores_higher_than_plain_best_style(self, face_shape):
        rules = FACE_SHAPE_RULES[face_shape]
        boosted_styles = [s for s in rules["best_styles"] if s in rules["score_boost"]]
        plain_styles = [s for s in rules["best_styles"] if s not in rules["score_boost"]]
        if not boosted_styles or not plain_styles:
            pytest.skip(f"{face_shape} has no boosted/plain split to compare")
        boosted = _frame(style=boosted_styles[0], colour="black")
        plain = _frame(style=plain_styles[0], colour="black")
        assert score_frame(boosted, face_shape, "neutral", 63.0) > score_frame(plain, face_shape, "neutral", 63.0)

    @pytest.mark.parametrize("face_shape", FACE_SHAPE_RULES.keys())
    def test_score_never_negative_for_any_shape(self, face_shape):
        worst_style = FACE_SHAPE_RULES[face_shape]["avoid_styles"]
        style = worst_style[0] if worst_style else "unknown-style"
        frame = _frame(style=style, colour="amber")  # bad colour too
        assert score_frame(frame, face_shape, "cool", 63.0) >= 0.0


# ── Feature modifier ──────────────────────────────────────────────────────────

class TestFeatureModifier:
    def test_angular_jaw_softening_style_bonus(self):
        assert get_feature_modifier("round", "angular", None, None) == 2

    def test_soft_jaw_defining_style_bonus(self):
        assert get_feature_modifier("square", "soft", None, None) == 2

    def test_high_cheekbones_cat_eye_bonus(self):
        assert get_feature_modifier("cat-eye", None, "high", None) == 2

    def test_close_eyes_wide_style_bonus(self):
        assert get_feature_modifier("square", None, None, "close") == 1

    def test_bonus_capped_at_5(self):
        # Stack every possible bonus on one style — must still clamp to 5
        bonus = get_feature_modifier("square", "soft", "low", "close")
        assert bonus <= 5.0

    def test_no_signals_gives_zero_bonus(self):
        assert get_feature_modifier("rectangular", None, None, None) == 0.0


# ── score_frame integration ────────────────────────────────────────────────────

class TestScoreFrame:
    def test_ideal_frame_scores_higher_than_bad_frame(self):
        good = _frame(style="rectangular", colour="tortoiseshell")
        bad = _frame(style="round", colour="black")  # "round" is round-face avoid_style
        assert score_frame(good, "round", "warm", 63.0) > score_frame(bad, "round", "warm", 63.0)

    def test_frame_width_in_range_adds_points(self):
        # standard band (IPD 63mm) → frame width 130-138mm
        in_range = _frame(style="rectangular", colour="tortoiseshell", lens_width=115, bridge_width=18)  # 133
        out_of_range = _frame(style="rectangular", colour="tortoiseshell", lens_width=90, bridge_width=18)  # 108
        assert score_frame(in_range, "oval", "warm", 63.0) > score_frame(out_of_range, "oval", "warm", 63.0)

    def test_score_floor_is_zero(self):
        worst = _frame(style="round", colour="amber")  # avoid_style + clashing colour on cool
        assert score_frame(worst, "round", "cool", 63.0) >= 0.0


# ── Size band ─────────────────────────────────────────────────────────────────

class TestSizeBand:
    def test_narrow_band(self):
        assert get_size_band(55.0) == "narrow"

    def test_standard_lower_boundary(self):
        assert get_size_band(60.0) == "standard"

    def test_standard_upper_boundary(self):
        assert get_size_band(66.0) == "standard"

    def test_wide_band(self):
        assert get_size_band(67.0) == "wide"

    def test_all_bands_have_frame_width_ranges(self):
        for band in ("narrow", "standard", "wide"):
            assert band in IPD_SIZE_RULES


# ── Ranking / dedup / diversity ─────────────────────────────────────────────────

class TestRankFrames:
    def test_returns_at_most_top_n(self):
        frames = [_frame(style=s, colour="tortoiseshell", name=f"F{i}")
                  for i, s in enumerate(["rectangular", "round", "square", "wayfarer",
                                          "cat-eye", "aviator", "browline", "geometric", "rimless"])]
        ranked = rank_frames(frames, "round", "warm", 63.0, top_n=5)
        assert len(ranked) <= 5

    def test_sorted_descending_by_score(self):
        frames = [_frame(style=s, name=f"F{i}") for i, s in enumerate(["rectangular", "round", "cat-eye"])]
        ranked = rank_frames(frames, "round", "warm", 63.0)
        scores = [f["score"] for f in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_explanation_present_on_every_ranked_frame(self):
        frames = [_frame(style="rectangular", colour="tortoiseshell")]
        ranked = rank_frames(frames, "oval", "warm", 63.0)
        for f in ranked:
            assert "explanation" in f and len(f["explanation"]) > 10

    def test_empty_catalogue_returns_empty(self):
        assert rank_frames([], "oval", "warm", 63.0) == []

    def test_duplicate_name_colour_pair_deduplicated(self):
        frames = [
            _frame(style="rectangular", colour="tortoiseshell", name="Same Frame"),
            _frame(style="rectangular", colour="tortoiseshell", name="Same Frame"),
            _frame(style="wayfarer", colour="black", name="Different Frame"),
        ]
        ranked = rank_frames(frames, "oval", "warm", 63.0, top_n=10)
        keys = [(f["name"].lower(), f["colour"].lower()) for f in ranked]
        assert len(keys) == len(set(keys))

    def test_style_diversity_cap_applied(self):
        # 3 rectangular (boosted, scores highest) + 1 each of 6 other oval-friendly
        # styles (unboosted) → enough non-dominant supply that the cap actually
        # binds instead of being defeated by the overflow-padding fallback.
        # top_n=6 → max_per_style = max(2, 6//3) = 2
        frames = [_frame(style="rectangular", colour="tortoiseshell", name=f"Rect{i}") for i in range(3)]
        frames += [
            _frame(style=s, colour="tortoiseshell", name=s)
            for s in ["square", "round", "aviator", "browline", "cat-eye", "geometric"]
        ]
        ranked = rank_frames(frames, "oval", "warm", 63.0, top_n=6)
        rectangular_count = sum(1 for f in ranked if f["style"] == "rectangular")
        assert rectangular_count == 2  # capped, third rectangular pushed to overflow


# ── Explanation generation ────────────────────────────────────────────────────

class TestBuildExplanation:
    def test_mentions_face_shape(self):
        frame = _frame(style="rectangular", colour="black")
        exp = build_explanation(frame, "square", "cool")
        assert "square" in exp.lower()

    def test_mentions_colour(self):
        frame = _frame(style="rectangular", colour="tortoiseshell")
        exp = build_explanation(frame, "round", "warm")
        assert "tortoiseshell" in exp.lower()

    def test_mentions_style(self):
        frame = _frame(style="cat-eye", colour="black")
        exp = build_explanation(frame, "square", "cool")
        assert "cat-eye" in exp.lower()
