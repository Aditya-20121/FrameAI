"""
Unit tests for face shape classification and IPD calculation.
Tests cover all 6 face shape rule branches and edge cases.
"""
import pytest
from services.face_analysis import (
    FaceGeometry,
    classify_face_shape,
    compute_ipd_mm,
    get_size_band,
    CONFIDENCE_THRESHOLD,
)


def _geometry(
    forehead: float,
    cheekbone: float,
    jaw: float,
    length: float,
    ipd_px: float = 80.0,
    height: int = 600,
) -> FaceGeometry:
    return FaceGeometry(
        forehead_width=forehead,
        cheekbone_width=cheekbone,
        jaw_width=jaw,
        face_length=length,
        ipd_px=ipd_px,
        image_height_px=height,
    )


# ── Face shape classification ─────────────────────────────────────────────────

class TestOvalClassification:
    def test_classic_oval(self):
        g = _geometry(forehead=130, cheekbone=150, jaw=120, length=200)
        result = classify_face_shape(g)
        assert result.shape == "oval"

    def test_oval_ratios(self):
        # forehead_ratio ~0.80, jaw_ratio ~0.77, aspect ~1.43
        g = _geometry(forehead=160, cheekbone=200, jaw=154, length=286)
        result = classify_face_shape(g)
        assert result.shape == "oval"

    def test_oval_explanation_populated(self):
        g = _geometry(forehead=130, cheekbone=150, jaw=120, length=200)
        result = classify_face_shape(g)
        assert len(result.explanation) > 20


class TestRoundClassification:
    def test_classic_round(self):
        # All widths similar, face not very long
        g = _geometry(forehead=145, cheekbone=150, jaw=143, length=180)
        result = classify_face_shape(g)
        assert result.shape == "round"

    def test_round_low_aspect_ratio(self):
        g = _geometry(forehead=148, cheekbone=155, jaw=150, length=170)
        result = classify_face_shape(g)
        assert result.shape == "round"


class TestSquareClassification:
    def test_classic_square(self):
        # Wide jaw similar to forehead + cheek, moderate length
        g = _geometry(forehead=155, cheekbone=160, jaw=158, length=200)
        result = classify_face_shape(g)
        assert result.shape == "square"


class TestHeartClassification:
    def test_classic_heart(self):
        # Wide forehead, narrow jaw
        g = _geometry(forehead=170, cheekbone=180, jaw=110, length=210)
        result = classify_face_shape(g)
        assert result.shape == "heart"

    def test_heart_extreme_taper(self):
        g = _geometry(forehead=175, cheekbone=185, jaw=100, length=225)
        result = classify_face_shape(g)
        assert result.shape == "heart"


class TestDiamondClassification:
    def test_classic_diamond(self):
        # Narrow forehead AND jaw, wide cheekbones
        g = _geometry(forehead=130, cheekbone=185, jaw=125, length=230)
        result = classify_face_shape(g)
        assert result.shape == "diamond"


class TestOblongClassification:
    def test_classic_oblong(self):
        # Long face, relatively even widths
        g = _geometry(forehead=145, cheekbone=155, jaw=140, length=260)
        result = classify_face_shape(g)
        assert result.shape == "oblong"

    def test_oblong_high_aspect_ratio(self):
        g = _geometry(forehead=140, cheekbone=150, jaw=138, length=250)
        result = classify_face_shape(g)
        assert result.shape == "oblong"


# ── Confidence ────────────────────────────────────────────────────────────────

class TestConfidence:
    def test_confidence_between_0_and_1(self):
        for g in [
            _geometry(130, 150, 120, 200),
            _geometry(145, 150, 143, 180),
            _geometry(170, 180, 110, 210),
        ]:
            result = classify_face_shape(g)
            assert 0.0 <= result.confidence <= 1.0

    def test_clear_shape_has_higher_confidence(self):
        # Extreme heart face — wide forehead, very narrow jaw
        g = _geometry(forehead=190, cheekbone=195, jaw=90, length=230)
        result = classify_face_shape(g)
        assert result.shape == "heart"
        assert result.confidence >= 0.70


# ── IPD + size band ───────────────────────────────────────────────────────────

class TestIPD:
    def test_narrow_band(self):
        assert get_size_band(55.0) == "narrow"

    def test_standard_band_lower(self):
        assert get_size_band(60.0) == "standard"

    def test_standard_band_upper(self):
        assert get_size_band(66.0) == "standard"

    def test_wide_band(self):
        assert get_size_band(68.0) == "wide"

    def test_boundary_exactly_60(self):
        assert get_size_band(60.0) == "standard"

    def test_boundary_exactly_67(self):
        assert get_size_band(67.0) == "wide"

    def test_ipd_mm_estimation_returns_positive(self):
        g = _geometry(130, 150, 120, 200, ipd_px=70.0)
        ipd = compute_ipd_mm(g)
        assert ipd > 0

    def test_ipd_zero_cheekbone_returns_default(self):
        g = _geometry(0, 0, 0, 0, ipd_px=0.0)
        ipd = compute_ipd_mm(g)
        assert ipd == 63.0  # safe default
