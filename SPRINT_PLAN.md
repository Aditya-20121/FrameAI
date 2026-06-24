# FrameAI — Sprint Plan (PDLC Phase 4)

**Total duration:** 8 weeks (4 sprints × 2 weeks)  
**Team assumption:** 1–2 developers  
**Start:** After PDLC Phase 3 (Design) is complete

---

## Sprint 1 — Backend Foundation (Weeks 7–8)

**Goal:** Working backend API with face analysis pipeline. No frontend yet.

### Tasks

| # | Task | Notes |
|---|---|---|
| 1.1 | FastAPI project scaffold | Folder structure, env vars, health check endpoint |
| 1.2 | Cloudflare R2 setup | Bucket, CORS, presigned URL generation |
| 1.3 | Supabase setup | sessions table, frames table schema |
| 1.4 | Photo upload endpoint | `POST /upload` → validates, stores in R2, returns job_id |
| 1.5 | MediaPipe face landmarks | Extract 478 points, compute ratios |
| 1.6 | Face shape classifier | Geometric rule-based first, EfficientNet fallback |
| 1.7 | Undertone analysis | OpenCV LAB conversion, Monk scale calibration |
| 1.8 | Analysis endpoint | `GET /analysis/{job_id}` → returns shape + undertone + IPD |
| 1.9 | Unit tests for all rule branches | Face shape rules + undertone rules fully tested |

### Deliverable
`POST /upload` + `GET /analysis/{job_id}` working end-to-end. Verified on 20 test photos.

### Gate
Face shape classification ≥ 88% on test set. Analysis completes < 3s.

---

## Sprint 2 — Recommendation Engine + Frame Catalogue (Weeks 9–10)

**Goal:** Recommendation engine working against a seed frame catalogue.

> **Before starting Sprint 2, complete the full data pipeline in `DATA_PIPELINE.md`.**
> The scraping and annotation work (estimated 6–8 days) should run in parallel with Sprint 1.
> Sprint 2 assumes 500 fully annotated frames are already loaded in Supabase.

### Tasks

| # | Task | Notes |
|---|---|---|
| 2.1 | Celery + Upstash Redis setup | Async task queue |
| 2.2 | Verify seed catalogue in DB | 500 frames, all schema fields populated — see DATA_PIPELINE.md |
| 2.3 | Recommendation rule engine | Face shape × undertone × IPD scoring — see RECOMMENDATION_RULES.md |
| 2.4 | `GET /recommendations/{job_id}` | Returns top 10 ranked frames |
| 2.5 | Frame scraper (already done via DATA_PIPELINE.md) | Playwright-based, all 4 sources |
| 2.6 | Price refresh job | Weekly Celery task to update price_inr |

### Deliverable
`GET /recommendations/{job_id}` returns top 10 ranked frames with all schema fields populated.

### Gate
Top 3 recommendations for any test face are plausibly correct per manual review.

---

## Sprint 3 — Image Generation (Weeks 11–12)

**Goal:** End-to-end generation pipeline working via fal.ai.

### Tasks

| # | Task | Notes |
|---|---|---|
| 3.1 | fal.ai account + API key | Set up billing, test FLUX.1 Kontext |
| 3.2 | LaMa inpainting integration | Conditional glasses removal |
| 3.3 | Geometric frame alignment | MediaPipe nose bridge + IPD → warp frame image |
| 3.4 | fal.ai FLUX.1 Kontext call | Composite user photo + aligned frame image |
| 3.5 | `POST /generate` endpoint | Queues Celery task, returns task_id immediately |
| 3.6 | `GET /generate/{task_id}` | Polls job status + returns presigned URL when done |
| 3.7 | Session + generation counter | Atomic DB increment, server-side enforcement |
| 3.8 | Generation limit middleware | Returns 403 when generations_used = 3 |
| 3.9 | Quality QA on 20 faces | Manual review of identity preservation + frame placement |

### Deliverable
Full pipeline: photo → analysis → recommendation → generation. 20 test users run through manually.

### Gate
≥ 16/20 test generations judged "photorealistic with correct frame placement" by manual QA.

---

## Sprint 4 — Frontend + Polish (Weeks 13–14)

**Goal:** Complete, shippable web product.

### Tasks

| # | Task | Notes |
|---|---|---|
| 4.1 | Next.js project scaffold | App Router, Tailwind, shadcn/ui |
| 4.2 | Camera screen | Oval guide, TF.js BlazeFace alignment, auto-capture |
| 4.3 | File upload fallback | Drag-and-drop + click to upload |
| 4.4 | Analysis card screen | Face shape, undertone, IPD display |
| 4.5 | Recommendations screen | Top 5 visible + "Show 5 more" toggle |
| 4.6 | Frame card component | Product image, name, price, "Try this on →", buy link |
| 4.7 | Generation UX | Spinner on card, image reveal, counter update |
| 4.8 | Micro-confirm modal | "X tries remaining" before generation fires |
| 4.9 | Generation limit state | Disabled buttons + sign-up CTA banner |
| 4.10 | Error states | All API failure cases handled with specific messages |
| 4.11 | Mobile responsiveness | Tested on iOS Safari + Android Chrome |
| 4.12 | Vercel + Railway deploy | Production URLs, env vars set |

### Deliverable
Live website at production URL. Full flow works on mobile and desktop.

### Gate
5 real users complete the full flow without assistance. No P0 bugs.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| InsightFace licence for commercial use | High | High | Use for prototype only; plan licence or encoder swap before launch |
| Identity drift in generation | Medium | High | Strict input requirements (close-up frontal); regenerate button |
| Generation latency > 15s | Medium | Medium | Timeout at 20s, show error, don't count against limit |
| Indian face shape accuracy gap | High | Medium | Collect 200–500 Indian face images for fine-tuning post-prototype |
| fal.ai outage | Low | High | Fallback: Replicate as secondary provider |
| R2 egress cost surprise | Low | Low | R2 has zero egress fees — not an issue |

---

## Definition of Done

A feature is done when:
1. Code is reviewed and merged to main
2. Unit tests pass
3. Manually tested on Chrome desktop + mobile Safari
4. Error states handled
5. No console errors in production build