import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from api import upload, analysis, recommendations, generate, catalogue
from config import settings

log = logging.getLogger(__name__)

# ── Rate limiter (in-memory, per-process) ─────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FrameAI API",
    version="1.0.0",
    description="AI-powered eyeglass frame recommendation engine",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security headers ──────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]         = "DENY"
        response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]      = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"]        = "1; mode=block"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload.router,          tags=["upload"])
app.include_router(analysis.router,        tags=["analysis"])
app.include_router(recommendations.router, tags=["recommendations"])
app.include_router(generate.router,        tags=["generate"])
app.include_router(catalogue.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
