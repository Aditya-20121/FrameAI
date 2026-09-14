"""
Unit tests for services/face_analysis.py against the current Gemini-VLM
pipeline (no MediaPipe, no geometric math — see the module docstring).

Covers the parts that don't require a real network call:
  - local image validation (resolution, blur, face count)
  - primary-shape label parsing
  - response normalisation / fallback-default rule branches in run_face_analysis
    (the Gemini call itself is monkeypatched — see TestRunFaceAnalysis)
"""
from pathlib import Path

import pytest
from PIL import Image
import io

from services.face_analysis import (
    validate_image,
    validate_faces,
    _extract_primary_shape,
    run_face_analysis,
    AnalysisResult,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _solid_image_bytes(size: tuple[int, int], color=(128, 128, 128)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


# ── validate_image ───────────────────────────────────────────────────────────

class TestValidateImage:
    def test_valid_real_photo_passes(self):
        data = (FIXTURES / "face.jpg").read_bytes()
        bgr, resized = validate_image(data)
        assert bgr.shape[0] >= 512 and bgr.shape[1] >= 512
        assert len(resized) > 0

    def test_too_small_resolution_rejected(self):
        data = _solid_image_bytes((300, 300))
        with pytest.raises(ValueError, match="resolution_too_low"):
            validate_image(data)

    def test_unsupported_format_rejected(self):
        with pytest.raises(ValueError, match="unsupported_format"):
            validate_image(b"not an image")

    def test_blurry_flat_colour_rejected(self):
        # A perfectly flat colour image has zero Laplacian variance — blurriest possible input.
        data = _solid_image_bytes((600, 600))
        with pytest.raises(ValueError, match="image_too_blurry"):
            validate_image(data)

    def test_oversized_image_is_downscaled(self):
        data = _solid_image_bytes((3000, 2000))
        # Flat colour still trips the blur check, so use a noisy image to get past it
        import numpy as np
        arr = (np.random.rand(2000, 3000, 3) * 255).astype("uint8")
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="JPEG")
        bgr, _ = validate_image(buf.getvalue())
        assert max(bgr.shape[0], bgr.shape[1]) <= 1600  # MAX_DIMENSION


# ── validate_faces ────────────────────────────────────────────────────────────

class TestValidateFaces:
    def test_real_face_detected(self):
        data = (FIXTURES / "face.jpg").read_bytes()
        bgr, _ = validate_image(data)
        validate_faces(bgr)  # should not raise

    def test_no_face_in_blank_image(self):
        import numpy as np
        arr = (np.random.rand(600, 600, 3) * 255).astype("uint8")
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="JPEG")
        bgr, _ = validate_image(buf.getvalue())
        with pytest.raises(ValueError, match="no_face_detected"):
            validate_faces(bgr)


# ── _extract_primary_shape ─────────────────────────────────────────────────────

class TestExtractPrimaryShape:
    def test_single_word_label(self):
        assert _extract_primary_shape("Oval") == "oval"

    def test_compound_label_takes_leftmost(self):
        assert _extract_primary_shape("Oval (leaning towards Square)") == "oval"

    def test_second_shape_named_first(self):
        assert _extract_primary_shape("Square (strong jaw, slightly rounded)") == "square"

    def test_word_boundary_avoids_partial_match(self):
        # "round" must not match inside "rounded" per the word-boundary regex
        assert _extract_primary_shape("Square (slightly rounded edges)") == "square"

    def test_unrecognised_label_falls_back_to_oval(self):
        assert _extract_primary_shape("Mysterious Face Shape") == "oval"


# ── run_face_analysis (Gemini call monkeypatched) ──────────────────────────────

FULL_RESPONSE = {
    "face_shape": "Heart (wide forehead)",
    "face_shape_primary": "heart",
    "face_shape_confidence": 0.91,
    "face_shape_explanation": "Wide forehead tapering to a narrow chin.",
    "jawline": "tapered",
    "cheekbones": "high",
    "eye_set": "wide",
    "undertone": "cool",
    "undertone_confidence": 0.77,
    "undertone_hex": "#E8C4A0",
    "skin_depth": "fair",
    "size_band": "wide",
}


class TestRunFaceAnalysis:
    async def test_full_valid_response_mapped_through(self, monkeypatch):
        async def fake_call(image_bytes, distinct_id="unknown"):
            return dict(FULL_RESPONSE)

        monkeypatch.setattr("services.face_analysis._call_gemini_vision", fake_call)
        result = await run_face_analysis(b"fake-bytes")

        assert isinstance(result, AnalysisResult)
        assert result.face_shape == "heart"
        assert result.face_shape_label == "Heart (wide forehead)"
        assert result.face_shape_confidence == 0.91
        assert result.jawline == "tapered"
        assert result.cheekbones == "high"
        assert result.eye_set == "wide"
        assert result.undertone == "cool"
        assert result.undertone_confidence == 0.77
        assert result.undertone_hex == "#E8C4A0"
        assert result.skin_depth == "fair"
        assert result.size_band == "wide"

    async def test_missing_primary_shape_derived_from_label(self, monkeypatch):
        async def fake_call(image_bytes, distinct_id="unknown"):
            q = dict(FULL_RESPONSE)
            q["face_shape_primary"] = ""  # force fallback to label parsing
            q["face_shape"] = "Diamond (strong cheekbones)"
            return q

        monkeypatch.setattr("services.face_analysis._call_gemini_vision", fake_call)
        result = await run_face_analysis(b"fake-bytes")
        assert result.face_shape == "diamond"

    @pytest.mark.parametrize(
        "field,bad_value,expected_default",
        [
            ("undertone", "greenish", "neutral"),
            ("jawline", "chiselled", "soft"),
            ("cheekbones", "extreme", "normal"),
            ("eye_set", "huge", "average"),
            ("skin_depth", "bronze", "medium"),
            ("size_band", "gigantic", "standard"),
        ],
    )
    async def test_invalid_enum_values_fall_back_to_default(self, monkeypatch, field, bad_value, expected_default):
        async def fake_call(image_bytes, distinct_id="unknown"):
            q = dict(FULL_RESPONSE)
            q[field] = bad_value
            return q

        monkeypatch.setattr("services.face_analysis._call_gemini_vision", fake_call)
        result = await run_face_analysis(b"fake-bytes")
        assert getattr(result, field) == expected_default

    async def test_missing_confidence_defaults_applied(self, monkeypatch):
        async def fake_call(image_bytes, distinct_id="unknown"):
            q = dict(FULL_RESPONSE)
            del q["face_shape_confidence"]
            del q["undertone_confidence"]
            del q["undertone_hex"]
            return q

        monkeypatch.setattr("services.face_analysis._call_gemini_vision", fake_call)
        result = await run_face_analysis(b"fake-bytes")
        assert result.face_shape_confidence == 0.85
        assert result.undertone_confidence == 0.80
        assert result.undertone_hex == "#C8956C"

    async def test_ipd_mm_is_not_computed(self, monkeypatch):
        async def fake_call(image_bytes, distinct_id="unknown"):
            return dict(FULL_RESPONSE)

        monkeypatch.setattr("services.face_analysis._call_gemini_vision", fake_call)
        result = await run_face_analysis(b"fake-bytes")
        assert result.ipd_mm == 0.0  # retained only for DB schema compat, per module comment
