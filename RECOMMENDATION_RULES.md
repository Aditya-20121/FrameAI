# FrameAI — Recommendation Rules Engine

This file is the single source of truth for all recommendation logic.
The rule engine is deterministic and fully auditable — no black-box ML.

---

## Face Shape → Frame Style Matrix

```python
FACE_SHAPE_RULES = {
    "oval": {
        "best_styles": ["rectangular", "wayfarer", "square", "round", "aviator", "browline"],
        "avoid_styles": ["oversized", "novelty"],
        "score_boost": ["rectangular", "wayfarer"],
        "explanation": "Oval faces have balanced proportions — almost any style works. "
                       "We've prioritised frames that add definition without overwhelming your features."
    },
    "round": {
        "best_styles": ["rectangular", "square", "wayfarer", "browline", "geometric"],
        "avoid_styles": ["round", "oval", "small"],
        "score_boost": ["rectangular", "square"],
        "explanation": "Angular frames create contrast against a round face, making it appear "
                       "longer and more defined. We've avoided round styles that echo your face shape."
    },
    "square": {
        "best_styles": ["round", "oval", "cat-eye", "rimless", "browline"],
        "avoid_styles": ["square", "rectangular", "geometric"],
        "score_boost": ["round", "oval", "cat-eye"],
        "explanation": "Curved frames soften your strong angular features. "
                       "Thin frames work better than heavy acetate for your face shape."
    },
    "heart": {
        "best_styles": ["round", "oval", "rimless", "aviator", "wayfarer"],
        "avoid_styles": ["cat-eye", "browline", "oversized"],
        "score_boost": ["round", "oval", "rimless"],
        "explanation": "Lighter frames draw attention downward, balancing your wider forehead "
                       "with your narrower chin. We've avoided top-heavy styles."
    },
    "diamond": {
        "best_styles": ["oval", "cat-eye", "browline", "rimless", "round"],
        "avoid_styles": ["rectangular", "narrow", "small"],
        "score_boost": ["oval", "cat-eye", "browline"],
        "explanation": "Frames with width or detail at the top balance your prominent cheekbones "
                       "and draw attention to your forehead and eyes."
    },
    "oblong": {
        "best_styles": ["round", "square", "wayfarer", "oversized", "browline"],
        "avoid_styles": ["narrow", "small", "rimless"],
        "score_boost": ["round", "wayfarer", "oversized"],
        "explanation": "Wide frames add perceived width and break your face's vertical length. "
                       "We've prioritised frames with strong horizontal presence."
    }
}
```

---

## Undertone → Frame Colour Matrix

```python
UNDERTONE_RULES = {
    "warm": {
        "best_colours": ["tortoiseshell", "amber", "brown", "olive", "gold", "rose_gold",
                         "tan", "honey", "cognac", "caramel"],
        "avoid_colours": ["silver", "grey", "cool_black"],
        "hardware_preference": "gold",
        "explanation": "Your warm undertone is complemented by earthy, golden tones. "
                       "We've matched frames that echo the warmth in your skin."
    },
    "cool": {
        "best_colours": ["black", "silver", "navy", "purple", "burgundy", "gunmetal",
                         "cool_grey", "blue", "deep_green"],
        "avoid_colours": ["orange", "warm_brown", "gold", "amber"],
        "hardware_preference": "silver",
        "explanation": "Your cool undertone pairs well with crisp, jewel-toned frames. "
                       "Silver hardware over gold brings out your natural colouring."
    },
    "neutral": {
        "best_colours": ["black", "tortoiseshell", "clear", "blush", "warm_grey",
                         "navy", "brown", "rose_gold"],
        "avoid_colours": [],
        "hardware_preference": "any",
        "explanation": "Your neutral undertone is versatile — most palettes work. "
                       "We've used your face shape as the primary filter and added colour variety."
    }
}
```

---

## IPD → Frame Size Band

```python
IPD_SIZE_RULES = {
    "narrow":   {"range": (0, 59),   "frame_width_mm": (125, 130)},
    "standard": {"range": (60, 66),  "frame_width_mm": (130, 138)},
    "wide":     {"range": (67, 999), "frame_width_mm": (138, 148)}
}
```

---

## Scoring Algorithm

```python
def score_frame(frame: dict, face_shape: str, undertone: str, ipd_mm: float) -> float:
    score = 0.0

    # 1. Face shape match (weight: 40%)
    shape_rules = FACE_SHAPE_RULES[face_shape]
    if frame["style"] in shape_rules["best_styles"]:
        score += 40
    if frame["style"] in shape_rules["score_boost"]:
        score += 10  # bonus for strongest matches
    if frame["style"] in shape_rules["avoid_styles"]:
        score -= 30  # heavy penalty

    # 2. Undertone colour match (weight: 30%)
    colour_rules = UNDERTONE_RULES[undertone]
    if frame["colour"] in colour_rules["best_colours"]:
        score += 30
    if frame["colour"] in colour_rules["avoid_colours"]:
        score -= 20

    # 3. IPD size match (weight: 20%)
    size_band = get_size_band(ipd_mm)
    min_w, max_w = IPD_SIZE_RULES[size_band]["frame_width_mm"]
    frame_width = frame.get("lens_width_mm", 0) + frame.get("bridge_width_mm", 0)
    if min_w <= frame_width <= max_w:
        score += 20
    elif abs(frame_width - (min_w + max_w) / 2) <= 5:
        score += 10  # close enough

    # 4. Vibe tag bonus (weight: 10% — soft signal)
    # Can be extended to accept user vibe preference input in v2

    return max(score, 0)
```

---

## Explanation String Generation

Every recommendation card shows a 1–2 sentence explanation.

**Template:**
```
"[Frame style] frames suit your [face shape] face because [reason from shape rules].
 The [colour] colour works with your [undertone] undertone."
```

**Examples:**
- "Rectangular frames suit your Round face because angular lines add definition and make your face appear longer. The tortoiseshell colour works beautifully with your warm undertone."
- "Cat-eye frames suit your Diamond face because the upswept detail at the temples balances your prominent cheekbones. The black colour complements your cool undertone."

---

## Catalogue Query

```sql
-- Get top 15 scored frames for a user's analysis
SELECT *
FROM frames
WHERE
  style = ANY(:best_styles)              -- face shape filter
  AND colour = ANY(:best_colours)        -- undertone filter  
  AND (lens_width_mm + bridge_width_mm)
      BETWEEN :min_width AND :max_width  -- IPD size filter
  AND product_image_url IS NOT NULL      -- must have product image for generation
ORDER BY
  CASE WHEN style = ANY(:boost_styles) THEN 0 ELSE 1 END,
  price_inr ASC                          -- within tier, sort by price
LIMIT 15;
```

Backend scores the 15 results with the Python algorithm above, returns top 10 ranked.
Frontend shows top 5, pre-loads 6–10 hidden.
