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
        Intercept Lenskart's paginated XHR API via Playwright + incremental scrolling.

        Lenskart fires XHR to /v1/cms/category/{id} on scroll (Intersection Observer).
        Scrolling by viewport/2 increments reliably triggers each batch load.
        Each XHR response contains TYPE_PRODUCT_CLARITY widgets with colorOptions —
        each colorOption has a `url` field with the full product buy URL.
        """
        listing_pages = [
            ("https://www.lenskart.com/men-eyeglasses.html", "men"),
            ("https://www.lenskart.com/women-eyeglasses.html", "women"),
        ]
        # vp/4 increments reliably trigger Lenskart's Intersection Observer;
        # vp/2 steps skip some trigger points and stall at ~60 products.
        # XHR batches arrive every ~28-30 scrolls, so stall threshold must exceed that.
        _SCROLL_STEP_DIV = 4   # scroll by viewport/4 per step
        _MAX_SCROLLS = 120     # 120 × vp/4 ≈ 22 000px — enough for 250+ products per gender
        _SCROLL_PAUSE = 0.5    # seconds between scrolls
        _MAX_STALL = 35        # stop if no new products in this many consecutive scrolls

        all_products: dict[str, dict] = {}  # product_url → record (global dedup)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(extra_http_headers=BROWSER_HEADERS)

            for listing_url, gender in listing_pages:
                page = await context.new_page()
                captured: dict[str, dict] = {}  # url → record for this gender

                async def on_response(resp, _gender=gender, _captured=captured):
                    if "v1/cms/category" not in resp.url:
                        return
                    try:
                        body = await resp.json()
                        for widget in body.get("result", []):
                            if widget.get("widgetType") != "TYPE_PRODUCT_CLARITY":
                                continue
                            wdata = widget.get("data", {})
                            for opt in wdata.get("colorOptions", []):
                                record = self._extract_coloropt_record(opt, wdata, _gender)
                                if record and record["product_url"] not in _captured:
                                    _captured[record["product_url"]] = record
                    except Exception as exc:
                        log.debug("XHR parse error: %s", exc)

                page.on("response", on_response)

                try:
                    await page.goto(
                        listing_url, wait_until="domcontentloaded", timeout=30000
                    )
                    try:
                        await page.click("button:has-text('Allow all')", timeout=4000)
                    except Exception:
                        pass
                    await asyncio.sleep(3)  # let initial XHRs fire

                    viewport_height = await page.evaluate("() => window.innerHeight")
                    prev_count = 0
                    stall_count = 0

                    for i in range(_MAX_SCROLLS):
                        scroll_y = (i + 1) * (viewport_height // _SCROLL_STEP_DIV)
                        await page.evaluate(f"window.scrollTo(0, {scroll_y})")
                        await asyncio.sleep(_SCROLL_PAUSE)

                        curr_count = len(captured)
                        if curr_count == prev_count:
                            stall_count += 1
                            if stall_count >= _MAX_STALL:
                                log.info(
                                    "Lenskart %s: stalled at %d products after scroll %d",
                                    gender, curr_count, i + 1,
                                )
                                break
                        else:
                            stall_count = 0
                        prev_count = curr_count

                        if (i + 1) % 20 == 0:
                            log.info(
                                "Lenskart %s: %d products after %d scrolls",
                                gender, curr_count, i + 1,
                            )

                    log.info(
                        "Lenskart Playwright %s: %d products via XHR", gender, len(captured)
                    )
                    all_products.update(captured)

                except Exception as exc:
                    log.warning("Lenskart Playwright %s failed: %s", listing_url, exc)
                finally:
                    await page.close()

            await browser.close()

        result = list(all_products.values())
        log.info("Lenskart Playwright total: %d products", len(result))
        return result

    def _extract_coloropt_record(self, opt: dict, wdata: dict, gender: str) -> dict | None:
        """Build a normalised record from a Lenskart XHR colorOption object."""
        import re as _re
        try:
            url = opt.get("url", "")
            if not url or "lenskart.com" not in url:
                return None

            # Price: prefer Sales Price, fall back to Lenskart Price
            price = None
            for price_list in (opt.get("pricesV2"), opt.get("prices")):
                if not price_list:
                    continue
                for p in price_list:
                    if p.get("name") == "Sales Price" and p.get("price"):
                        price = int(float(p["price"]))
                        break
                if price:
                    break
            if not price:
                for price_list in (opt.get("pricesV2"), opt.get("prices")):
                    if not price_list:
                        continue
                    for p in price_list:
                        if p.get("name") == "Lenskart Price" and p.get("price"):
                            price = int(float(p["price"]))
                            break
                    if price:
                        break

            # Source ID: slug without suffix
            slug = url.split("/")[-1].replace("-eyeglasses.html", "").replace(".html", "")

            # Name: brand + model_name
            brand = opt.get("brandName") or wdata.get("brandName") or opt.get("title") or ""
            model = opt.get("model_name") or ""
            name = f"{brand} {model}".strip() if brand else model

            # Frame colour from API field
            frame_colour = (opt.get("frameColor") or "").lower().strip()
            raw_colour = frame_colour
            colour = None
            for kw in COLOUR_MAP:
                if kw in raw_colour:
                    colour = COLOUR_MAP[kw]
                    break

            # Style: scan URL slug and name for known keywords
            raw_style = ""
            search_text = f"{slug} {name}".lower()
            for kw in STYLE_MAP:
                if kw in search_text:
                    raw_style = kw
                    break

            # Image: first from imageUrls list, else imageUrl
            image_urls = opt.get("imageUrls") or []
            image_url = image_urls[0] if image_urls else opt.get("imageUrl")

            return {
                "source": self.source_key,
                "source_id": slug,
                "name": name,
                "product_url": url,
                "image_url": image_url,
                "raw_style": raw_style,
                "style": STYLE_MAP.get(raw_style) if raw_style else None,
                "raw_colour": raw_colour,
                "colour": colour,
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
            log.debug("coloropt extract failed: %s", exc)
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
