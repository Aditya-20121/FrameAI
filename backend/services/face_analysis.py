"""
Face analysis pipeline — pure vision AI.

Stage 1 (local):  Basic image validation (resolution, blur, face presence via Haar cascade)
Stage 2 (cloud):  Segmind Gemini 2.5 Flash Lite → face shape, undertone, features

No MediaPipe. No geometric math. The VLM handles all face shape reasoning.
~$0.00011 per call (543 tokens avg at Gemini 2.5 Flash Lite rates).
"""
import base64
import io
import json
import re
from dataclasses import dataclass

import cv2
import httpx
import numpy as np
from PIL import Image

from config import settings

GEMINI_ENDPOINT = "https://api.segmind.com/v1/gemini-2.5-flash-lite"

ANALYSIS_PROMPT = """Look at this portrait photo and analyse the person's face using professional optometry standards.
Return ONLY a valid JSON object — no markdown fences, no extra text:

{
  "face_shape": "<nuanced display label — e.g. 'Oval', 'Oval (leaning towards Square)', 'Square (strong jaw, slightly rounded)', 'Round', 'Heart (wide forehead)', 'Diamond', 'Oblong' — be specific about the nuance, do not restrict to one word if the face sits between two categories>",
  "face_shape_primary": "<oval|round|square|heart|diamond|oblong — the single closest primary category>",
  "face_shape_confidence": <float 0.0-1.0>,
  "face_shape_explanation": "<ONE sentence, plain English, referencing specific proportions visible in this photo>",
  "jawline": "<angular|soft|tapered>",
  "cheekbones": "<high|normal|low>",
  "eye_set": "<close|average|wide>",
  "undertone": "<warm|cool|neutral>",
  "undertone_confidence": <float 0.0-1.0>,
  "undertone_hex": "<#RRGGBB approximation of the person's skin tone>",
  "skin_depth": "<fair|light|medium|olive|deep>",
  "size_band": "<narrow|standard|wide — estimate frame size needed based on the distance between the inner eye corners relative to the total face width: narrow if eyes are close-set, wide if eyes are far apart, standard otherwise>"
}

Face shape definitions:
- oval: balanced proportions, slightly wider cheekbones, gentle taper at forehead and jaw
- round: nearly as wide as long, soft curves, full cheeks, short face height
- square: strong angular jaw corners clearly visible from the front, similar width from forehead to jaw
- heart: wide forehead, narrow pointed chin, jaw significantly narrower than forehead
- diamond: narrow forehead AND narrow jaw, wide prominent cheekbones are the widest point
- oblong: significantly longer than wide, relatively even proportions from forehead to jaw

If a face clearly sits between two categories, use a compound label in "face_shape" (e.g. "Oval (leaning towards Square)") but still pick the single best match for "face_shape_primary".

Jawline definitions — look at the jaw corners when viewed straight on:
- angular: jaw corners are visibly wide and form distinct right angles; the jaw maintains lateral width before dropping to the chin — structured, defined look typical of square or strong oval faces
- soft: jaw curves smoothly with no distinct corners; blends gradually from cheek to chin with no visible angles — rounded and gentle, typical of round faces
- tapered: jaw gradually narrows in a V-shape toward the chin; no distinct lateral corners, just a gradual inward slope — typical of heart, diamond, or oval faces

Cheekbone definitions:
- high: prominent, visible bone structure clearly above the midface
- normal: average prominence, not a defining feature
- low: cheekbones sit at or below the midface, not prominent

Eye set definitions:
- close: eyes appear close to the nose bridge, narrow inner canthal distance
- average: balanced, standard spacing between the eyes
- wide: noticeable gap between the eyes relative to face width

Skin undertone (constant — does not change with sun exposure):
- warm: golden, yellow, peachy, or olive base tones visible in the skin
- cool: pink, rosy, reddish, or bluish-pink base tones visible in the skin
- neutral: balanced beige — an even mix of warm and cool, no dominant cast

Skin depth:
- fair: very light, minimal melanin — pale or porcelain
- light: light skin with slightly more pigmentation than fair
- medium: middle range — golden to light brown tones
- olive: medium depth with a yellow-green cast
- deep: rich, high melanin — from brown to deep brown"""

FACE_SHAPE_EXPLANATIONS = {
    "oval":    "Your face has balanced proportions with slightly wider cheekbones tapering gently to the forehead and jaw — the most versatile shape for frames.",
    "round":   "Your face is nearly as wide as it is long, with soft curves all around — angular frames will add great definition.",
    "square":  "Your face has a strong jaw, wide forehead, and similar width throughout — curved frames soften those angles beautifully.",
    "heart":   "Your face is widest at the forehead and tapers to a narrow chin — bottom-weighted or rimless frames balance it perfectly.",
    "diamond": "Your face is widest at the cheekbones, with a narrower forehead and jawline — frames with detail at the top balance your striking features.",
    "oblong":  "Your face is noticeably longer than wide, with even proportions — wide, oversized frames add beautiful horizontal presence.",
}


@dataclass
class AnalysisResult:
    face_shape: str        # primary enum: oval | round | square | heart | diamond | oblong
    face_shape_label: str  # nuanced display label: "Oval (leaning towards Square)"
    face_shape_confidence: float
    face_shape_explanation: str
    jawline: str
    cheekbones: str
    eye_set: str
    undertone: str
    undertone_confidence: float
    undertone_hex: str
    skin_depth: str
    ipd_mm: float
    size_band: str
    landmarks: list


# ── Image + face validation ────────────────────────────────────────────────────

MIN_RESOLUTION  = 512
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
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(80, 80))

    if len(faces) == 0:
        raise ValueError("no_face_detected")

    h, w = bgr.shape[:2]
    significant = [(x, y, fw, fh) for (x, y, fw, fh) in faces
                   if (fw * fh) / (w * h) >= MIN_FACE_FRACTION]
    if len(significant) > 1:
        raise ValueError("multiple_faces")


# ── Gemini 2.5 Flash Lite vision analysis ─────────────────────────────────────

def _image_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n': return "image/png"
    if image_bytes[:2] == b'\xff\xd8':           return "image/jpeg"
    return "image/webp"


async def _call_gemini_vision(image_bytes: bytes) -> dict:
    mime   = _image_mime(image_bytes)
    img_b64 = base64.b64encode(image_bytes).decode()

    payload = {
        "messages": {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": ANALYSIS_PROMPT},
                        {"inlineData": {"mimeType": mime, "data": img_b64}},
                    ],
                }
            ]
        }
    }
    headers = {"x-api-key": settings.segmind_api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GEMINI_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()

    # Gemini response: candidates[0].content.parts[0].text
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    # Strip markdown fences if the model wraps the JSON anyway
    text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in Gemini response: {text[:200]}")
    return json.loads(match.group())


# ── Valid value sets ───────────────────────────────────────────────────────────

_VALID_SHAPES     = {"oval", "round", "square", "heart", "diamond", "oblong"}
_VALID_TONES      = {"warm", "cool", "neutral"}
_VALID_JAWLINES   = {"angular", "soft", "tapered"}
_VALID_CHEEKBONES = {"high", "normal", "low"}
_VALID_EYE_SET    = {"close", "average", "wide"}
_VALID_SKIN_DEPTH = {"fair", "light", "medium", "olive", "deep"}


def _extract_primary_shape(label: str) -> str:
    """Extract the primary shape enum from a nuanced label like 'Oval (leaning towards Square)'.
    Takes the leftmost matching shape word — the primary shape is always named first in the label.
    Uses word boundaries so 'round' does not match inside 'rounded'."""
    import re
    lower = label.lower()
    best_pos   = len(lower) + 1
    best_shape = "oval"
    for shape in _VALID_SHAPES:
        m = re.search(r"\b" + shape + r"\b", lower)
        if m and m.start() < best_pos:
            best_pos   = m.start()
            best_shape = shape
    return best_shape


# ── Top-level entry point ──────────────────────────────────────────────────────

async def run_face_analysis(image_bytes: bytes) -> AnalysisResult:
    """
    Full pipeline:
    Stage 1 — local image decode (resolution + blur check already done by validate_image)
    Stage 2 — Gemini 2.5 Flash Lite VLM → face shape, undertone, features

    Raises on failure so the caller can return a proper 500 to the client.
    """
    q = await _call_gemini_vision(image_bytes)

    # face_shape is the nuanced display label ("Oval (leaning towards Square)")
    # face_shape_primary is the strict enum for DB/logic ("oval")
    face_shape_label = q.get("face_shape", "").strip()
    fs_primary       = q.get("face_shape_primary", "").lower().strip()
    face_shape       = fs_primary if fs_primary in _VALID_SHAPES else _extract_primary_shape(face_shape_label)

    # Normalise label casing — capitalise first word, preserve the rest
    if face_shape_label:
        face_shape_label = face_shape_label[0].upper() + face_shape_label[1:]
    else:
        face_shape_label = face_shape.capitalize()

    ut = q.get("undertone",  "").lower().strip()
    jl = q.get("jawline",    "").lower().strip()
    cb = q.get("cheekbones", "").lower().strip()
    es = q.get("eye_set",    "").lower().strip()
    sd = q.get("skin_depth", "").lower().strip()
    sb = q.get("size_band",  "").lower().strip()

    undertone      = ut if ut in _VALID_TONES      else "neutral"
    jawline        = jl if jl in _VALID_JAWLINES   else "soft"
    cheekbones     = cb if cb in _VALID_CHEEKBONES else "normal"
    eye_set        = es if es in _VALID_EYE_SET    else "average"
    skin_depth     = sd if sd in _VALID_SKIN_DEPTH else "medium"
    size_band      = sb if sb in {"narrow", "standard", "wide"} else "standard"

    confidence     = float(q.get("face_shape_confidence", 0.85))
    explanation    = q.get("face_shape_explanation") or FACE_SHAPE_EXPLANATIONS[face_shape]
    undertone_conf = float(q.get("undertone_confidence", 0.80))
    undertone_hex  = q.get("undertone_hex", "#C8956C")

    return AnalysisResult(
        face_shape=face_shape,
        face_shape_label=face_shape_label,
        face_shape_confidence=round(confidence, 3),
        face_shape_explanation=explanation,
        jawline=jawline,
        cheekbones=cheekbones,
        eye_set=eye_set,
        undertone=undertone,
        undertone_confidence=round(undertone_conf, 3),
        undertone_hex=undertone_hex,
        skin_depth=skin_depth,
        ipd_mm=0.0,     # not computed — retained only for DB schema compat
        size_band=size_band,
        landmarks=[],
    )
