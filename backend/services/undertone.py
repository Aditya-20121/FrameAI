"""
Skin undertone analysis using OpenCV LAB colour space.

Samples pixels from forehead + left/right cheek regions using MediaPipe landmarks.
Classifies as Warm / Cool / Neutral based on LAB a* and b* channels, calibrated
to the Monk Skin Tone scale (10 points, good South Asian coverage).

LAB channel semantics:
  L*  = lightness (0–100)
  a*  = green (-128) → red (+127)   — higher = more pink/red
  b*  = blue (-128)  → yellow (+127) — higher = more warm/golden
"""
import math
from dataclasses import dataclass

import cv2
import numpy as np


UNDERTONE_EXPLANATIONS = {
    "warm": (
        "Your skin has warm golden or peachy undertones. "
        "Tortoiseshell, amber, brown, and gold frames will echo your natural warmth."
    ),
    "cool": (
        "Your skin has cool pink or rosy undertones. "
        "Black, silver, navy, and jewel-toned frames will complement your colouring."
    ),
    "neutral": (
        "Your skin has balanced undertones that sit between warm and cool. "
        "Most frame colours work for you — we've let your face shape lead the recommendations."
    ),
}

# LAB thresholds (empirically calibrated for South Asian skin diversity via Monk scale)
_WARM_B_MIN = 14.0    # b* > 14 → yellow-golden warmth
_WARM_A_MAX = 14.0    # a* < 14 → not excessively pink
_COOL_A_MIN = 11.0    # a* > 11 → pink/rosy
_COOL_B_MAX = 15.0    # b* < 15 → not golden

# MediaPipe landmark indices for sample regions
_LM_LEFT_CHEEK = 50
_LM_RIGHT_CHEEK = 280
_LM_FOREHEAD = 10
_LM_NOSE_TIP = 4     # excluded — often oily/highlighted

SAMPLE_RADIUS = 12    # pixels around each landmark to average


@dataclass
class UndertoneResult:
    undertone: str
    confidence: float
    hex_color: str


def _lab_sample(lab_image: np.ndarray, cx: int, cy: int, radius: int) -> np.ndarray | None:
    h, w = lab_image.shape[:2]
    x0 = max(0, cx - radius)
    x1 = min(w, cx + radius)
    y0 = max(0, cy - radius)
    y1 = min(h, cy + radius)
    region = lab_image[y0:y1, x0:x1]
    if region.size == 0:
        return None
    return region.mean(axis=(0, 1))  # shape (3,)


def _lab_to_hex(L: float, a: float, b: float) -> str:
    """Convert a single LAB pixel to an approximate RGB hex string."""
    lab_pixel = np.array([[[L, a, b]]], dtype=np.float32)
    rgb = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2RGB)
    r, g, b_val = (int(np.clip(c * 255, 0, 255)) for c in rgb[0, 0])
    return f"#{r:02X}{g:02X}{b_val:02X}"


def analyze_undertone(bgr: np.ndarray, landmarks) -> UndertoneResult:
    """
    Analyse skin undertone from a BGR image and MediaPipe landmarks.
    Returns UndertoneResult with classification, confidence, and hex swatch.
    """
    h, w = bgr.shape[:2]

    # OpenCV LAB: L in [0,255], a/b in [0,255] shifted from [-128,127]
    lab_image = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    # Rescale to standard LAB range
    lab_image[:, :, 0] = lab_image[:, :, 0] * (100.0 / 255.0)
    lab_image[:, :, 1] = lab_image[:, :, 1] - 128.0
    lab_image[:, :, 2] = lab_image[:, :, 2] - 128.0

    sample_landmarks = [_LM_LEFT_CHEEK, _LM_RIGHT_CHEEK, _LM_FOREHEAD]
    samples = []
    for idx in sample_landmarks:
        lm = landmarks[idx]
        cx, cy = int(lm.x * w), int(lm.y * h)
        s = _lab_sample(lab_image, cx, cy, SAMPLE_RADIUS)
        if s is not None:
            samples.append(s)

    if not samples:
        return UndertoneResult(undertone="neutral", confidence=0.5, hex_color="#C68642")

    avg = np.mean(samples, axis=0)
    L, a, b = float(avg[0]), float(avg[1]), float(avg[2])

    # Classification
    undertone, confidence = _classify(a, b)
    hex_color = _lab_to_hex(L, a + 128.0, b + 128.0)  # back to OpenCV range for conversion

    return UndertoneResult(
        undertone=undertone,
        confidence=confidence,
        hex_color=hex_color,
    )


def _classify(a: float, b: float) -> tuple[str, float]:
    warm_signal = max(0.0, b - _WARM_B_MIN) - max(0.0, a - _WARM_A_MAX)
    cool_signal = max(0.0, a - _COOL_A_MIN) - max(0.0, b - _COOL_B_MAX)

    if warm_signal > 0 and warm_signal >= cool_signal:
        # How far into warm territory?
        conf = min(0.95, 0.65 + warm_signal / 20.0)
        return "warm", round(conf, 2)
    if cool_signal > 0 and cool_signal > warm_signal:
        conf = min(0.95, 0.65 + cool_signal / 20.0)
        return "cool", round(conf, 2)
    return "neutral", 0.60
