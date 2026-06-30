"""
Session management helpers for FastAPI endpoints.
Session token lives in an HttpOnly cookie named `_frameai_session`.
"""
import os
from fastapi import Cookie, Response

from db import client as db

COOKIE_NAME = "_frameai_session"
COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year

# On production (HTTPS) use Secure + SameSite=None for cross-origin cookies.
# On local dev (HTTP) Secure must be False or browsers reject the cookie.
_IS_PROD = os.getenv("ENVIRONMENT", "development").lower() == "production"


def get_or_create_session(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> str:
    """
    FastAPI dependency — returns the session token, creating one if needed.
    Attaches the cookie to the response if a new session was created.
    """
    if session_token:
        session = db.get_session(session_token)
        if session:
            db.touch_session(session_token)
            return session_token

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
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> str:
    """
    FastAPI dependency — requires an existing session.
    Raises 401 if missing or unknown.
    """
    from fastapi import HTTPException
    if not session_token:
        raise HTTPException(status_code=401, detail="No session found. Upload a photo first.")
    session = db.get_session(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired. Please start over.")
    return session_token
