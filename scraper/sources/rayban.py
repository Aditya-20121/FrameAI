"""
Ray-Ban India scraper.

Ray-Ban uses Salesforce Commerce Cloud. We scrape product listings only
(name, price, style, image, buy URL) — no deep detail scraping to respect
their ToS. ~200–300 eyeglass SKUs.

Per DATA_PIPELINE.md: "Scrape only the public product listing."
"""
import asyncio
import logging
from pathlib import Path

import httpx
from playwright.async_api import async_playwright

from config import SOURCES, STYLE_MAP, COLOUR_MAP, BROWSER_HEADERS, PLAYWRIGHT_TIMEOUT_MS
from sources.base import BaseScraper

log = logging.getLogger(__name__)

SOURCE = SOURCES["rayban"]

# Ray-Ban India eyeglasses category ID for their Commerce Cloud API
_RB_CATEGORY = "eyeglasses"


class RayBanScraper(BaseScraper):
    retailer = "Ray-Ban"
    source_key = "rayban"

    async def scrape_all(self) -> list[dict]:
        listings = self.load_checkpoint("rayban_listings")
        if not listings:
            listings = await self._scrape_listings()
            self.save_checkpoint(listings, "rayban_listings")

        log.info("Ray-Ban listings: %d products", len(listings))
        # No detail scraping for Ray-Ban
        return listings

    async def _scrape_listings(self) -> list[dict]:
        all_products: list[dict] = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            start = 0
            while True:
                params = {
                    "category": _RB_CATEGORY,
                    "start": start,
                    "sz": SOURCE["page_size"],
                    "format": "json",
                }
                data = await self.get_json(client, SOURCE["listing_api"], params)
                if not data:
                    break

                hits = (
                    data.get("hits")
                    or data.get("products")
                    or data.get("productSearchResult", {}).get("hits")
                    or []
                )
                if not hits:
                    break

                for p in hits:
                    record = self._extract_fields(p)
                    if record:
                        all_products.append(record)

                total = data.get("total") or data.get("count") or 0
                log.info("Ray-Ban start=%d: +%d (total available: %s)", start, len(hits), total)
                start += SOURCE["page_size"]
                if start >= (total or len(all_products)):
                    break

        if not all_products:
            log.info("Ray-Ban API returned nothing (likely 403) — falling back to Playwright")
            all_products = await self._scrape_listings_playwright()

        return all_products

    async def _scrape_listings_playwright(self) -> list[dict]:
        """
        Scrape Ray-Ban India eyeglasses listing via Playwright.

        Ray-Ban uses Salesforce Commerce Cloud with XHR product loading.
        We intercept XHR responses containing product hits.
        Listing URL: https://www.ray-ban.com/en_IN/c/eyeglasses
        """
        _LISTING_URL = "https://www.ray-ban.com/en_IN/c/eyeglasses"
        _MAX_SCROLLS = 10
        captured_hits: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(extra_http_headers=BROWSER_HEADERS)
            page = await context.new_page()

            async def _on_response(resp):
                if resp.status != 200:
                    return
                ct = resp.headers.get("content-type", "")
                if "json" not in ct:
                    return
                try:
                    body = await resp.json()
                    hits = (
                        body.get("hits")
                        or body.get("productSearchResult", {}).get("hits")
                        or body.get("products")
                        or []
                    )
                    if hits:
                        captured_hits.extend(hits)
                        log.info("Ray-Ban intercepted %d hits from %s", len(hits), resp.url[:80])
                except Exception:
                    pass

            page.on("response", _on_response)

            try:
                await page.goto(_LISTING_URL, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
                await asyncio.sleep(3)

                prev_count = 0
                for _ in range(_MAX_SCROLLS):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                    if len(captured_hits) == prev_count:
                        break
                    prev_count = len(captured_hits)

                log.info("Ray-Ban Playwright: %d raw hits intercepted", len(captured_hits))
            except Exception as exc:
                log.warning("Ray-Ban Playwright listing failed: %s", exc)
            finally:
                await browser.close()

        all_products = []
        for p in captured_hits:
            record = self._extract_fields(p)
            if record:
                all_products.append(record)

        log.info("Ray-Ban Playwright: %d products extracted", len(all_products))
        return all_products

    def _extract_fields(self, p: dict) -> dict | None:
        try:
            product_id = str(p.get("productId") or p.get("id") or "")
            slug = str(p.get("productName") or p.get("name") or "").lower().replace(" ", "-")
            buy_url = f"{SOURCE['product_base_url']}/p/{product_id}"

            # Image: prefer the clean white-background swatch image
            images = p.get("images") or {}
            if isinstance(images, dict):
                large = images.get("large") or images.get("medium") or []
                image_url = large[0].get("url") if large else None
            elif isinstance(images, list):
                image_url = images[0].get("url") if images else None
            else:
                image_url = None

            raw_style = str(
                p.get("frameShape")
                or p.get("frame_shape")
                or p.get("attributes", {}).get("frameShape", "")
            )
            raw_colour = str(
                p.get("colour")
                or p.get("frame_colour")
                or p.get("variationAttributes", [{}])[0].get("displayValue", "")
                if p.get("variationAttributes") else p.get("colour", "")
            )

            price_raw = (
                p.get("price")
                or p.get("pricing", {}).get("sale")
                or p.get("prices", {}).get("sale", {}).get("value")
            )

            return {
                "source": "rayban",
                "source_id": product_id,
                "name": str(p.get("productName") or p.get("name") or ""),
                "product_url": buy_url,
                "image_url": image_url,
                "raw_style": raw_style.lower().strip(),
                "style": STYLE_MAP.get(raw_style.lower().strip()),
                "raw_colour": raw_colour.lower().strip(),
                "colour": COLOUR_MAP.get(raw_colour.lower().strip()),
                "price_inr": self.parse_price(price_raw),
                "gender_tag": "unisex",
                "retailer": self.retailer,
                "buy_url": buy_url,
                "lens_width_mm": None,
                "bridge_width_mm": None,
                "temple_length_mm": None,
                "material": "metal",  # Ray-Ban typically metal or acetate
            }
        except Exception as exc:
            log.debug("Ray-Ban extract failed: %s", exc)
            return None
