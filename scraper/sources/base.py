"""
Base class and shared utilities for all source scrapers.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncIterator

import httpx
from bs4 import BeautifulSoup
from config import BROWSER_HEADERS, RATE_LIMIT_SECONDS, MAX_CONCURRENT, CHECKPOINT_EVERY

log = logging.getLogger(__name__)


class BaseScraper:
    retailer: str = ""
    source_key: str = ""

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def scrape_all(self) -> list[dict]:
        """Run the full scrape. Returns merged list of normalised raw records."""
        raise NotImplementedError

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    async def get_json(self, client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict | list | None:
        async with self._semaphore:
            try:
                r = await client.get(url, params=params, headers=BROWSER_HEADERS, timeout=20)
                r.raise_for_status()
                return r.json()
            except Exception as exc:
                log.warning("GET %s failed: %s", url, exc)
                return None
            finally:
                await asyncio.sleep(RATE_LIMIT_SECONDS)

    async def get_html(self, client: httpx.AsyncClient, url: str) -> BeautifulSoup | None:
        async with self._semaphore:
            try:
                r = await client.get(url, headers=BROWSER_HEADERS, timeout=20)
                r.raise_for_status()
                return BeautifulSoup(r.text, "html.parser")
            except Exception as exc:
                log.warning("GET %s failed: %s", url, exc)
                return None
            finally:
                await asyncio.sleep(RATE_LIMIT_SECONDS)

    # ── Checkpoint helpers ────────────────────────────────────────────────────

    def save_checkpoint(self, records: list[dict], name: str) -> None:
        path = self.raw_dir / f"{name}.json"
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Checkpoint: saved %d records → %s", len(records), path)

    def load_checkpoint(self, name: str) -> list[dict] | None:
        path = self.raw_dir / f"{name}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            log.info("Resumed from checkpoint: %d records ← %s", len(data), path)
            return data
        return None

    # ── Dimension parsing ─────────────────────────────────────────────────────

    @staticmethod
    def parse_dimensions(spec: str | dict) -> tuple[int | None, int | None, int | None]:
        """
        Parse lens/bridge/temple from various formats:
          "51-18-140"
          "Lens: 51mm | Bridge: 18mm | Temple: 140mm"
          {"lens_width": "51", "bridge_width": "18", "temple_length": "140"}
        Returns (lens_width_mm, bridge_width_mm, temple_length_mm).
        """
        import re
        if isinstance(spec, dict):
            def _int(k):
                v = spec.get(k, "")
                digits = re.sub(r"[^\d]", "", str(v))
                return int(digits) if digits else None
            return _int("lens_width"), _int("bridge_width"), _int("temple_length")

        spec = str(spec)
        # Pattern: "51-18-140"
        m = re.search(r"(\d{2})-(\d{1,2})-(\d{3})", spec)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))

        # Pattern with labels
        lens = re.search(r"[Ll]ens[^\d]*(\d{2})", spec)
        bridge = re.search(r"[Bb]ridge[^\d]*(\d{1,2})", spec)
        temple = re.search(r"[Tt]emple[^\d]*(\d{3})", spec)
        return (
            int(lens.group(1)) if lens else None,
            int(bridge.group(1)) if bridge else None,
            int(temple.group(1)) if temple else None,
        )

    @staticmethod
    def parse_price(raw: str | int | float | None) -> int | None:
        """Parse "₹1,899", "Rs. 1899", "1899.00", "1800.000000", 1899 → 1899."""
        import re
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return int(raw)
        # Try float conversion first so "1800.000000" → 1800 (not 1800000000)
        try:
            return int(float(str(raw).replace(",", "")))
        except (ValueError, TypeError):
            pass
        digits = re.sub(r"[^\d]", "", str(raw))
        return int(digits) if digits else None
