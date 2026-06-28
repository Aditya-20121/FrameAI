"""
Central config for all scraper components.
Paths, rate limits, style maps, colour maps, field names.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / "backend" / ".env")

# ── Credentials (shared with backend) ─────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY_ID = os.environ["R2_ACCESS_KEY_ID"]
R2_SECRET_ACCESS_KEY = os.environ["R2_SECRET_ACCESS_KEY"]
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "frameai")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN", "https://r2.frameai.in")

# ── Output paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
RAW_DIR = OUTPUT_DIR / "raw"
PROCESSED_DIR = OUTPUT_DIR / "processed"
IMAGES_RAW_DIR = OUTPUT_DIR / "images" / "raw"
IMAGES_NORM_DIR = OUTPUT_DIR / "images" / "normalised"
ANNOTATION_DIR = BASE_DIR / "annotation"

for d in [RAW_DIR, PROCESSED_DIR, IMAGES_RAW_DIR, IMAGES_NORM_DIR, ANNOTATION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── HTTP headers (mimic a real browser to avoid 403s) ────────────────────────
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "application/json, text/html, */*",
    "Referer": "https://www.google.com/",
}

# ── Rate limits ───────────────────────────────────────────────────────────────
RATE_LIMIT_SECONDS = 1.5       # delay between requests per domain
MAX_CONCURRENT = 2             # max parallel requests per domain
CHECKPOINT_EVERY = 100         # save progress every N products
PLAYWRIGHT_TIMEOUT_MS = 15000  # 15s max per page load

# ── Style normalisation map ───────────────────────────────────────────────────
# Maps raw source strings → our canonical schema values.
# Add entries as you discover new raw values during scraping.
STYLE_MAP: dict[str, str] = {
    # Canonical
    "rectangular": "rectangular",
    "round": "round",
    "oval": "oval",
    "square": "square",
    "cat-eye": "cat-eye",
    "aviator": "aviator",
    "wayfarer": "wayfarer",
    "browline": "browline",
    "geometric": "geometric",
    "rimless": "rimless",
    "oversized": "oversized",
    # Lenskart variants
    "rectangle": "rectangular",
    "cat eye": "cat-eye",
    "cateye": "cat-eye",
    "clubmaster": "browline",
    "club master": "browline",
    "wayfarers": "wayfarer",
    "half rim": "browline",
    "half-rim": "browline",
    "semi-rimless": "rimless",
    "rimless/supra": "rimless",
    # Titan Eye+ variants
    "rectangle frame": "rectangular",
    "round frame": "round",
    "square frame": "square",
    # John Jacobs
    "narrow rectangular": "rectangular",
    "wide rectangular": "rectangular",
    # Ray-Ban
    "phantos": "square",
    "erika": "round",
    "new wayfarer": "wayfarer",
    "clubround": "browline",
    "hexagonal": "geometric",
}

# ── Colour normalisation map ──────────────────────────────────────────────────
COLOUR_MAP: dict[str, str] = {
    # Black variants
    "black": "black",
    "matte black": "black",
    "gloss black": "black",
    "shiny black": "black",
    # Tortoiseshell
    "tortoise": "tortoiseshell",
    "tortoiseshell": "tortoiseshell",
    "tort": "tortoiseshell",
    "tortoise shell": "tortoiseshell",
    "havana": "tortoiseshell",
    # Brown
    "brown": "brown",
    "dark brown": "brown",
    "light brown": "brown",
    "chocolate": "brown",
    # Gold
    "gold": "gold",
    "golden": "gold",
    "shiny gold": "gold",
    # Silver
    "silver": "silver",
    "chrome": "silver",
    "shiny silver": "silver",
    # Rose gold
    "rose gold": "rose_gold",
    "rosegold": "rose_gold",
    "pink gold": "rose_gold",
    # Navy
    "navy": "navy",
    "navy blue": "navy",
    "dark blue": "navy",
    # Blue
    "blue": "blue",
    "sky blue": "blue",
    "cobalt": "blue",
    # Gunmetal
    "gunmetal": "gunmetal",
    "dark gunmetal": "gunmetal",
    "grey gun": "gunmetal",
    # Grey
    "grey": "cool_grey",
    "gray": "cool_grey",
    "dark grey": "cool_grey",
    "cool grey": "cool_grey",
    "light grey": "cool_grey",
    # Burgundy
    "burgundy": "burgundy",
    "wine": "burgundy",
    "maroon": "burgundy",
    "red": "burgundy",
    "wine red": "burgundy",
    # Purple
    "purple": "purple",
    "violet": "purple",
    "mauve": "purple",
    # Amber
    "amber": "amber",
    # Olive
    "olive": "olive",
    "olive green": "olive",
    "khaki": "olive",
    # Tan
    "tan": "tan",
    "sand": "tan",
    "beige": "tan",
    # Honey
    "honey": "honey",
    "honey brown": "honey",
    # Clear
    "clear": "clear",
    "transparent": "clear",
    "crystal": "clear",
    # Blush
    "blush": "blush",
    "pink": "blush",
    "light pink": "blush",
    # Warm grey
    "warm grey": "warm_grey",
    "taupe": "warm_grey",
    # Cognac
    "cognac": "cognac",
    # Caramel
    "caramel": "caramel",
    # Deep green
    "deep green": "deep_green",
    "dark green": "deep_green",
    "forest green": "deep_green",
    "green": "deep_green",
}

# ── Colour RGB centroids (for hex→name mapping from extracted dominant colour) ─
COLOUR_CENTROIDS: dict[str, tuple[int, int, int]] = {
    "black":        (30, 30, 30),
    "silver":       (192, 192, 192),
    "gold":         (200, 160, 40),
    "rose_gold":    (183, 110, 121),
    "tortoiseshell":(139, 90, 43),
    "brown":        (101, 67, 33),
    "amber":        (200, 150, 10),
    "olive":        (107, 142, 35),
    "tan":          (210, 180, 140),
    "honey":        (205, 170, 40),
    "cognac":       (156, 97, 20),
    "caramel":      (196, 127, 65),
    "navy":         (0, 0, 128),
    "purple":       (128, 0, 128),
    "burgundy":     (128, 0, 32),
    "gunmetal":     (84, 98, 111),
    "cool_grey":    (140, 146, 172),
    "warm_grey":    (150, 140, 130),
    "blue":         (65, 105, 225),
    "deep_green":   (0, 100, 0),
    "blush":        (222, 148, 141),
    "clear":        (230, 230, 245),
}

# ── CLIP style labels ─────────────────────────────────────────────────────────
CLIP_STYLE_LABELS = [
    "rectangular eyeglasses frame",
    "round eyeglasses frame",
    "oval eyeglasses frame",
    "square eyeglasses frame",
    "cat-eye eyeglasses frame",
    "aviator eyeglasses frame",
    "wayfarer eyeglasses frame",
    "browline eyeglasses frame",
    "geometric eyeglasses frame",
    "rimless eyeglasses frame",
    "oversized eyeglasses frame",
]

CLIP_STYLE_TO_SCHEMA = {label.split(" eyeglasses")[0]: label.split(" eyeglasses")[0] for label in CLIP_STYLE_LABELS}

# ── Source metadata ───────────────────────────────────────────────────────────
SOURCES = {
    "lenskart": {
        "retailer": "Lenskart",
        "listing_api": "https://www.lenskart.com/rest/v2/catalog/category/eyeglasses",
        "product_base_url": "https://www.lenskart.com",
        "page_size": 48,
    },
    "johnjacobs": {
        "retailer": "John Jacobs",
        "listing_api": "https://www.johnjacobs.com/rest/v2/catalog/category/eyeglasses",
        "product_base_url": "https://www.johnjacobs.com",
        "page_size": 48,
    },
    "titan": {
        "retailer": "Titan Eye+",
        # Discovered via Playwright XHR intercept — /api/products returns 404
        "listing_api": "https://www.titaneyeplus.com/api/products/get-list/eyeglasses",
        "listing_url": "https://www.titaneyeplus.com/eyeglasses",
        "product_base_url": "https://www.titaneyeplus.com",
        "page_size": 24,
    },
    "rayban": {
        "retailer": "Ray-Ban",
        "listing_api": "https://www.ray-ban.com/api/product-search",
        "product_base_url": "https://www.ray-ban.com/en_IN",
        "page_size": 24,
    },
}
