"""
Lenskart scraper.

Listing:  Lenskart JSON API (fast, no JS rendering needed)
Details:  Product page HTML for spec table (lens/bridge/temple dims)
Genders:  men + women (separate pagination)

Lenskart API note: endpoints may change. If 403/404, check the Network tab
on lenskart.com/eyeglasses/men.html for the current endpoint path.
"""
import asyncio
import logging
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from config import SOURCES, STYLE_MAP, COLOUR_MAP, CHECKPOINT_EVERY, BROWSER_HEADERS
from sources.base import BaseScraper

log = logging.getLogger(__name__)

SOURCE = SOURCES["lenskart"]
GENDERS = ["men", "women", "unisex"]


class LenskartScraper(BaseScraper):
    retailer = "Lenskart"
    source_key = "lenskart"

    async def scrape_all(self) -> list[dict]:
        # Check for existing listing checkpoint
        listings = self.load_checkpoint("lenskart_listings")
        if not listings:
            listings = await self._scrape_listings()
            self.save_checkpoint(listings, "lenskart_listings")

        log.info("Lenskart listings: %d products", len(listings))

        # Check for details checkpoint
        details = self.load_checkpoint("lenskart_details")
        scraped_ids = {d["source_id"] for d in (details or [])}

        if details is None:
            details = []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            pending = [p for p in listings if p["source_id"] not in scraped_ids]
            log.info("Fetching details for %d products...", len(pending))

            for i, product in enumerate(pending):
                detail = await self._scrape_detail(client, product)
                details.append(detail)

                if (i + 1) % CHECKPOINT_EVERY == 0:
                    self.save_checkpoint(details, "lenskart_details")
                    log.info("Progress: %d/%d", i + 1, len(pending))

        self.save_checkpoint(details, "lenskart_details")
        return details

    # ── Listing scraper ───────────────────────────────────────────────────────

    async def _scrape_listings(self) -> list[dict]:
        all_products: list[dict] = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for gender in GENDERS:
                page = 0
                while True:
                    params = {
                        "page": page,
                        "pageSize": SOURCE["page_size"],
                        "gender": gender,
                        "format": "json",
                    }
                    data = await self.get_json(client, SOURCE["listing_api"], params)
                    if not data:
                        break

                    products = (
                        data.get("result", {}).get("products")
                        or data.get("products")
                        or []
                    )
                    if not products:
                        break

                    for p in products:
                        record = self._extract_listing_fields(p, gender)
                        if record:
                            all_products.append(record)

                    log.info("Lenskart %s page %d: +%d products", gender, page, len(products))
                    page += 1

        return all_products

    def _extract_listing_fields(self, p: dict, gender: str) -> dict | None:
        try:
            # Image: prefer the front-view image
            images = p.get("imageList") or p.get("image_urls") or []
            image_url = None
            for img in images:
                url = img.get("url") if isinstance(img, dict) else str(img)
                if url and ("front" in url.lower() or not image_url):
                    image_url = url
                    if "front" in url.lower():
                        break

            url_key = p.get("urlKey") or p.get("url_key") or p.get("slug", "")
            product_url = f"{SOURCE['product_base_url']}/{url_key}"

            raw_style = str(p.get("frameShape") or p.get("frame_shape") or "")
            raw_colour = str(p.get("frameColour") or p.get("frame_colour") or p.get("colour") or "")

            return {
                "source": "lenskart",
                "source_id": str(p.get("id") or p.get("product_id") or ""),
                "name": str(p.get("name") or ""),
                "product_url": product_url,
                "image_url": image_url,
                "raw_style": raw_style.lower().strip(),
                "style": STYLE_MAP.get(raw_style.lower().strip()),
                "raw_colour": raw_colour.lower().strip(),
                "colour": COLOUR_MAP.get(raw_colour.lower().strip()),
                "price_inr": self.parse_price(p.get("price") or p.get("special_price")),
                "gender_tag": gender,
                "retailer": self.retailer,
                "buy_url": product_url,
                # dims — filled in by detail scraper
                "lens_width_mm": None,
                "bridge_width_mm": None,
                "temple_length_mm": None,
                "material": None,
            }
        except Exception as exc:
            log.debug("Failed to extract listing fields: %s", exc)
            return None

    # ── Detail scraper ────────────────────────────────────────────────────────

    async def _scrape_detail(self, client: httpx.AsyncClient, product: dict) -> dict:
        soup = await self.get_html(client, product["product_url"])
        if not soup:
            return product

        specs = self._parse_spec_table(soup)

        lens_w, bridge_w, temple_l = self.parse_dimensions(specs)
        product["lens_width_mm"] = lens_w or product.get("lens_width_mm")
        product["bridge_width_mm"] = bridge_w or product.get("bridge_width_mm")
        product["temple_length_mm"] = temple_l or product.get("temple_length_mm")
        product["material"] = self._extract_material(soup, specs)

        # Try to get a better image URL from the product page JSON-LD
        better_image = self._extract_product_image(soup)
        if better_image:
            product["image_url"] = better_image

        return product

    @staticmethod
    def _parse_spec_table(soup: BeautifulSoup) -> dict:
        specs: dict[str, str] = {}

        # Strategy 1: table rows with th/td
        for row in soup.select("table tr, .product-spec tr, .specs-table tr"):
            th = row.select_one("th, .spec-label, .label")
            td = row.select_one("td, .spec-value, .value")
            if th and td:
                specs[th.get_text(strip=True).lower()] = td.get_text(strip=True)

        # Strategy 2: dl/dt/dd pairs
        for dl in soup.select("dl"):
            dts = dl.select("dt")
            dds = dl.select("dd")
            for dt, dd in zip(dts, dds):
                specs[dt.get_text(strip=True).lower()] = dd.get_text(strip=True)

        # Strategy 3: look for "51-18-140" style dimension string anywhere
        import re
        text = soup.get_text()
        m = re.search(r"(\d{2})-(\d{1,2})-(\d{3})", text)
        if m and "lens" not in specs:
            specs["lens_width"] = m.group(1)
            specs["bridge_width"] = m.group(2)
            specs["temple_length"] = m.group(3)

        return specs

    @staticmethod
    def _extract_material(soup: BeautifulSoup, specs: dict) -> str | None:
        import re
        # From spec table
        for key in ("material", "frame material", "lens material"):
            if key in specs:
                return specs[key].lower()

        # From page text
        text = soup.get_text().lower()
        for mat in ("acetate", "titanium", "metal", "tr90", "wood", "mixed"):
            if mat in text:
                return mat
        return None

    @staticmethod
    def _extract_product_image(soup: BeautifulSoup) -> str | None:
        import json as _json, re
        # JSON-LD product schema
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = _json.loads(script.string or "")
                if isinstance(data, dict) and data.get("@type") == "Product":
                    img = data.get("image")
                    if isinstance(img, list):
                        return img[0]
                    if isinstance(img, str):
                        return img
            except Exception:
                pass

        # og:image
        og = soup.select_one('meta[property="og:image"]')
        if og:
            return og.get("content")
        return None
