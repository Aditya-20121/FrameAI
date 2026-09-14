"""
pytest configuration for the scraper pipeline tests — no network, no
Playwright, no real Supabase/R2 needed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# scraper/config.py requires these as raw env vars at import time (it's
# shared config for the live scrape/load pipeline, which does need real
# credentials) — dummy values so importing it for unit tests doesn't need
# backend/.env present.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("R2_ACCOUNT_ID", "test-account")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-secret")
