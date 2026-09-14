"""
Frame recommendation engine — v2.

Scoring (max 100):
  Face shape   40 + 5 boost = 45 pts   primary driver (industry standard)
  Colour       30 pts                   undertone × skin depth family system
  IPD size     20 pts                   fit measurement
  Features      5 pts                   jawline / cheekbones / eye spacing
"""

# ── Colour family system ───────────────────────────────────────────────────────
# Maps raw DB colour strings → one of 7 canonical families.
# All comparisons are case-insensitive against this table.

COLOUR_FAMILY: dict[str, str] = {
    # warm earthy tones (tortoiseshell, brown, tan, cognac …)
    "tortoiseshell": "warm_earth",
    "demi":          "warm_earth",    # tortoiseshell variant
    "brown":         "warm_earth",
    "olive":         "warm_earth",
    "honey":         "warm_earth",
    "cognac":        "warm_earth",
    "caramel":       "warm_earth",
    "tan":           "warm_earth",

    # warm metals
    "gold":          "warm_metal",
    "rose_gold":     "warm_metal",

    # warm bold / saturated (amber, orange, flame …)
    "amber":         "warm_bold",
    "orange":        "warm_bold",
    "flame":         "warm_bold",
    "citrus-ace":    "warm_bold",

    # cool neutrals (greyscale)
    "black":         "cool_neutral",
    "silver":        "cool_neutral",
    "gunmetal":      "cool_neutral",
    "cool_grey":     "cool_neutral",
    "graphite-ace":  "cool_neutral",
    "dark night":    "cool_neutral",
    "frost":         "cool_neutral",

    # cool jewel tones (blue, navy, purple, deep green …)
    "blue":          "cool_jewel",
    "navy":          "cool_jewel",
    "purple":        "cool_jewel",
    "burgundy":      "cool_jewel",
    "deep_green":    "cool_jewel",
    "sapphire-ace":  "cool_jewel",
    "turquoise":     "cool_jewel",

    # universal — flatters everyone
    "clear":         "universal",

    # soft / rose tones — gentle, slightly cooler lean
    "blush":         "universal_soft",
    "dusty rose":    "universal_soft",
    "flamingo":      "universal_soft",
    "rose-ace":      "universal_soft",
}

# Graded colour score (0–30) per undertone per family.
# Sources: Warby Parker colour guide, Zenni colour guide, Readers.com skin-tone guide.
_COLOUR_SCORES: dict[str, dict[str, int]] = {
    "warm": {
        "warm_earth":     30,   # tortoiseshell, brown — classic warm match
        "warm_metal":     28,   # gold, rose gold — warms skin beautifully
        "warm_bold":      20,   # amber, orange — works but can overpower
        "cool_neutral":    8,   # black/silver — not ideal but wearable
        "cool_jewel":      0,   # blue/purple — clashes with warm tones
        "universal":      15,   # clear — neutral, no conflict
        "universal_soft": 12,   # blush — light, not as warm as earth tones
        "unknown":         5,
    },
    "cool": {
        "warm_earth":      0,   # tortoiseshell on cool skin — muddy
        "warm_metal":      8,   # gold — wearable but silver is better
        "warm_bold":      -10,  # orange/amber — clashes with cool skin
        "cool_neutral":   30,   # black, silver, gunmetal — crisp & clean
        "cool_jewel":     28,   # navy, purple, deep green — jewel-toned complement
        "universal":      15,
        "universal_soft": 12,
        "unknown":         5,
    },
    "neutral": {
        "warm_earth":     20,
        "warm_metal":     18,
        "warm_bold":      12,
        "cool_neutral":   20,
        "cool_jewel":     20,
        "universal":      28,   # clear is especially flattering on neutral skin
        "universal_soft": 22,
        "unknown":        15,
    },
}

# Depth adjustment on top of base colour score.
# Research: fair/light skin tolerates less contrast; deep skin tolerates bold jewels.
def _depth_adj(family: str, skin_depth: str | None) -> int:
    if not skin_depth:
        return 0
    if skin_depth == "deep" and family == "cool_jewel":
        return +5   # electric blue, purple, teal — exceptional on deep skin
    if skin_depth == "deep" and family == "warm_bold":
        return +4   # bold warm also pops on deep skin
    if skin_depth == "deep" and family == "universal":
        return -3   # clear can disappear on deep skin
    if skin_depth in ("fair", "light") and family == "universal":
        return +4   # clear creates elegant, non-competing look on fair skin
    if skin_depth in ("fair", "light") and family == "universal_soft":
        return +4   # blush/rose on fair skin is very flattering
    if skin_depth == "olive" and family == "warm_earth":
        return +4   # tortoiseshell, brown — harmony with olive skin
    return 0


def get_colour_score(colour: str, undertone: str, skin_depth: str | None) -> float:
    family = COLOUR_FAMILY.get(colour.lower().strip(), "unknown")
    base = _COLOUR_SCORES.get(undertone, {}).get(family, 5)
    adj = _depth_adj(family, skin_depth)
    return max(0.0, min(30.0, float(base + adj)))


# ── Face shape rules ───────────────────────────────────────────────────────────
# Verified against DB styles: square, rectangular, geometric, round, cat-eye,
# rimless, aviator, wayfarer, browline.
# "oval" style removed — does not exist in catalogue.

FACE_SHAPE_RULES: dict[str, dict] = {
    "oval": {
        "best_styles":  ["rectangular", "wayfarer", "square", "round", "aviator", "browline", "cat-eye", "geometric"],
        "avoid_styles": [],
        "score_boost":  ["rectangular", "wayfarer"],
        "explanation":  (
            "Oval faces have balanced proportions — almost any style works. "
            "We've prioritised frames that add definition without overwhelming your features."
        ),
    },
    "round": {
        "best_styles":  ["rectangular", "square", "wayfarer", "browline", "geometric"],
        "avoid_styles": ["round"],
        "score_boost":  ["rectangular", "square"],
        "explanation":  (
            "Angular frames create contrast against a round face, making it appear "
            "longer and more defined."
        ),
    },
    "square": {
        "best_styles":  ["round", "cat-eye", "rimless", "aviator", "browline"],
        "avoid_styles": ["square", "rectangular", "geometric"],
        "score_boost":  ["round", "cat-eye"],
        "explanation":  (
            "Curved frames soften your strong angular jaw and balanced proportions. "
            "Thin rimless or aviator styles also ease the angularity."
        ),
    },
    "heart": {
        "best_styles":  ["round", "rimless", "aviator", "wayfarer", "geometric"],
        "avoid_styles": ["cat-eye", "browline"],
        "score_boost":  ["round", "rimless", "aviator"],
        "explanation":  (
            "Lighter, bottom-weighted frames balance your wider forehead against "
            "your narrower chin. We've avoided top-heavy styles that add visual weight to the brow."
        ),
    },
    "diamond": {
        "best_styles":  ["cat-eye", "browline", "rimless", "round", "wayfarer"],
        "avoid_styles": ["rectangular", "geometric"],
        "score_boost":  ["cat-eye", "browline"],
        "explanation":  (
            "Frames with width or decorative detail at the top balance your prominent "
            "cheekbones and draw attention upward to your forehead."
        ),
    },
    "oblong": {
        "best_styles":  ["round", "square", "wayfarer", "browline", "cat-eye"],
        "avoid_styles": ["rimless", "aviator"],
        "score_boost":  ["round", "wayfarer", "square"],
        "explanation":  (
            "Wide frames add perceived horizontal width and break the vertical length "
            "of your face. Browlines and bold square frames work especially well."
        ),
    },
}

# ── Undertone display labels (used in explanation strings) ────────────────────

_UNDERTONE_COLOUR_LABELS: dict[str, dict[str, str]] = {
    "warm":    {
        "warm_earth":     "earthy brown tones that echo the warmth in your skin",
        "warm_metal":     "gold-toned hardware that harmonises with warm undertones",
        "cool_neutral":   "a neutral frame that pairs cleanly with any wardrobe",
        "universal":      "a clean clear frame that lets your features speak",
        "universal_soft": "a soft rose tone that flatters warm skin beautifully",
        "unknown":        "a versatile tone",
    },
    "cool":    {
        "cool_neutral":   "crisp black or silver that pops against cool undertones",
        "cool_jewel":     "a jewel tone that complements your natural cool tones",
        "universal":      "a clear frame that works elegantly on cool skin",
        "universal_soft": "a soft blush that softens and flatters cool undertones",
        "unknown":        "a versatile tone",
    },
    "neutral": {
        "universal":      "clear frames that flatter your balanced, versatile skin tone",
        "universal_soft": "a soft tone that works beautifully on neutral skin",
        "warm_earth":     "a warm earthy tone that suits your neutral palette",
        "cool_neutral":   "a classic neutral that works with your versatile undertone",
        "cool_jewel":     "a bold jewel tone that pops on neutral skin",
        "unknown":        "a versatile tone",
    },
}


def _colour_label(colour: str, undertone: str) -> str:
    family = COLOUR_FAMILY.get(colour.lower().strip(), "unknown")
    return _UNDERTONE_COLOUR_LABELS.get(undertone, {}).get(family, "a well-matched colour")


# ── IPD / size rules ──────────────────────────────────────────────────────────

IPD_SIZE_RULES: dict[str, dict] = {
    "narrow":   {"range": (0, 59),    "frame_width_mm": (125, 130)},
    "standard": {"range": (60, 66),   "frame_width_mm": (130, 138)},
    "wide":     {"range": (67, 9999), "frame_width_mm": (138, 148)},
}


def get_size_band(ipd_mm: float) -> str:
    if ipd_mm < 60:
        return "narrow"
    if ipd_mm <= 66:
        return "standard"
    return "wide"


# ── Feature modifier ──────────────────────────────────────────────────────────
# Secondary signal — max 5 pts. Based on jawline type, cheekbone prominence,
# and eye spacing modifying the base face-shape style preference.

_SOFTENING_STYLES = {"round", "cat-eye", "aviator", "rimless"}
_DEFINING_STYLES  = {"rectangular", "square", "geometric", "browline"}
_WIDE_STYLES      = {"square", "wayfarer", "rectangular"}
_NARROW_STYLES    = {"round", "rimless", "aviator"}


def get_feature_modifier(
    style: str,
    jawline: str | None,
    cheekbones: str | None,
    eye_set: str | None,
) -> float:
    bonus = 0.0

    # Jawline: angular jaw → softer frames reduce harshness;
    #          soft jaw → defining frames add structure.
    if jawline == "angular" and style in _SOFTENING_STYLES:
        bonus += 2
    elif jawline == "soft" and style in _DEFINING_STYLES:
        bonus += 2

    # Cheekbone prominence: high → cat-eye/browline frames accent them;
    #                       low  → browline/geometric adds upper structure.
    if cheekbones == "high" and style in {"cat-eye", "browline"}:
        bonus += 2
    elif cheekbones == "low" and style in {"browline", "geometric"}:
        bonus += 1

    # Eye spacing: close-set → wide frames optically spread eyes;
    #              wide-set  → narrower/lighter frames draw eyes together.
    if eye_set == "close" and style in _WIDE_STYLES:
        bonus += 1
    elif eye_set == "wide" and style in _NARROW_STYLES:
        bonus += 1

    return min(bonus, 5.0)


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_frame(
    frame: dict,
    face_shape: str,
    undertone: str,
    ipd_mm: float,
    skin_depth: str | None = None,
    jawline: str | None = None,
    cheekbones: str | None = None,
    eye_set: str | None = None,
) -> float:
    score = 0.0

    shape_rules = FACE_SHAPE_RULES.get(face_shape, {})
    size_band = get_size_band(ipd_mm)
    min_w, max_w = IPD_SIZE_RULES[size_band]["frame_width_mm"]

    # 1. Face shape (45 pts max: 40 base + 5 boost)
    style = (frame.get("style") or "").lower().strip()
    if style in shape_rules.get("best_styles", []):
        score += 40
    if style in shape_rules.get("score_boost", []):
        score += 5
    if style in shape_rules.get("avoid_styles", []):
        score -= 30

    # 2. Colour — family-based, depth-adjusted (30 pts max)
    colour = (frame.get("colour") or "").lower().strip()
    score += get_colour_score(colour, undertone, skin_depth)

    # 3. IPD / frame width (20 pts max)
    lens_w  = frame.get("lens_width_mm") or 0
    bridge_w = frame.get("bridge_width_mm") or 0
    frame_width = lens_w + bridge_w
    if frame_width:
        if min_w <= frame_width <= max_w:
            score += 20
        elif abs(frame_width - (min_w + max_w) / 2) <= 5:
            score += 10

    # 4. Feature modifier (5 pts max)
    score += get_feature_modifier(style, jawline, cheekbones, eye_set)

    return max(score, 0.0)


# ── Explanation builder ───────────────────────────────────────────────────────

def build_explanation(
    frame: dict,
    face_shape: str,
    undertone: str,
    skin_depth: str | None = None,
    jawline: str | None = None,
    cheekbones: str | None = None,
) -> str:
    style  = (frame.get("style") or "frame").capitalize()
    colour = (frame.get("colour") or "").lower()

    shape_reason = FACE_SHAPE_RULES.get(face_shape, {}).get("explanation", "")
    colour_label = _colour_label(colour, undertone)

    parts: list[str] = []

    # Opening — style × face shape
    parts.append(f"{style} frames are a great match for your {face_shape.capitalize()} face.")

    # Shape rationale (1 sentence extracted from the longer explanation)
    if shape_reason:
        sentence = shape_reason.split(".")[0] + "."
        parts.append(sentence)

    # Colour rationale — uses the family label
    if colour:
        parts.append(f"The {colour} colour is {colour_label}.")

    # Feature note — mention only if relevant
    _jaw_map = {"angular": "your defined jawline", "soft": "your softer jaw"}
    _cb_map  = {"high": "your high cheekbones"}
    if jawline in _jaw_map and style.lower() in (_SOFTENING_STYLES | _DEFINING_STYLES):
        parts.append(f"The shape complements {_jaw_map[jawline]}.")
    elif cheekbones in _cb_map and style.lower() in {"cat-eye", "browline"}:
        parts.append(f"The upswept frame highlights {_cb_map[cheekbones]}.")

    return " ".join(parts)


# ── Top-level entry point ─────────────────────────────────────────────────────

def rank_frames(
    frames: list[dict],
    face_shape: str,
    undertone: str,
    ipd_mm: float,
    skin_depth: str | None = None,
    jawline: str | None = None,
    cheekbones: str | None = None,
    eye_set: str | None = None,
    top_n: int = 10,
) -> list[dict]:
    """Score, deduplicate, and rank frames. Returns top_n with `score` and `explanation` added."""
    scored = []
    for frame in frames:
        s = score_frame(
            frame, face_shape, undertone, ipd_mm,
            skin_depth=skin_depth,
            jawline=jawline,
            cheekbones=cheekbones,
            eye_set=eye_set,
        )
        explanation = build_explanation(
            frame, face_shape, undertone,
            skin_depth=skin_depth,
            jawline=jawline,
            cheekbones=cheekbones,
        )
        scored.append({**frame, "score": round(s, 1), "explanation": explanation})

    scored.sort(key=lambda f: f["score"], reverse=True)

    # Deduplicate: same (name, colour) pair is the same product appearing twice
    # due to scraper data quality issues. Keep the first (highest-scored) occurrence.
    seen_products: set[tuple] = set()
    deduped: list[dict] = []
    for frame in scored:
        key = ((frame.get("name") or "").strip().lower(), (frame.get("colour") or "").strip().lower())
        if key not in seen_products:
            seen_products.add(key)
            deduped.append(frame)

    # Style diversity: cap each style at ⌊top_n / 3⌋ frames (min 2) so the top-10
    # always shows variety rather than 10 identical rectangular frames.
    max_per_style = max(2, top_n // 3)
    style_counts: dict[str, int] = {}
    diverse: list[dict] = []
    overflow: list[dict] = []
    for frame in deduped:
        style = (frame.get("style") or "").strip()
        if style_counts.get(style, 0) < max_per_style:
            style_counts[style] = style_counts.get(style, 0) + 1
            diverse.append(frame)
        else:
            overflow.append(frame)
        if len(diverse) == top_n:
            break

    # If we don't yet have top_n after diversity pass, fill from overflow (still sorted)
    if len(diverse) < top_n:
        diverse.extend(overflow[: top_n - len(diverse)])

    return diverse
