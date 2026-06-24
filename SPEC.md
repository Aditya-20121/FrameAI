# FrameAI — Master Product Specification
**Version:** 1.0  
**Last Updated:** June 2026  
**Status:** Approved — Ready for Development

---

## 1. Problem Statement

Buying spectacle frames is a high-friction, high-anxiety decision. Customers spend up to 45 minutes in-store unsure of what suits them, relying on store assistants who may or may not have relevant expertise. Online, the problem is worse — AR try-on tools look plasticky and unreal, and no tool tells you *why* a frame suits your face.

People with prescriptions above -2.0 diopters cannot even see themselves clearly when trying frames in-store without their current glasses.

**FrameAI solves this:** Upload one photo. Get an expert AI analysis of your face shape and skin undertone. Receive top 10 frame recommendations with reasons. Generate photorealistic images of yourself wearing your chosen frames — indistinguishable from a real photograph.

---

## 2. Product Overview

**Product name:** FrameAI  
**Type:** Web application (prototype)  
**Target users:** Anyone buying spectacle frames — particularly urban Indian buyers aged 18–45  
**Business model:** B2C freemium (3 free generations → sign up / pay for more). Future: B2B SaaS to optical chains.  
**Monetisation path:** Affiliate links to retailer product pages (Lenskart, Titan Eye+, John Jacobs, Rayban India) from day 1.

---

## 3. Core User Flow

```
1. User opens website
2. Camera opens with oval alignment guide → user takes photo without glasses
   (Upload fallback available for desktop users)
3. Face analysis runs server-side (~2–3s):
   - Face shape classified (6 classes: Oval, Round, Square, Heart, Diamond, Oblong)
   - Skin undertone detected (Warm / Cool / Neutral)
   - IPD (interpupillary distance) measured
4. Analysis card shown to user:
   - Face shape + plain-English explanation
   - Undertone + colour swatch
5. Top 5 frame recommendations displayed:
   - Frame product image, name, style, colour, retailer, price
   - "Try this on →" button per frame
   - "View on [Retailer] →" buy link per frame
   - "Show 5 more" expands to show frames 6–10 (no new request, already loaded)
6. User clicks "Try this on →" on a specific frame:
   - Micro-confirm: "This uses 1 of your 3 free tries. X remaining."
   - 1 API call fires (fal.ai / FLUX.1 Kontext)
   - ~4–8s generation time
   - Photorealistic composite image appears on that card
   - Buy link shown prominently below image
7. User can try 2 more frames (3 total across all frames)
8. After 3rd generation: all "Try this on" buttons disabled
   - Banner: "Sign up to try more frames"
   - Recommendations and buy links remain fully functional
```

**Key principle:** Zero API cost until the user deliberately triggers generation.

---

## 4. What Makes This Different

| Feature | Lenskart AR | Warby Parker AR | FrameAI |
|---|---|---|---|
| Works with glasses on | ❌ | ❌ | ✅ (inpaints existing glasses) |
| Photorealistic output | ❌ Plasticky | ❌ Plasticky | ✅ Diffusion-generated |
| Face shape analysis | Basic quiz | Basic quiz | ✅ AI landmark-based |
| Undertone + colour recommendation | ❌ | ❌ | ✅ |
| Explains why a frame suits you | ❌ | ❌ | ✅ |
| Uses actual product image | ✅ | ✅ | ✅ (no text prompts for frame) |

---

## 5. Technical Pipeline

### Step 1 — Photo ingestion & validation
- User uploads via camera (oval guide) or file upload
- Server validates: single face, min 512×512, not blurred, not corrupted
- Stored in Cloudflare R2 with job UUID, 24h TTL
- **Stack:** FastAPI, InsightFace BlazeFace detect, Pillow, Cloudflare R2

### Step 2 — Face landmark extraction
- 478 landmarks via MediaPipe Face Mesh
- Extract: forehead width, cheekbone width, jawline width, face length, nose bridge midpoint, eye corners, IPD
- Pure geometry — ~200ms on CPU
- **Stack:** MediaPipe, NumPy

### Step 3 — Face shape classification
- Primary: rule-based geometric classifier (ratio thresholds → fast + explainable)
- Fallback if confidence < 0.75: EfficientNet-B0 fine-tuned on CelebA-HQ
- Output: shape class + confidence + explanation string
- 6 classes: Oval, Round, Square, Heart, Diamond, Oblong
- **Accuracy:** ~92% (MediaPipe-based, to be improved with Indian face data)

### Step 4 — Skin undertone analysis
- Sample pixels from cheek + forehead regions (avoiding shadows)
- RGB → LAB colour space conversion
- Classify via LAB a* and b* channel thresholds calibrated to Monk scale (10-point, inclusive of South Asian skin diversity)
- Output: Warm / Cool / Neutral + confidence + hex approximation
- **Stack:** OpenCV, Monk scale calibration

### Step 5 — Frame recommendation engine
- Input: face_shape + undertone + IPD
- Process: rule-based lookup against frame catalogue
  - Face shape → allowed/preferred frame styles (see Section 6)
  - Undertone → colour palette
  - IPD → size band (narrow/standard/wide)
  - Vibe tags as soft secondary filter
- Scores top 15, returns top 10 to frontend
- Frontend shows top 5, hides 6–10 behind "Show more" (pre-loaded, no extra request)
- **Stack:** Python dict/rule engine, PostgreSQL catalogue query

### Step 6 — Photorealistic image generation (on-demand per frame)
- Triggered only when user clicks "Try this on →"
- Input A: user photo (retrieved from R2 by job ID)
- Input B: frame product image (white background, from catalogue R2)
- Pre-process: if user wearing glasses → LaMa inpainting removes them first
- Geometric alignment: MediaPipe nose bridge + eye corners → warp frame image to correct position/scale
- API call: fal.ai FLUX.1 Kontext [pro]
  - Prompt is positional/structural only: *"Place these glasses on this person's face. Preserve the person's identity, skin tone, and lighting. The glasses should sit naturally on the nose bridge. Do not change the person's face, hair, or background."*
  - Frame image passed as reference condition — NOT described in text
- Output: photorealistic composite at 1024×1024, stored in R2 with 24h TTL
- Generation time: ~4–8s
- **Cost:** ~$0.04 per image (fal.ai FLUX.1 Kontext pricing)

### Step 7 — Results delivery
- Presigned R2 URL returned to frontend
- Image appears on the specific frame card
- Buy link displayed below image
- Generation counter decremented (server-side, atomic)

---

## 6. Recommendation Rules

### Face Shape → Frame Style

| Face Shape | Best Styles | Avoid |
|---|---|---|
| **Oval** | Rectangle, wayfarer, square, round — almost anything | Extremely oversized, novelty shapes |
| **Round** | Rectangle, square, angular wayfarers | Round frames, small oval (echo the shape) |
| **Square** | Round, oval, cat-eye, rimless | Square/rectangular (amplify angularity) |
| **Heart** | Bottom-heavy frames, round, oval, rimless | Cat-eye, top-heavy decorative frames |
| **Diamond** | Oval, cat-eye, semi-rimless | Narrow rectangular |
| **Oblong** | Oversized round, square, wayfarer, thick-rimmed | Narrow, small frames |

### Undertone → Frame Colour

| Undertone | Best Colours | Avoid |
|---|---|---|
| **Warm** | Tortoiseshell, amber, warm brown, olive green, gold metal, rose gold | Cold silver, stark black |
| **Cool** | Black, silver, navy, deep purple, burgundy, gunmetal | Warm gold, orange-tinted frames |
| **Neutral** | Most palettes work. Focus on face shape rule as primary driver | — |

### IPD → Frame Size

| IPD | Frame Width Band |
|---|---|
| < 60mm | Narrow (125–130mm) |
| 60–66mm | Standard (130–138mm) |
| > 66mm | Wide (138–148mm) |

---

## 7. Frame Catalogue Schema

```sql
CREATE TABLE frames (
  frame_id          UUID PRIMARY KEY,
  name              TEXT NOT NULL,
  style             TEXT NOT NULL,          -- rectangular, round, oval, square, cat-eye, aviator, wayfarer, browline, geometric, rimless
  colour            TEXT NOT NULL,          -- human label e.g. "tortoiseshell"
  colour_hex        TEXT,                   -- dominant hex from image
  material          TEXT,                   -- acetate, metal, titanium, mixed, wood, TR90
  face_shape_tags   TEXT[],                 -- e.g. ["oval","diamond","heart"]
  undertone_tags    TEXT[],                 -- e.g. ["warm","neutral"]
  gender_tag        TEXT,                   -- men, women, unisex
  lens_width_mm     INTEGER,
  bridge_width_mm   INTEGER,
  temple_length_mm  INTEGER,
  vibe_tags         TEXT[],                 -- minimal, editorial, retro, bold, professional, sporty
  retailer          TEXT NOT NULL,          -- Lenskart, Titan Eye+, John Jacobs, Rayban, etc.
  price_inr         INTEGER,
  buy_url           TEXT NOT NULL,
  product_image_url TEXT NOT NULL,          -- white-background front-facing shot in R2 at 512×512
  scraped_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 8. Generation Limit Logic

- On first photo upload: server generates UUID session token, sets as HttpOnly cookie (1 year expiry)
- DB table `sessions`: `{token, generations_used, created_at, last_active_at}`
- `generations_used` starts at 0, max 3, never resets for anonymous users
- Every generation request: server validates token + checks `generations_used < 3` before firing API
- Counter incremented atomically after successful API response — failed generations do not count
- Client-side counter is display only — never trusted for access control
- Cookie cleared = new 3 generations (accepted v1 limitation — fingerprinting out of scope)

---

## 9. Camera Guide Spec

- MediaDevices.getUserMedia() API for browser camera
- Oval SVG overlay on video feed — fixed proportions, not dynamic AR
- Real-time face alignment: TensorFlow.js BlazeFace (~500KB) at 30fps
- Alignment logic: face bounding box must overlap oval region ≥ 85%
- Oval turns green when aligned
- Auto-capture after 1.5s continuous green (eliminates tap blur)
- Instruction text: "Remove your glasses" + "Look straight ahead, relax your face"
- "Upload a photo instead" fallback always visible

---

## 10. API Provider

**Primary:** fal.ai  
**Model:** FLUX.1 Kontext [pro] for image compositing  
**Upgrade path:** Nano Banana 2 Edit (accepts up to 14 reference images) if quality improvement needed  
**Cost:** ~$0.04/image · 3 images/user = $0.12 max per user

| Scale | Monthly API cost |
|---|---|
| 100 users (all use 3 tries) | ~$36 |
| 500 users | ~$180 |
| 1,000 users | ~$360 |

---

## 11. Out of Scope for v1

- Real-time AR video overlay
- Smart mirror / hardware kiosk
- User accounts and saved history
- Direct checkout integration
- Multi-face group photos
- Glasses sticker removal from frame product images
- Fingerprinting / device-based generation limit enforcement
