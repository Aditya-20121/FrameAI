"""
Session management helpers for FastAPI endpoints.
Session token lives in an HttpOnly cookie named `_frameai_session`.
For cross-domain deployments (e.g. Vercel + Render on different domains) browsers
block third-party cookies, so every response also returns the token in the body and
clients send it back via the X-Session-Token header.
"""
import os
from fastapi import Cookie, Header, HTTPException, Response

from db import client as db

COOKIE_NAME = "_frameai_session"
COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year

# On production (HTTPS) use Secure + SameSite=None for cross-origin cookies.
# On local dev (HTTP) Secure must be False or browsers reject the cookie.
_IS_PROD = os.getenv("ENVIRONMENT", "development").lower() == "production"


def get_or_create_session(
    response: Response,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> str:
    """
    FastAPI dependency — returns the session token, creating one if needed.
    Checks X-Session-Token header first (cross-domain clients), then cookie.
    Attaches the cookie to the response if a new session was created.
    """
    token = x_session_token or session_token
    if token:
        session = db.get_session(token)
        if session:
            db.touch_session(token)
            return token

    # Create fresh session
    token = db.create_session()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="none" if _IS_PROD else "lax",
        secure=_IS_PROD,
        max_age=COOKIE_MAX_AGE,
    )
    return token


def require_session(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> str:
    """
    FastAPI dependency — requires an existing session.
    Checks X-Session-Token header first (cross-domain clients), then cookie.
    Raises 401 if missing or unknown.
    """
    token = x_session_token or session_token
    if not token:
        raise HTTPException(status_code=401, detail="No session found. Upload a photo first.")
    session = db.get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired. Please start over.")
    db.touch_session(token)
    return token
