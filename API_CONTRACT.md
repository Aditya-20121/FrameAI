# FrameAI — API Contract

Base URL (prototype): `https://api.frameai.in` (Railway)  
All responses: `application/json`  
Auth: Session token via HttpOnly cookie (set on first upload)

---

## POST /upload

Upload user photo and start analysis.

**Request:** `multipart/form-data`
```
photo: File (JPG/PNG/WEBP, max 10MB)
```

**Response 200:**
```json
{
  "job_id": "uuid-v4",
  "status": "processing"
}
```

**Response 400 (validation failures):**
```json
{
  "error": "no_face_detected",
  "message": "We couldn't find a face in this photo. Please use a front-facing photo with good lighting."
}
```

Possible error codes:
- `no_face_detected`
- `multiple_faces`
- `resolution_too_low` (min 512×512)
- `file_too_large` (max 10MB)
- `unsupported_format`
- `face_too_small` (face region < 30% of image)

---

## GET /analysis/{job_id}

Get face analysis results.

**Response 200:**
```json
{
  "job_id": "uuid-v4",
  "status": "complete",
  "face_shape": "diamond",
  "face_shape_confidence": 0.91,
  "face_shape_explanation": "Your face is widest at the cheekbones, with a narrower forehead and jawline — that's the Diamond shape.",
  "undertone": "warm",
  "undertone_confidence": 0.84,
  "undertone_hex": "#C68642",
  "ipd_mm": 63.4,
  "size_band": "standard"
}
```

**Response 202 (still processing):**
```json
{ "status": "processing" }
```

---

## GET /recommendations/{job_id}

Get ranked frame recommendations.

**Response 200:**
```json
{
  "job_id": "uuid-v4",
  "total": 10,
  "frames": [
    {
      "frame_id": "uuid",
      "rank": 1,
      "name": "Vincent Chase VC E14662",
      "style": "oval",
      "colour": "tortoiseshell",
      "colour_hex": "#8B5C2A",
      "material": "acetate",
      "retailer": "Lenskart",
      "price_inr": 1899,
      "buy_url": "https://www.lenskart.com/...",
      "product_image_url": "https://r2.frameai.in/frames/uuid.webp",
      "vibe_tags": ["minimal", "professional"],
      "score": 88.5,
      "explanation": "Oval frames suit your Diamond face because they soften your angles and draw attention to your eyes. The tortoiseshell colour works beautifully with your warm undertone."
    }
    // ... 9 more
  ]
}
```

---

## POST /generate

Trigger image generation for one frame.

**Request:**
```json
{
  "job_id": "uuid-v4",
  "frame_id": "uuid"
}
```

**Response 200:**
```json
{
  "task_id": "uuid-v4",
  "status": "queued",
  "generations_remaining": 2
}
```

**Response 403 (limit reached):**
```json
{
  "error": "generation_limit_reached",
  "message": "You've used all 3 free generations. Sign up to get more.",
  "generations_used": 3,
  "generations_remaining": 0
}
```

---

## GET /generate/{task_id}

Poll generation status.

**Response 200 (complete):**
```json
{
  "task_id": "uuid-v4",
  "status": "complete",
  "image_url": "https://r2.frameai.in/generated/uuid.webp",
  "expires_at": "2026-06-25T10:00:00Z"
}
```

**Response 200 (processing):**
```json
{
  "task_id": "uuid-v4",
  "status": "processing",
  "progress": 0.6
}
```

**Response 200 (failed — does not count against limit):**
```json
{
  "task_id": "uuid-v4",
  "status": "failed",
  "error": "generation_failed",
  "message": "Something went wrong. This try has not been counted. Please try again."
}
```

---

## GET /session

Get current session generation status.

**Response 200:**
```json
{
  "generations_used": 1,
  "generations_remaining": 2,
  "limit": 3
}
```

---

## Database Schema

```sql
-- Sessions
CREATE TABLE sessions (
  token              TEXT PRIMARY KEY,
  generations_used   INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_active_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Jobs
CREATE TABLE jobs (
  job_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_token      TEXT REFERENCES sessions(token),
  photo_r2_key       TEXT NOT NULL,
  face_shape         TEXT,
  face_shape_conf    FLOAT,
  undertone          TEXT,
  undertone_conf     FLOAT,
  undertone_hex      TEXT,
  ipd_mm             FLOAT,
  size_band          TEXT,
  status             TEXT NOT NULL DEFAULT 'processing',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at         TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Generation tasks
CREATE TABLE generation_tasks (
  task_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id             UUID REFERENCES jobs(job_id),
  frame_id           UUID REFERENCES frames(frame_id),
  session_token      TEXT REFERENCES sessions(token),
  status             TEXT NOT NULL DEFAULT 'queued',
  image_r2_key       TEXT,
  fal_request_id     TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at       TIMESTAMPTZ,
  expires_at         TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Frames catalogue (see SPEC.md for full schema)
CREATE TABLE frames (
  frame_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              TEXT NOT NULL,
  style             TEXT NOT NULL,
  colour            TEXT NOT NULL,
  colour_hex        TEXT,
  material          TEXT,
  face_shape_tags   TEXT[],
  undertone_tags    TEXT[],
  gender_tag        TEXT,
  lens_width_mm     INTEGER,
  bridge_width_mm   INTEGER,
  temple_length_mm  INTEGER,
  vibe_tags         TEXT[],
  retailer          TEXT NOT NULL,
  price_inr         INTEGER,
  buy_url           TEXT NOT NULL,
  product_image_url TEXT NOT NULL,
  scraped_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
```
