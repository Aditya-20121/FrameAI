"""
Titan Eye+ scraper.

Titan Eye+ is a Next.js site. Product listings are available via their
internal API (intercepted from Network tab). Product detail pages require
Playwright for JS rendering.

If the internal API changes, fall back to Playwright for listing pages too
by setting TITAN_USE_PLAYWRIGHT=1 in your env.
"""
import asyncio
import logging
import os
from pathlib import Path

import httpx
from playwright.async_api import async_playwright, Browser, Page

from config import SOURCES, STYLE_MAP, COLOUR_MAP, CHECKPOINT_EVERY, PLAYWRIGHT_TIMEOUT_MS, BROWSER_HEADERS
from sources.base import BaseScraper

log = logging.getLogger(__name__)

SOURCE = SOURCES["titan"]
USE_PLAYWRIGHT = os.environ.get("TITAN_USE_PLAYWRIGHT", "0") == "1"


class TitanScraper(BaseScraper):
    retailer = "Titan Eye+"
    source_key = "titan"

    async def scrape_all(self) -> list[dict]:
        listings = self.load_checkpoint("titan_listings")
        if not listings:
            listings = await self._scrape_listings()
            self.save_checkpoint(listings, "titan_listings")

        log.info("Titan listings: %d products", len(listings))

        details = self.load_checkpoint("titan_details") or []
        scraped_ids = {d["source_id"] for d in details}
        pending = [p for p in listings if p["source_id"] not in scraped_ids]

        log.info("Fetching Titan details for %d products...", len(pending))
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            for i, product in enumerate(pending):
                detail = await self._scrape_detail_playwright(browser, product)
                details.append(detail)
                if (i + 1) % CHECKPOINT_EVERY == 0:
                    self.save_checkpoint(details, "titan_details")
                    log.info("Titan progress: %d/%d", i + 1, len(pending))
            await browser.close()

        self.save_checkpoint(details, "titan_details")
        return details

    # ── Listing scraper ───────────────────────────────────────────────────────

    async def _scrape_listings(self) -> list[dict]:
        """Try REST API first; auto-fall back to Playwright if it returns nothing."""
        all_products: list[dict] = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            page = 1
            while True:
                # Category is in the URL path; paginate with page + limit
                params = {"page": page, "limit": SOURCE["page_size"]}
                data = await self.get_json(client, SOURCE["listing_api"], params)
                if not data:
                    break

                products = (
                    data.get("products")
                    or data.get("data", {}).get("products")
                    or data.get("items")
                    or data.get("result", {}).get("products")
                    or (data if isinstance(data, list) else [])
                )
                if not products:
                    break

                for p in products:
                    record = self._extract_listing_fields(p)
                    if record:
                        all_products.append(record)

                log.info("Titan page %d: +%d products (total %d)", page, len(products), len(all_products))
                if len(products) < SOURCE["page_size"]:
                    break
                page += 1

        if not all_products:
            log.info("Titan REST API returned nothing — falling back to Playwright listing")
            all_products = await self._scrape_listings_playwright()

        return all_products

    async def _scrape_listings_playwright(self) -> list[dict]:
        """Scrape Titan listing page via Playwright: intercepts XHR and reads __NEXT_DATA__."""
        captured: list[dict] = []
        listing_url = f"{SOURCE['product_base_url']}/eyeglasses"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(extra_http_headers=BROWSER_HEADERS)
            page = await context.new_page()

            async def _on_response(response):
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type:
                    return
                try:
                    body = await response.json()
                    products = (
                        body.get("products")
                        or body.get("data", {}).get("products")
                        or body.get("items")
                        or []
                    )
                    if products:
                        captured.extend(products)
                        log.info("Titan intercepted %d products from %s", len(products), response.url)
                except Exception:
                    pass

            page.on("response", _on_response)

            try:
                await page.goto(listing_url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT_MS)

                if not captured:
                    # Next.js embeds server-side data in __NEXT_DATA__
                    next_data = await page.evaluate("""
                        () => {
                            const el = document.getElementById('__NEXT_DATA__');
                            return el ? JSON.parse(el.textContent) : null;
                        }
                    """)
                    if next_data:
                        props = next_data.get("props", {}).get("pageProps", {})
                        for key in ("products", "items"):
                            products = props.get(key) or props.get("data", {}).get(key, [])
                            if products:
                                captured.extend(products)
                                break
                        log.info("Titan __NEXT_DATA__: %d products", len(captured))
            except Exception as exc:
                log.warning("Titan Playwright listing failed: %s", exc)
            finally:
                await browser.close()

        all_products: list[dict] = []
        for p in captured:
            record = self._extract_listing_fields(p)
            if record:
                all_products.append(record)

        log.info("Titan Playwright listing: %d products extracted", len(all_products))
        return all_products

    def _extract_listing_fields(self, p: dict) -> dict | None:
        try:
            sku = str(p.get("sku") or p.get("id") or p.get("product_id") or "")
            product_url = f"{SOURCE['product_base_url']}/product/{sku}"

            images = p.get("images") or p.get("image") or []
            if isinstance(images, str):
                images = [images]
            image_url = images[0] if images else None
            if isinstance(image_url, dict):
                image_url = image_url.get("url") or image_url.get("src")

            raw_style = str(p.get("frame_shape") or p.get("frameShape") or p.get("shape") or "")
            raw_colour = str(p.get("colour") or p.get("frame_colour") or p.get("color") or "")

            return {
                "source": "titan",
                "source_id": sku,
                "name": str(p.get("name") or p.get("title") or ""),
                "product_url": product_url,
                "image_url": image_url,
                "raw_style": raw_style.lower().strip(),
                "style": STYLE_MAP.get(raw_style.lower().strip()),
                "raw_colour": raw_colour.lower().strip(),
                "colour": COLOUR_MAP.get(raw_colour.lower().strip()),
                "price_inr": self.parse_price(p.get("price") or p.get("mrp")),
                "gender_tag": str(p.get("gender") or "unisex").lower(),
                "retailer": self.retailer,
                "buy_url": product_url,
                "lens_width_mm": None,
                "bridge_width_mm": None,
                "temple_length_mm": None,
                "material": None,
            }
        except Exception as exc:
            log.debug("Titan listing extract failed: %s", exc)
            return None

    # ── Detail scraper (Playwright) ───────────────────────────────────────────

    async def _scrape_detail_playwright(self, browser: Browser, product: dict) -> dict:
        page: Page | None = None
        try:
            page = await browser.new_page()
            await page.set_extra_http_headers(BROWSER_HEADERS)
            await page.goto(product["product_url"], wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT_MS)

            # Extract spec table via JS evaluation
            specs = await page.evaluate("""
                () => {
                    const result = {};
                    // Strategy 1: table rows
                    document.querySelectorAll('table tr, .specs tr, .product-specs tr').forEach(row => {
                        const label = row.querySelector('th, .label, td:first-child');
                        const value = row.querySelector('td:last-child, .value');
                        if (label && value) {
                            result[label.textContent.trim().toLowerCase()] = value.textContent.trim();
                        }
                    });
                    // Strategy 2: dl/dt/dd
                    document.querySelectorAll('dl').forEach(dl => {
                        const dts = dl.querySelectorAll('dt');
                        const dds = dl.querySelectorAll('dd');
                        dts.forEach((dt, i) => {
                            if (dds[i]) result[dt.textContent.trim().toLowerCase()] = dds[i].textContent.trim();
                        });
                    });
                    return result;
                }
            """)

            if specs:
                dim_str = " ".join(specs.values())
                lens_w, bridge_w, temple_l = self.parse_dimensions(dim_str)
                product["lens_width_mm"] = lens_w or product.get("lens_width_mm")
                product["bridge_width_mm"] = bridge_w or product.get("bridge_width_mm")
                product["temple_length_mm"] = temple_l or product.get("temple_length_mm")
                # Material
                for key in ("material", "frame material"):
                    if key in specs:
                        product["material"] = specs[key].lower()
                        break

            # Try to get a better product image
            img_url = await page.evaluate("""
                () => {
                    const og = document.querySelector('meta[property="og:image"]');
                    if (og) return og.content;
                    const img = document.querySelector('.product-image img, .gallery img');
                    return img ? img.src : null;
                }
            """)
            if img_url:
                product["image_url"] = img_url

        except Exception as exc:
            log.warning("Titan detail scrape failed for %s: %s", product["product_url"], exc)
        finally:
            if page:
                await page.close()

        return product
