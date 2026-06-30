"""
Playwright-based batch image downloader.

httpx cannot download Lenskart CDN images (403) because the CDN checks
TLS fingerprints and browser-specific headers that only a real Chromium
browser produces. This module opens one headless Chromium instance and
downloads all outstanding images through it.

Usage (via run.py):
    python run.py download-images
"""
import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright

log = logging.getLogger(__name__)

_REFERERS = {
    "lenskart": "https://www.lenskart.com/",
    "titan":    "https://www.titaneyeplus.com/",
}


def _referer(url: str) -> str:
    for key, ref in _REFERERS.items():
        if key in url:
            return ref
    return "https://www.google.com/"


async def download_images_playwright(
    url_map: dict[str, Path],   # {image_url: destination_path}
    concurrency: int = 8,
) -> dict[str, bool]:
    """
    Download images using a single headless Chromium browser context.
    Returns {url: success} for each entry in url_map.
    """
    results: dict[str, bool] = {}
    urls = list(url_map.keys())

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )

        sem = asyncio.Semaphore(concurrency)

        async def _fetch(url: str) -> None:
            dest = url_map[url]
            async with sem:
                try:
                    resp = await context.request.get(
                        url,
                        headers={"Referer": _referer(url)},
                        timeout=15_000,
                    )
                    if not resp.ok:
                        log.warning("HTTP %d for %s", resp.status, url[:60])
                        results[url] = False
                        return
                    body = await resp.body()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(body)
                    results[url] = True
                except Exception as exc:
                    log.warning("Download failed %s: %s", url[:60], exc)
                    results[url] = False

        await asyncio.gather(*[_fetch(u) for u in urls])
        await browser.close()

    ok  = sum(v for v in results.values())
    log.info("Downloaded %d/%d images", ok, len(urls))
    return results
