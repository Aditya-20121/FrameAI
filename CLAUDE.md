# CLAUDE.md — Instructions for Claude Code

This file tells Claude Code everything it needs to know about this project.
Read this before writing any code.

---

## What We Are Building

**FrameAI** — An AI-powered web application that:
1. Takes a user's selfie via a camera guide (oval overlay, auto-capture)
2. Analyses face shape (6 classes) and skin undertone (warm/cool/neutral) using MediaPipe + EfficientNet
3. Recommends top 10 eyeglass frames from a curated catalogue (shows 5, expands to 10)
4. Generates photorealistic images of the user wearing their chosen frame via fal.ai FLUX.1 Kontext
5. Links directly to buy the frame from the retailer

**Read these files first:**
- `SPEC.md` — full product specification, user flow, all pipeline steps
- `PRD.md` — functional and non-functional requirements
- `TECH_STACK.md` — all technology decisions with reasoning
- `SPRINT_PLAN.md` — what to build in each sprint
- `API_CONTRACT.md` — all endpoints, request/response schemas, DB schema
- `RECOMMENDATION_RULES.md` — the complete recommendation logic
- `DATA_PIPELINE.md` — full scrape → process → annotate → load plan for the frame catalogue

---

## Current Sprint

**Sprint 1 — Backend Foundation**

Build these in order:
1. FastAPI project scaffold (`/backend`)
2. Cloudflare R2 integration (upload + presigned URLs)
3. Supabase tables (sessions, jobs, frames)
4. `POST /upload` endpoint
5. MediaPipe face landmark extraction
6. Face shape classifier (geometric rules + EfficientNet fallback)
7. Skin undertone analysis (OpenCV LAB)
8. `GET /analysis/{job_id}` endpoint
9. Unit tests for all rule branches

---

## Project Structure

```
frameAI/
├── CLAUDE.md              ← you are here
├── SPEC.md
├── PRD.md
├── TECH_STACK.md
├── SPRINT_PLAN.md
├── API_CONTRACT.md
├── RECOMMENDATION_RULES.md
│
├── backend/               ← FastAPI Python app
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   ├── recommendations.py
│   │   └── generate.py
│   ├── services/
│   │   ├── face_analysis.py     ← MediaPipe + shape classifier
│   │   ├── undertone.py         ← OpenCV LAB analysis
│   │   ├── recommender.py       ← rule engine
│   │   ├── generation.py        ← fal.ai calls
│   │   └── storage.py           ← R2 operations
│   ├── models/
│   │   └── schemas.py           ← Pydantic models
│   ├── db/
│   │   └── supabase.py
│   └── tests/
│       ├── test_face_analysis.py
│       └── test_recommender.py
│
└── frontend/              ← Next.js 15 app (Sprint 4)
    ├── app/
    ├── components/
    └── public/
```

---

## Key Technical Decisions (don't re-discuss these)

- **Image generation:** fal.ai FLUX.1 Kontext [pro] — NOT text-prompted. Frame image passed as reference.
- **Generation is per-frame:** 1 click = 1 API call = 1 generation consumed. NOT batch.
- **Generation limit:** 3 per anonymous session, server-enforced, never resets.
- **Recommendations:** Top 15 scored server-side, top 10 returned, top 5 shown, 6–10 pre-loaded hidden.
- **Camera:** TF.js BlazeFace for alignment only. Server-side MediaPipe for actual analysis.
- **1 photo only:** Do not ask for multiple photos. Oval guide ensures quality.
- **Frame image = real product photo** from catalogue on white background, NOT AI-generated.

---

## Rules for Code

1. **Python 3.11**, `asyncio` throughout the backend
2. **Pydantic v2** for all request/response models
3. **Never trust the client** for generation count — always validate server-side
4. **Atomic increments** on `generations_used` — use `UPDATE ... RETURNING` not read-then-write
5. **Failed generations do NOT count** against the limit — only increment on success
6. **All images expire in 24h** — set `expires_at` on every R2 upload
7. **Specific error messages** always — see API_CONTRACT.md for error codes
8. **Test all rule branches** — the recommendation engine must be fully unit tested
9. **No hardcoded credentials** — use environment variables from `.env`
10. **InsightFace is research-only** — note this in comments wherever used; plan to swap before launch

---

## Environment Variables

See `TECH_STACK.md` for the full list. Create `backend/.env` from `backend/.env.example`.

---

## How to Run (once scaffolded)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Tests:
```bash
pytest tests/ -v
```

---

## Agent Skills

5 skills are active for this project. Install them once in your Claude Code environment before starting.
The other 5 from the article were deliberately excluded — see reasoning below.

### Install commands

```bash
# 1. Frontend Design (Anthropic official — production-grade UI)
npx skills add anthropics/claude-code --skill frontend-design

# 2. Code Reviewer / Simplify (Anthropic official — auto code quality pass)
npx skills add anthropics/claude-code --skill simplify

# 3. Excalidraw Diagram Generator (architecture diagrams)
npx skills add https://github.com/coleam00/excalidraw-diagram-skill --skill excalidraw-diagram

# 4. Browser Use (E2E testing + retailer frame scraping)
npx skills add https://github.com/browser-use/browser-use --skill browser-use

# 5. PlanetScale Database Skills (schema + query optimisation)
npx skills add planetscale/agent-skill
```

### When to invoke each skill

| Skill | Invoke when... | Sprint |
|---|---|---|
| `/frontend-design` | Starting any new UI screen or component | Sprint 4 |
| `/simplify` | After completing any implementation — runs automatically before presenting code | All sprints |
| `/excalidraw-diagram` | Documenting architecture, data flow, or sequence diagrams | Any |
| `/browser-use` | Running E2E tests on camera flow, or scraping retailer frame catalogues | Sprint 2 + 4 |
| `/database` (PlanetScale) | Designing schema changes, writing queries, reviewing indexes | Sprint 1 + 2 |

### Skills NOT installed and why

| Skill | Reason excluded |
|---|---|
| **Remotion** | Video creation — not needed for a web prototype |
| **Google Workspace** | No GWS dependency in this stack |
| **Valyu** | Specialised data (SEC, PubMed) — not relevant to eyewear |
| **Antigravity Awesome Skills** | 1,234 skills adds noise for a focused 4-sprint build; adds specific ones if needed |
| **Shannon (pentesting)** | Security audit — relevant only at pre-launch (Sprint 5+), not during prototype |

### Code review rule (auto-applied by /simplify)

Add this to your Claude Code session config so the simplify skill runs automatically:

```
## Code Review Standards
After completing any implementation, run /simplify and check for:
- Functions longer than 30 lines (likely doing too much)
- Logic duplicated more than twice (extract to utility)
- Any untyped parameters in Python (add type hints)
- Missing error handling on async operations
- N+1 query patterns in DB calls
- Hardcoded values that should be environment variables
```