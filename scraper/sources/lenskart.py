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
from playwright.async_api import async_playwright

from config import SOURCES, STYLE_MAP, COLOUR_MAP, CHECKPOINT_EVERY, BROWSER_HEADERS, PLAYWRIGHT_TIMEOUT_MS
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
        """Try JSON API first; fall back to HTML __NEXT_DATA__ if API redirects/fails."""
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

        if not all_products:
            log.info(
                "Lenskart JSON API unavailable (403/redirect) — falling back to Playwright"
            )
            all_products = await self._scrape_listings_playwright()

        return all_products

    async def _scrape_listings_playwright(self) -> list[dict]:
        """
        Scrape lenskart.com SSR listing pages via Playwright DOM evaluation.

        Lenskart renders products server-side so XHR interception misses them.
        We load the page, dismiss the cookie dialog, scroll to trigger infinite
        scroll, and extract from the live DOM using page.evaluate().
        """
        import re as _re

        # DOM extractor: finds product links by Lenskart's -cN- colour-variant URL pattern.
        # Uses closest('li') to scope each card, then walks siblings for name/price.
        _JS_EXTRACT = (
            "() => {"
            "  const results = [];"
            "  const seen = new Set();"
            "  const links = Array.from(document.querySelectorAll("
            "    'a[href*=\"-c1-\"], a[href*=\"-c2-\"], a[href*=\"-c3-\"], a[href*=\"-c4-\"]'"
            "  ));"
            "  links.forEach(link => {"
            "    const href = link.href;"
            "    if (!href || !href.includes('lenskart.com')) return;"
            "    if (seen.has(href)) return; seen.add(href);"
            "    const card = link.closest('li') || link.closest('[class]') || link.parentElement;"
            "    const cardText = card ? card.innerText : '';"
            "    const img = card ? card.querySelector('img') : null;"
            "    results.push({"
            "      url: href,"
            "      card_text: cardText.substring(0, 500),"
            "      image_url: img ? img.src : null,"
            "    });"
            "  });"
            "  return results;"
            "}"
        )

        listing_pages = [
            ("https://www.lenskart.com/men-eyeglasses.html", "men"),
            ("https://www.lenskart.com/women-eyeglasses.html", "women"),
        ]
        _MAX_SCROLLS = 8  # each scroll loads ~12 more products
        captured: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(extra_http_headers=BROWSER_HEADERS)

            for page_url, gender in listing_pages:
                page = await context.new_page()
                try:
                    await page.goto(
                        page_url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS
                    )
                    # Dismiss cookie / privacy dialog
                    try:
                        await page.click("button:has-text('Allow all')", timeout=4000)
                    except Exception:
                        pass
                    await asyncio.sleep(3)

                    # Scroll to trigger infinite scroll pagination
                    seen_count = 0
                    for _ in range(_MAX_SCROLLS):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)
                        raw = await page.evaluate(_JS_EXTRACT)
                        if len(raw) == seen_count:
                            break  # no new products loaded
                        seen_count = len(raw)

                    raw_items = await page.evaluate(_JS_EXTRACT)
                    log.info("Lenskart Playwright %s: %d raw DOM items", gender, len(raw_items))

                    for item in raw_items:
                        record = self._extract_dom_record(item, gender)
                        if record:
                            captured.append(record)

                except Exception as exc:
                    log.warning("Lenskart Playwright %s failed: %s", gender, exc)
                finally:
                    await page.close()

            await browser.close()

        log.info("Lenskart Playwright fallback: %d products", len(captured))
        return captured

    def _extract_dom_record(self, item: dict, gender: str) -> dict | None:
        """Parse a DOM-extracted product dict into a normalised record."""
        import re as _re
        try:
            url = item.get("url", "")
            if not url:
                return None

            card_text: str = item.get("card_text", "")
            lines = [l.strip() for l in card_text.split("\n") if l.strip()]

            # Name: line immediately after a "+ N" colour-count line (e.g. "+ 4")
            name = ""
            for i, line in enumerate(lines):
                if _re.match(r"^\+\s*\d+$", line) and i + 1 < len(lines):
                    name = lines[i + 1]
                    break
            if not name:
                # Fall back to slug
                slug = url.split("/")[-1]
                name = _re.sub(r"-c\d+-eyeglasses.*", "", slug).replace("-", " ")

            # Price: first 3-5 digit number in reasonable range
            price = None
            for line in lines:
                m = _re.search(r"(\d{3,5})", line)
                if m and 300 <= int(m.group(1)) <= 30000:
                    price = int(m.group(1))
                    break

            # Source ID from URL slug
            slug = url.split("/")[-1]
            source_id = slug.replace("-eyeglasses.html", "").replace(".html", "")

            # Style / colour from name keywords
            raw_style = ""
            for kw in STYLE_MAP:
                if kw in name.lower():
                    raw_style = kw
                    break
            raw_colour = ""
            for kw in COLOUR_MAP:
                if kw in name.lower():
                    raw_colour = kw
                    break

            return {
                "source": self.source_key,
                "source_id": source_id,
                "name": name,
                "product_url": url,
                "image_url": item.get("image_url"),
                "raw_style": raw_style,
                "style": STYLE_MAP.get(raw_style) if raw_style else None,
                "raw_colour": raw_colour,
                "colour": COLOUR_MAP.get(raw_colour) if raw_colour else None,
                "price_inr": price,
                "gender_tag": gender,
                "retailer": self.retailer,
                "buy_url": url,
                "lens_width_mm": None,
                "bridge_width_mm": None,
                "temple_length_mm": None,
                "material": None,
            }
        except Exception as exc:
            log.debug("DOM record extract failed: %s", exc)
            return None

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
