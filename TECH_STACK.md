# FrameAI — Tech Stack & Architecture

---

## Stack Overview

```
Frontend          Next.js 15 (App Router) + Tailwind CSS + shadcn/ui
Backend API       FastAPI (Python 3.11)
Task Queue        Celery + Redis (Upstash)
Face Analysis     MediaPipe + EfficientNet-B0 (self-hosted)
Inpainting        LaMa (self-hosted, conditional)
Image Generation  fal.ai API — FLUX.1 Kontext [pro]
Database          Supabase (PostgreSQL)
Storage           Cloudflare R2
Frontend Host     Vercel
Backend Host      Railway (prototype) → AWS ECS (scale)
```

---

## Frontend

| Concern | Choice | Reason |
|---|---|---|
| Framework | Next.js 15 (App Router) | SSR, React, file routing, image optimisation |
| Styling | Tailwind CSS | Rapid iteration, no runtime CSS |
| Components | shadcn/ui | Unstyled, accessible, no vendor lock-in |
| Camera | MediaDevices.getUserMedia() | Native browser API, no dependencies |
| Real-time face align | TensorFlow.js + BlazeFace | ~500KB, 30fps on mobile, runs in browser |
| Hosting | Vercel | Zero-config Next.js, global CDN, free tier |

---

## Backend

| Concern | Choice | Reason |
|---|---|---|
| Framework | FastAPI (Python) | Native async, auto OpenAPI docs, all ML libs are Python-native |
| Task queue | Celery + Redis | Image generation is async (4–8s) — must not block the API thread |
| Redis host | Upstash | Serverless Redis, pay-per-request, free tier available |
| Hosting | Railway (prototype) | Zero-config, $15/mo, Docker deploy |

---

## AI / ML

| Step | Model | Notes |
|---|---|---|
| Face detection (browser) | TensorFlow.js BlazeFace | Alignment only — not analysis |
| Face detection (server) | InsightFace | Validation gate |
| Face landmarks | MediaPipe Face Mesh | 478 points, CPU, ~200ms |
| Face shape classify | EfficientNet-B0 (fine-tuned) | Fallback when geometric confidence < 0.75 |
| Undertone analysis | OpenCV + LAB space | Rule-based, no ML model needed |
| Glasses removal | LaMa inpainting | Conditional — only if glasses detected |
| Image generation | fal.ai FLUX.1 Kontext [pro] | $0.04/image, image compositing |

### InsightFace Licence Note
InsightFace's AntelopeV2 encoder is non-commercial research only. For commercial launch, either:
- License InsightFace separately, OR
- Replace with ArcFace (commercial-licensed alternative)

---

## Storage & Database

| Concern | Choice | Reason |
|---|---|---|
| Image storage | Cloudflare R2 | Zero egress fees (vs S3), 10GB free, presigned URLs |
| Database | Supabase (PostgreSQL) | Managed Postgres, free tier, row-level security |
| TTL | 24h auto-purge | Privacy by default — no long-term biometric storage |

---

## API Provider — Image Generation

**Primary:** fal.ai  
**Model:** FLUX.1 Kontext [pro]  
**Upgrade path:** Nano Banana 2 Edit (14 reference images, stronger compositing)

```
fal.ai advantages:
- 30–50% cheaper than Replicate for same models
- Exclusive access to Nano Banana 2 Edit
- Faster inference (custom CUDA kernels)
- Single API key for all models — easy to swap
- Per-output pricing — no idle GPU cost
```

### Cost at Scale

| Monthly users | API cost | Total infra |
|---|---|---|
| 100 users | ~$36 | ~$61 |
| 500 users | ~$180 | ~$205 |
| 1,000 users | ~$360 | ~$385 |

---

## Architecture Diagram

```
Browser
  │
  ├── Camera (TF.js BlazeFace alignment)
  ├── Next.js App (Vercel)
  │     ├── /upload → FastAPI
  │     ├── /analysis → FastAPI
  │     ├── /recommendations → FastAPI
  │     └── /generate → FastAPI (queued)
  │
FastAPI (Railway)
  ├── Photo upload → R2
  ├── Face analysis (MediaPipe + EfficientNet)
  ├── Undertone analysis (OpenCV)
  ├── Recommendation engine (DB query + rules)
  ├── Celery worker → fal.ai API
  └── Session management (Supabase)
  │
  ├── Supabase (PostgreSQL)
  │     ├── sessions table
  │     └── frames catalogue
  │
  ├── Cloudflare R2
  │     ├── user photos (24h TTL)
  │     ├── generated images (24h TTL)
  │     └── frame product images (permanent)
  │
  └── fal.ai
        └── FLUX.1 Kontext [pro]
```

---

## Environment Variables Required

```bash
# Backend
FAL_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=
REDIS_URL=
SESSION_SECRET=

# Frontend
NEXT_PUBLIC_API_URL=
```
