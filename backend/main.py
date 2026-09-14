import logging
import time

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from logging_config import configure_logging
from limiter import limiter
from api import upload, analysis, recommendations, generate, catalogue
from config import settings
from services import analytics

configure_logging()
log = structlog.get_logger(__name__)

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


# ── Request logging + analytics ─────────────────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request as structured JSON and mirrors it to PostHog as
    `api_request` (volume, latency for P50/P95, error rate via status_code)."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            distinct_id = (
                request.headers.get("X-Session-Token")
                or request.cookies.get("_frameai_session")
                or (request.client.host if request.client else "unknown")
            )
            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            await analytics.capture(
                distinct_id=distinct_id,
                event="api_request",
                properties={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "is_error": status_code >= 400,
                },
            )


app.add_middleware(RequestLoggingMiddleware)

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
