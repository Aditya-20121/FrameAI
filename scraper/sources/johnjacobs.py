"""
John Jacobs scraper.

John Jacobs shares Lenskart's platform — same API structure, same HTML.
We reuse LenskartScraper with the JJ base URL and retailer name.
"""
import logging
from pathlib import Path

from config import SOURCES, STYLE_MAP, COLOUR_MAP
from sources.lenskart import LenskartScraper

log = logging.getLogger(__name__)

SOURCE = SOURCES["johnjacobs"]


class JohnJacobsScraper(LenskartScraper):
    retailer = "John Jacobs"
    source_key = "johnjacobs"

    def __init__(self, raw_dir: Path):
        super().__init__(raw_dir)
        # Override source URLs to use JJ's domain
        import config as cfg
        cfg.SOURCES["lenskart"]["listing_api"] = SOURCE["listing_api"]
        cfg.SOURCES["lenskart"]["product_base_url"] = SOURCE["product_base_url"]

    async def scrape_all(self) -> list[dict]:
        # Use parent's scrape logic but checkpoint under johnjacobs prefix
        listings = self.load_checkpoint("johnjacobs_listings")
        if not listings:
            import httpx
            listings = []
            genders = ["men", "women"]
            async with httpx.AsyncClient(follow_redirects=True) as client:
                for gender in genders:
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
                                record["source"] = "johnjacobs"
                                record["retailer"] = self.retailer
                                record["buy_url"] = record["buy_url"].replace(
                                    "lenskart.com", "johnjacobs.com"
                                )
                                listings.append(record)
                        page += 1
            self.save_checkpoint(listings, "johnjacobs_listings")

        import httpx
        details = self.load_checkpoint("johnjacobs_details") or []
        scraped_ids = {d["source_id"] for d in details}
        pending = [p for p in listings if p["source_id"] not in scraped_ids]

        async with httpx.AsyncClient(follow_redirects=True) as client:
            for i, product in enumerate(pending):
                detail = await self._scrape_detail(client, product)
                detail["source"] = "johnjacobs"
                detail["retailer"] = self.retailer
                details.append(detail)
                if (i + 1) % 100 == 0:
                    self.save_checkpoint(details, "johnjacobs_details")

        self.save_checkpoint(details, "johnjacobs_details")
        return details
