"""
Face analysis pipeline — two-stage:

Stage 1 (free, local): MediaPipe face validation + landmark extraction → IPD/size_band
Stage 2 (AI):          Segmind Qwen3 VL Flash → face shape + undertone + explanations
                       ~$0.0001/analysis, ~2s response time

Falls back to geometric classification if Qwen3 VL Flash is unavailable.

InsightFace note: NOT used here. MediaPipe FaceDetection used for validation only.
"""
import base64
import io
import json
import math
import re
from dataclasses import dataclass

import cv2
import httpx
import numpy as np
import mediapipe as mp
from PIL import Image

from config import settings

# ── Landmark index constants ───────────────────────────────────────────────────
_LM_FOREHEAD_L   = 54;   _LM_FOREHEAD_R  = 284
_LM_CHEEK_L      = 234;  _LM_CHEEK_R     = 454
_LM_JAW_L        = 172;  _LM_JAW_R       = 397
_LM_FACE_TOP     = 10;   _LM_CHIN        = 152
_LM_LEFT_INNER   = 133;  _LM_RIGHT_INNER = 362

QWEN_ENDPOINT = "https://api.segmind.com/v1/qwen3-vl-flash"

ANALYSIS_PROMPT = """Look at this portrait photo and analyse the person's face.
Return ONLY a valid JSON object — no markdown fences, no extra text:

{
  "face_shape": "<oval|round|square|heart|diamond|oblong>",
  "face_shape_confidence": <float 0.0-1.0>,
  "face_shape_explanation": "<2-sentence plain English explanation referencing specific proportions visible in this photo>",
  "undertone": "<warm|cool|neutral>",
  "undertone_confidence": <float 0.0-1.0>,
  "undertone_hex": "<#RRGGBB approximation of the person's skin tone>"
}

Face shape definitions:
- oval: balanced proportions, slightly wider cheekbones, gentle taper at forehead and jaw
- round: nearly as wide as long, soft curves, full cheeks
- square: strong angular jaw, similar width from forehead to jaw
- heart: wide forehead, narrow pointed chin
- diamond: narrow forehead AND narrow jaw, wide prominent cheekbones
- oblong: significantly longer than wide, even proportions top to bottom

Undertone definitions:
- warm: golden, yellow, peachy, or olive tones
- cool: pink, rosy, reddish, or bluish-pink tones
- neutral: balanced beige, mix of warm and cool"""

FACE_SHAPE_EXPLANATIONS = {
    "oval": (
        "Your face has balanced proportions with slightly wider cheekbones tapering gently "
        "to the forehead and jaw — that's the Oval shape, the most versatile for frames."
    ),
    "round": (
        "Your face is nearly as wide as it is long, with soft curves all around — "
        "that's the Round shape. Angular frames will add great definition."
    ),
    "square": (
        "Your face has a strong jaw, wide forehead, and similar width throughout — "
        "that's the Square shape. Curved frames soften those angles beautifully."
    ),
    "heart": (
        "Your face is widest at the forehead and tapers to a narrow chin — "
        "that's the Heart shape. Bottom-weighted or rimless frames balance it perfectly."
    ),
    "diamond": (
        "Your face is widest at the cheekbones, with a narrower forehead and jawline — "
        "that's the Diamond shape. Frames with detail at the top balance your striking features."
    ),
    "oblong": (
        "Your face is noticeably longer than wide, with even proportions — "
        "that's the Oblong shape. Wide, oversized frames add beautiful horizontal presence."
    ),
}


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class FaceGeometry:
    forehead_width: float
    cheekbone_width: float
    jaw_width: float
    face_length: float
    ipd_px: float
    image_height_px: int

    @property
    def forehead_ratio(self) -> float:
        return self.forehead_width / self.cheekbone_width if self.cheekbone_width else 1.0

    @property
    def jaw_ratio(self) -> float:
        return self.jaw_width / self.cheekbone_width if self.cheekbone_width else 1.0

    @property
    def aspect_ratio(self) -> float:
        return self.face_length / self.cheekbone_width if self.cheekbone_width else 1.3


@dataclass
class AnalysisResult:
    face_shape: str
    face_shape_confidence: float
    face_shape_explanation: str
    undertone: str
    undertone_confidence: float
    undertone_hex: str
    ipd_mm: float
    size_band: str
    landmarks: list


# ── Image + face validation ────────────────────────────────────────────────────

MIN_RESOLUTION = 512
MIN_FACE_FRACTION = 0.25


def validate_image(image_bytes: bytes) -> np.ndarray:
    try:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise ValueError("unsupported_format")

    w, h = pil.size
    if w < MIN_RESOLUTION or h < MIN_RESOLUTION:
        raise ValueError("resolution_too_low")

    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 60:
        raise ValueError("image_too_blurry")

    return bgr


def validate_faces(bgr: np.ndarray) -> None:
    mp_fd = mp.solutions.face_detection
    h, w = bgr.shape[:2]
    image_area = h * w
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    with mp_fd.FaceDetection(model_selection=1, min_detection_confidence=0.4) as detector:
        results = detector.process(rgb)

    if not results.detections:
        raise ValueError("no_face_detected")
    if len(results.detections) > 1:
        raise ValueError("multiple_faces")

    bb = results.detections[0].location_data.relative_bounding_box
    if (bb.width * w) * (bb.height * h) / image_area < MIN_FACE_FRACTION:
        raise ValueError("face_too_small")


# ── Landmark extraction + IPD ──────────────────────────────────────────────────

def extract_landmarks(bgr: np.ndarray):
    mp_fm = mp.solutions.face_mesh
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    with mp_fm.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.4,
    ) as mesh:
        results = mesh.process(rgb)

    if not results.multi_face_landmarks:
        raise ValueError("no_face_detected")
    return results.multi_face_landmarks[0].landmark


def _dist(a, b, w: int, h: int) -> float:
    return math.hypot((a.x - b.x) * w, (a.y - b.y) * h)


def compute_geometry(landmarks, w: int, h: int) -> FaceGeometry:
    lm = landmarks
    return FaceGeometry(
        forehead_width  = _dist(lm[_LM_FOREHEAD_L], lm[_LM_FOREHEAD_R], w, h),
        cheekbone_width = _dist(lm[_LM_CHEEK_L],    lm[_LM_CHEEK_R],    w, h),
        jaw_width       = _dist(lm[_LM_JAW_L],       lm[_LM_JAW_R],      w, h),
        face_length     = _dist(lm[_LM_FACE_TOP],    lm[_LM_CHIN],       w, h),
        ipd_px          = _dist(lm[_LM_LEFT_INNER],  lm[_LM_RIGHT_INNER], w, h),
        image_height_px = h,
    )


def compute_ipd_mm(geometry: FaceGeometry) -> float:
    if geometry.cheekbone_width == 0:
        return 63.0
    return round(geometry.ipd_px / (geometry.cheekbone_width / 140.0), 1)


def get_size_band(ipd_mm: float) -> str:
    if ipd_mm < 60:   return "narrow"
    if ipd_mm <= 66:  return "standard"
    return "wide"


# ── Geometric fallback ─────────────────────────────────────────────────────────

def _classify_geometric(g: FaceGeometry) -> tuple[str, float]:
    scores = {
        "oval":    30 * (0.72 <= g.forehead_ratio <= 0.90) + 30 * (0.68 <= g.jaw_ratio <= 0.88) + 40 * (1.25 <= g.aspect_ratio <= 1.65),
        "round":   30 * (0.85 <= g.forehead_ratio <= 1.02) + 30 * (0.85 <= g.jaw_ratio <= 1.02) + 40 * (g.aspect_ratio < 1.22),
        "square":  25 * (0.85 <= g.forehead_ratio <= 1.02) + 35 * (0.88 <= g.jaw_ratio <= 1.05) + 40 * (1.05 <= g.aspect_ratio <= 1.40),
        "heart":   40 * (g.forehead_ratio >= 0.88) + 40 * (g.jaw_ratio <= 0.72) + 20 * (g.aspect_ratio >= 1.15),
        "diamond": 40 * (g.forehead_ratio <= 0.78) + 40 * (g.jaw_ratio <= 0.78) + 20 * (g.aspect_ratio >= 1.20),
        "oblong":  50 * (g.aspect_ratio >= 1.50) + 25 * (0.75 <= g.forehead_ratio <= 0.95) + 25 * (0.72 <= g.jaw_ratio <= 0.92),
    }
    best = max(scores, key=scores.__getitem__)
    return best, min(scores[best] / 100.0, 0.72)


# ── Qwen3 VL Flash vision analysis ────────────────────────────────────────────

def _image_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n': return "image/png"
    if image_bytes[:2] == b'\xff\xd8':           return "image/jpeg"
    return "image/webp"


async def _call_qwen_vision(image_bytes: bytes) -> dict:
    mime = _image_mime(image_bytes)
    img_b64 = base64.b64encode(image_bytes).decode()

    payload = {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                {"type": "text", "text": ANALYSIS_PROMPT},
            ],
        }]
    }
    headers = {"x-api-key": settings.segmind_api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(QWEN_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    # Strip markdown fences if present
    content = re.sub(r'```(?:json)?\s*|\s*```', '', content).strip()
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in Qwen3 response: {content[:200]}")
    return json.loads(match.group())


# ── Top-level entry point ──────────────────────────────────────────────────────

_VALID_SHAPES = {"oval", "round", "square", "heart", "diamond", "oblong"}
_VALID_TONES  = {"warm", "cool", "neutral"}


async def run_face_analysis(image_bytes: bytes) -> AnalysisResult:
    """
    Full pipeline — raises ValueError with error code on validation failures.

    Stage 1: MediaPipe → validate image, count faces, extract landmarks → IPD + size_band
    Stage 2: Qwen3 VL Flash → face shape + undertone + explanation
             Falls back to geometric rules if Qwen call fails.
    """
    bgr = validate_image(image_bytes)
    validate_faces(bgr)

    h, w = bgr.shape[:2]
    landmarks = extract_landmarks(bgr)
    geometry = compute_geometry(landmarks, w, h)
    ipd_mm = compute_ipd_mm(geometry)
    size_band = get_size_band(ipd_mm)

    # Defaults (used if Qwen fails)
    face_shape = "oval";  confidence = 0.80
    explanation = FACE_SHAPE_EXPLANATIONS["oval"]
    undertone = "neutral"; undertone_conf = 0.75; undertone_hex = "#C8956C"

    try:
        q = await _call_qwen_vision(image_bytes)

        fs = q.get("face_shape", "oval").lower().strip()
        ut = q.get("undertone", "neutral").lower().strip()

        face_shape     = fs if fs in _VALID_SHAPES else "oval"
        confidence     = float(q.get("face_shape_confidence", 0.85))
        explanation    = q.get("face_shape_explanation") or FACE_SHAPE_EXPLANATIONS[face_shape]
        undertone      = ut if ut in _VALID_TONES else "neutral"
        undertone_conf = float(q.get("undertone_confidence", 0.80))
        undertone_hex  = q.get("undertone_hex", "#C8956C")

    except Exception:
        face_shape, confidence = _classify_geometric(geometry)
        explanation = FACE_SHAPE_EXPLANATIONS[face_shape]

    return AnalysisResult(
        face_shape=face_shape,
        face_shape_confidence=round(confidence, 3),
        face_shape_explanation=explanation,
        undertone=undertone,
        undertone_confidence=round(undertone_conf, 3),
        undertone_hex=undertone_hex,
        ipd_mm=ipd_mm,
        size_band=size_band,
        landmarks=landmarks,
    )
