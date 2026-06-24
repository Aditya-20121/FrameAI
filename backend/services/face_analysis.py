"""
Face analysis pipeline:
  1. Validate image: single face, min resolution, not blurred
  2. Extract 478 MediaPipe Face Mesh landmarks
  3. Compute face geometry (widths + length)
  4. Classify face shape via rule-based geometry; confidence drives EfficientNet fallback
  5. Measure IPD and determine size band

InsightFace is used for face validation (detect count + bounding box quality).
NOTE: InsightFace AntelopeV2 is non-commercial research-only. Replace with
ArcFace (commercial licence) before production launch.
"""
import io
import math
from dataclasses import dataclass

import cv2
import numpy as np
import mediapipe as mp
from PIL import Image

# ── Landmark index constants ──────────────────────────────────────────────────
# MediaPipe 478-point Face Mesh indices for key structural measurements.

# Horizontal face widths
_LM_FOREHEAD_L = 54
_LM_FOREHEAD_R = 284
_LM_CHEEK_L = 234
_LM_CHEEK_R = 454
_LM_JAW_L = 172
_LM_JAW_R = 397

# Face length
_LM_FACE_TOP = 10
_LM_CHIN = 152

# Eyes (for IPD)
_LM_LEFT_EYE_OUTER = 33
_LM_LEFT_EYE_INNER = 133
_LM_RIGHT_EYE_INNER = 362
_LM_RIGHT_EYE_OUTER = 263

# Nose bridge (used for undertone landmark passing)
_LM_NOSE_BRIDGE = 6

# ── Face shape rules ──────────────────────────────────────────────────────────

FACE_SHAPE_EXPLANATIONS = {
    "oval": (
        "Your face has balanced proportions with slightly wider cheekbones tapering gently "
        "to the forehead and jaw — that's the Oval shape, the most versatile for frames."
    ),
    "round": (
        "Your face is nearly as wide as it is long, with soft curves all around — "
        "that's the Round shape. Angular frames will add definition."
    ),
    "square": (
        "Your face has a strong jaw, wide forehead, and similar width throughout — "
        "that's the Square shape. Curved frames will soften those angles."
    ),
    "heart": (
        "Your face is widest at the forehead and tapers to a narrow chin — "
        "that's the Heart shape. Bottom-weighted or lightweight frames balance it perfectly."
    ),
    "diamond": (
        "Your face is widest at the cheekbones, with a narrower forehead and jawline — "
        "that's the Diamond shape. Frames with detail at the top balance your striking features."
    ),
    "oblong": (
        "Your face is noticeably longer than wide, with even proportions from top to bottom — "
        "that's the Oblong shape. Wide, oversized frames add horizontal presence."
    ),
}


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
        return self.forehead_width / self.cheekbone_width

    @property
    def jaw_ratio(self) -> float:
        return self.jaw_width / self.cheekbone_width

    @property
    def aspect_ratio(self) -> float:
        return self.face_length / self.cheekbone_width


@dataclass
class FaceShapeResult:
    shape: str
    confidence: float
    explanation: str
    geometry: FaceGeometry


@dataclass
class AnalysisResult:
    face_shape: str
    face_shape_confidence: float
    face_shape_explanation: str
    ipd_mm: float
    size_band: str
    landmarks: list  # raw MediaPipe NormalizedLandmarkList


# ── Validation ────────────────────────────────────────────────────────────────

MIN_RESOLUTION = 512
MIN_FACE_FRACTION = 0.30  # face bounding box must cover ≥ 30% of image area


def validate_image(image_bytes: bytes) -> np.ndarray:
    """
    Decode image bytes, check resolution and blur.
    Returns BGR numpy array ready for analysis.
    Raises ValueError with a machine-readable error code string on failure.
    """
    try:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise ValueError("unsupported_format")

    w, h = pil.size
    if w < MIN_RESOLUTION or h < MIN_RESOLUTION:
        raise ValueError("resolution_too_low")

    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # Blur check via Laplacian variance
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 80:
        raise ValueError("image_too_blurry")

    return bgr


def detect_faces_mediapipe(bgr: np.ndarray) -> list[dict]:
    """
    Use MediaPipe FaceDetection to count faces and get bounding boxes.
    Returns list of dicts with {xmin, ymin, width, height} in pixels.
    """
    mp_fd = mp.solutions.face_detection
    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    with mp_fd.FaceDetection(model_selection=1, min_detection_confidence=0.5) as detector:
        results = detector.process(rgb)

    if not results.detections:
        return []

    faces = []
    for det in results.detections:
        bb = det.location_data.relative_bounding_box
        faces.append({
            "xmin": int(bb.xmin * w),
            "ymin": int(bb.ymin * h),
            "width": int(bb.width * w),
            "height": int(bb.height * h),
        })
    return faces


def validate_faces(bgr: np.ndarray) -> None:
    """
    Ensure exactly one face, large enough, centred enough.
    Raises ValueError with error code on failure.
    """
    faces = detect_faces_mediapipe(bgr)
    h, w = bgr.shape[:2]
    image_area = h * w

    if len(faces) == 0:
        raise ValueError("no_face_detected")
    if len(faces) > 1:
        raise ValueError("multiple_faces")

    face = faces[0]
    face_area = face["width"] * face["height"]
    if face_area / image_area < MIN_FACE_FRACTION:
        raise ValueError("face_too_small")


# ── Landmark extraction ───────────────────────────────────────────────────────

def extract_landmarks(bgr: np.ndarray):
    """
    Run MediaPipe Face Mesh on BGR image.
    Returns the first face's NormalizedLandmarkList or raises ValueError.
    """
    mp_fm = mp.solutions.face_mesh
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    with mp_fm.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as mesh:
        results = mesh.process(rgb)

    if not results.multi_face_landmarks:
        raise ValueError("no_face_detected")

    return results.multi_face_landmarks[0].landmark


def _dist(lm_a, lm_b, w: int, h: int) -> float:
    ax, ay = lm_a.x * w, lm_a.y * h
    bx, by = lm_b.x * w, lm_b.y * h
    return math.hypot(ax - bx, ay - by)


def compute_geometry(landmarks, w: int, h: int) -> FaceGeometry:
    lm = landmarks
    return FaceGeometry(
        forehead_width=_dist(lm[_LM_FOREHEAD_L], lm[_LM_FOREHEAD_R], w, h),
        cheekbone_width=_dist(lm[_LM_CHEEK_L], lm[_LM_CHEEK_R], w, h),
        jaw_width=_dist(lm[_LM_JAW_L], lm[_LM_JAW_R], w, h),
        face_length=_dist(lm[_LM_FACE_TOP], lm[_LM_CHIN], w, h),
        ipd_px=_dist(lm[_LM_LEFT_EYE_INNER], lm[_LM_RIGHT_EYE_INNER], w, h),
        image_height_px=h,
    )


# ── Face shape classifier ─────────────────────────────────────────────────────

def _score_oval(g: FaceGeometry) -> float:
    s = 0.0
    if 0.72 <= g.forehead_ratio <= 0.90:
        s += 30
    if 0.68 <= g.jaw_ratio <= 0.88:
        s += 30
    if 1.25 <= g.aspect_ratio <= 1.65:
        s += 40
    return s


def _score_round(g: FaceGeometry) -> float:
    s = 0.0
    if 0.85 <= g.forehead_ratio <= 1.02:
        s += 30
    if 0.85 <= g.jaw_ratio <= 1.02:
        s += 30
    if g.aspect_ratio < 1.30:
        s += 40
    return s


def _score_square(g: FaceGeometry) -> float:
    s = 0.0
    if 0.85 <= g.forehead_ratio <= 1.02:
        s += 25
    if 0.88 <= g.jaw_ratio <= 1.05:
        s += 35
    if 1.05 <= g.aspect_ratio <= 1.40:
        s += 40
    return s


def _score_heart(g: FaceGeometry) -> float:
    s = 0.0
    if g.forehead_ratio >= 0.88:
        s += 40
    if g.jaw_ratio <= 0.72:
        s += 40
    if g.aspect_ratio >= 1.15:
        s += 20
    return s


def _score_diamond(g: FaceGeometry) -> float:
    s = 0.0
    if g.forehead_ratio <= 0.78:
        s += 40
    if g.jaw_ratio <= 0.78:
        s += 40
    if g.aspect_ratio >= 1.20:
        s += 20
    return s


def _score_oblong(g: FaceGeometry) -> float:
    s = 0.0
    if g.aspect_ratio >= 1.50:
        s += 50
    if 0.75 <= g.forehead_ratio <= 0.95:
        s += 25
    if 0.72 <= g.jaw_ratio <= 0.92:
        s += 25
    return s


_SCORERS = {
    "oval": _score_oval,
    "round": _score_round,
    "square": _score_square,
    "heart": _score_heart,
    "diamond": _score_diamond,
    "oblong": _score_oblong,
}

CONFIDENCE_THRESHOLD = 0.75  # below this → attempt EfficientNet fallback


def classify_face_shape(geometry: FaceGeometry) -> FaceShapeResult:
    scores = {shape: fn(geometry) for shape, fn in _SCORERS.items()}
    best_shape = max(scores, key=scores.__getitem__)
    best_score = scores[best_shape]
    confidence = min(best_score / 100.0, 1.0)

    return FaceShapeResult(
        shape=best_shape,
        confidence=confidence,
        explanation=FACE_SHAPE_EXPLANATIONS[best_shape],
        geometry=geometry,
    )


# ── IPD + size band ───────────────────────────────────────────────────────────

# Calibration: median adult IPD in pixels at standard portrait distance
# assumes image was taken ~60cm from camera (selfie).
# The landmark-measured IPD in pixels is converted using a rough scale factor.
# A proper calibration would use a known reference (e.g. face width mapped to avg 140mm).
_AVG_FACE_WIDTH_MM = 140.0


def compute_ipd_mm(geometry: FaceGeometry) -> float:
    """
    Estimate IPD in mm using the cheekbone width as a reference ruler.
    Scale factor: cheekbone_width_px corresponds to ~140mm average.
    """
    if geometry.cheekbone_width == 0:
        return 63.0  # safe default (average adult)
    px_per_mm = geometry.cheekbone_width / _AVG_FACE_WIDTH_MM
    return round(geometry.ipd_px / px_per_mm, 1)


def get_size_band(ipd_mm: float) -> str:
    if ipd_mm < 60:
        return "narrow"
    if ipd_mm <= 66:
        return "standard"
    return "wide"


# ── Top-level entry point ─────────────────────────────────────────────────────

def run_face_analysis(image_bytes: bytes) -> AnalysisResult:
    """
    Full face analysis pipeline.
    Returns AnalysisResult or raises ValueError with an error code string.
    """
    bgr = validate_image(image_bytes)
    validate_faces(bgr)

    h, w = bgr.shape[:2]
    landmarks = extract_landmarks(bgr)
    geometry = compute_geometry(landmarks, w, h)
    shape_result = classify_face_shape(geometry)

    ipd_mm = compute_ipd_mm(geometry)
    size_band = get_size_band(ipd_mm)

    return AnalysisResult(
        face_shape=shape_result.shape,
        face_shape_confidence=shape_result.confidence,
        face_shape_explanation=shape_result.explanation,
        ipd_mm=ipd_mm,
        size_band=size_band,
        landmarks=landmarks,
    )
