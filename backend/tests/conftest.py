"""
pytest configuration — no external services needed for unit tests.
"""
import sys
import os

# Ensure backend/ is on the path so imports work without pip install -e
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Dummy required settings so config.py/db/client.py import cleanly without a
# real .env. Tests that need specific DB/API behaviour monkeypatch db.client
# or services directly rather than hitting real Supabase/Segmind.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("R2_ACCOUNT_ID", "test-account")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-secret")
os.environ.setdefault("SESSION_SECRET", "x" * 32)

import pytest
from db import client as db


@pytest.fixture(autouse=True)
def _no_network_analytics(monkeypatch):
    """Every request goes through main.py's RequestLoggingMiddleware, which
    writes to Supabase. Route it to a no-op in tests so the suite never makes
    a real network call (and never waits out a DNS failure on the dummy
    SUPABASE_URL) just because a request happened."""
    monkeypatch.setattr(db, "insert_event", lambda *a, **kw: None)
