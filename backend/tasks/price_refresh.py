"""
Celery task: weekly lightweight price refresh from retailer listing APIs.

Hits JSON listing endpoints only (no Playwright, no images).
Titan and Ray-Ban require full re-scrape (monthly, manual).
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from supabase import create_client

from celery_app import celery_app
from config import settings

log = logging.getLogger(__name__)

_LENSKART_LISTING_API = (
    "https://www.lenskart.com/rest/v2/catalog/category/eyeglasses"
    "?page={page}&pageSize=48&gender={gender}&format=json"
)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.lenskart.com/eyeglasses.html",
}
_MAX_PAGES_PER_GENDER = 10  # ~480 listings per gender; enough for price sync


@celery_app.task(name="tasks.price_refresh.refresh_prices")
def refresh_prices() -> dict:
    """Re-scrape Lenskart listing prices and update frames table."""
    return asyncio.run(_run())


async def _run() -> dict:
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)

    async with httpx.AsyncClient(timeout=20, headers=_HEADERS) as http:
        prices = await _fetch_lenskart_prices(http)

    if not prices:
        log.warning("Price refresh: no prices fetched — Lenskart API may have changed")
        return {"updated": 0, "errors": 0, "total": 0}

    result = (
        supabase.table("frames")
        .select("frame_id,buy_url,retailer")
        .in_("retailer", ["Lenskart", "John Jacobs"])
        .execute()
    )
    frames = result.data or []
    now = datetime.now(timezone.utc).isoformat()
    updated = errors = 0

    for frame in frames:
        # Extract URL slug from buy_url
        # "https://www.lenskart.com/vc-e14662-c1-eyeglasses.html" → "vc-e14662-c1-eyeglasses"
        buy_url: str = frame.get("buy_url", "")
        slug = buy_url.rstrip("/").split("/")[-1].replace(".html", "")
        new_price = prices.get(slug)

        if new_price:
            try:
                supabase.table("frames").update({
                    "price_inr": new_price,
                    "scraped_at": now,
                }).eq("frame_id", frame["frame_id"]).execute()
                updated += 1
            except Exception:
                log.exception("Failed to update price for frame %s", frame["frame_id"])
                errors += 1

    log.info("Price refresh complete: %d updated, %d errors / %d total frames", updated, errors, len(frames))
    return {"updated": updated, "errors": errors, "total": len(frames)}


async def _fetch_lenskart_prices(http: httpx.AsyncClient) -> dict[str, int]:
    """Return {url_key: price_inr} from Lenskart listing API pages."""
    prices: dict[str, int] = {}

    for gender in ("men", "women"):
        for page in range(_MAX_PAGES_PER_GENDER):
            try:
                resp = await http.get(
                    _LENSKART_LISTING_API.format(page=page, gender=gender)
                )
                if resp.status_code != 200:
                    break
                body = resp.json()
                products = (
                    body.get("result", {}).get("products")
                    or body.get("data", {}).get("products")
                    or []
                )
                if not products:
                    break

                for p in products:
                    url_key: str = p.get("url_key") or ""
                    raw_price = p.get("special_price") or p.get("price") or 0
                    if url_key:
                        try:
                            prices[url_key] = int(float(str(raw_price).replace(",", "")))
                        except (ValueError, TypeError):
                            pass

                await asyncio.sleep(1.5)
            except Exception:
                log.exception("Lenskart API %s page %d failed", gender, page)
                break

    log.info("Fetched %d Lenskart prices across men/women listings", len(prices))
    return prices
