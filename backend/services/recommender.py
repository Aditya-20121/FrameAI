"""
Frame recommendation engine — Sprint 2.

Implements the scoring algorithm from RECOMMENDATION_RULES.md exactly.
Pure Python, fully deterministic, fully unit-testable.
"""
from dataclasses import dataclass

# ── Rule tables ───────────────────────────────────────────────────────────────

FACE_SHAPE_RULES: dict[str, dict] = {
    "oval": {
        "best_styles": ["rectangular", "wayfarer", "square", "round", "aviator", "browline"],
        "avoid_styles": ["oversized", "novelty"],
        "score_boost": ["rectangular", "wayfarer"],
        "explanation": (
            "Oval faces have balanced proportions — almost any style works. "
            "We've prioritised frames that add definition without overwhelming your features."
        ),
    },
    "round": {
        "best_styles": ["rectangular", "square", "wayfarer", "browline", "geometric"],
        "avoid_styles": ["round", "oval", "small"],
        "score_boost": ["rectangular", "square"],
        "explanation": (
            "Angular frames create contrast against a round face, making it appear "
            "longer and more defined. We've avoided round styles that echo your face shape."
        ),
    },
    "square": {
        "best_styles": ["round", "oval", "cat-eye", "rimless", "browline"],
        "avoid_styles": ["square", "rectangular", "geometric"],
        "score_boost": ["round", "oval", "cat-eye"],
        "explanation": (
            "Curved frames soften your strong angular features. "
            "Thin frames work better than heavy acetate for your face shape."
        ),
    },
    "heart": {
        "best_styles": ["round", "oval", "rimless", "aviator", "wayfarer"],
        "avoid_styles": ["cat-eye", "browline", "oversized"],
        "score_boost": ["round", "oval", "rimless"],
        "explanation": (
            "Lighter frames draw attention downward, balancing your wider forehead "
            "with your narrower chin. We've avoided top-heavy styles."
        ),
    },
    "diamond": {
        "best_styles": ["oval", "cat-eye", "browline", "rimless", "round"],
        "avoid_styles": ["rectangular", "narrow", "small"],
        "score_boost": ["oval", "cat-eye", "browline"],
        "explanation": (
            "Frames with width or detail at the top balance your prominent cheekbones "
            "and draw attention to your forehead and eyes."
        ),
    },
    "oblong": {
        "best_styles": ["round", "square", "wayfarer", "oversized", "browline"],
        "avoid_styles": ["narrow", "small", "rimless"],
        "score_boost": ["round", "wayfarer", "oversized"],
        "explanation": (
            "Wide frames add perceived width and break your face's vertical length. "
            "We've prioritised frames with strong horizontal presence."
        ),
    },
}

UNDERTONE_RULES: dict[str, dict] = {
    "warm": {
        "best_colours": [
            "tortoiseshell", "amber", "brown", "olive", "gold", "rose_gold",
            "tan", "honey", "cognac", "caramel",
        ],
        "avoid_colours": ["silver", "grey", "cool_black"],
        "hardware_preference": "gold",
        "explanation": (
            "Your warm undertone is complemented by earthy, golden tones. "
            "We've matched frames that echo the warmth in your skin."
        ),
    },
    "cool": {
        "best_colours": [
            "black", "silver", "navy", "purple", "burgundy", "gunmetal",
            "cool_grey", "blue", "deep_green",
        ],
        "avoid_colours": ["orange", "warm_brown", "gold", "amber"],
        "hardware_preference": "silver",
        "explanation": (
            "Your cool undertone pairs well with crisp, jewel-toned frames. "
            "Silver hardware over gold brings out your natural colouring."
        ),
    },
    "neutral": {
        "best_colours": [
            "black", "tortoiseshell", "clear", "blush", "warm_grey",
            "navy", "brown", "rose_gold",
        ],
        "avoid_colours": [],
        "hardware_preference": "any",
        "explanation": (
            "Your neutral undertone is versatile — most palettes work. "
            "We've used your face shape as the primary filter and added colour variety."
        ),
    },
}

IPD_SIZE_RULES: dict[str, dict] = {
    "narrow":   {"range": (0, 59),    "frame_width_mm": (125, 130)},
    "standard": {"range": (60, 66),   "frame_width_mm": (130, 138)},
    "wide":     {"range": (67, 9999), "frame_width_mm": (138, 148)},
}


# ── Scoring ───────────────────────────────────────────────────────────────────

def get_size_band(ipd_mm: float) -> str:
    if ipd_mm < 60:
        return "narrow"
    if ipd_mm <= 66:
        return "standard"
    return "wide"


def score_frame(frame: dict, face_shape: str, undertone: str, ipd_mm: float) -> float:
    score = 0.0

    shape_rules = FACE_SHAPE_RULES.get(face_shape, {})
    colour_rules = UNDERTONE_RULES.get(undertone, {})
    size_band = get_size_band(ipd_mm)
    min_w, max_w = IPD_SIZE_RULES[size_band]["frame_width_mm"]

    # 1. Face shape (40 pts + 10 bonus)
    style = frame.get("style", "")
    if style in shape_rules.get("best_styles", []):
        score += 40
    if style in shape_rules.get("score_boost", []):
        score += 10
    if style in shape_rules.get("avoid_styles", []):
        score -= 30

    # 2. Undertone colour (30 pts)
    colour = frame.get("colour", "")
    if colour in colour_rules.get("best_colours", []):
        score += 30
    if colour in colour_rules.get("avoid_colours", []):
        score -= 20

    # 3. IPD size (20 pts)
    frame_width = (frame.get("lens_width_mm") or 0) + (frame.get("bridge_width_mm") or 0)
    if frame_width and min_w <= frame_width <= max_w:
        score += 20
    elif frame_width and abs(frame_width - (min_w + max_w) / 2) <= 5:
        score += 10

    return max(score, 0.0)


def build_explanation(frame: dict, face_shape: str, undertone: str) -> str:
    style = frame.get("style", "frame")
    colour = frame.get("colour", "colour")
    shape_reason = FACE_SHAPE_RULES.get(face_shape, {}).get("explanation", "")
    colour_reason = UNDERTONE_RULES.get(undertone, {}).get("explanation", "")
    return (
        f"{style.capitalize()} frames suit your {face_shape.capitalize()} face. "
        f"{shape_reason} The {colour} colour works with your {undertone} undertone. "
        f"{colour_reason}"
    ).strip()


# ── Top-level entry point ─────────────────────────────────────────────────────

def rank_frames(
    frames: list[dict],
    face_shape: str,
    undertone: str,
    ipd_mm: float,
    top_n: int = 10,
) -> list[dict]:
    """
    Score and rank frames. Returns top_n frames with `score` and `explanation` added.
    """
    scored = []
    for frame in frames:
        s = score_frame(frame, face_shape, undertone, ipd_mm)
        explanation = build_explanation(frame, face_shape, undertone)
        scored.append({**frame, "score": round(s, 1), "explanation": explanation})

    scored.sort(key=lambda f: f["score"], reverse=True)
    return scored[:top_n]
