# FrameAI — Frame Data Pipeline
## Scrape → Process → Annotate → Load

**Status:** Pre-Sprint 2 — must be completed before Sprint 2 Task 2.4

---

## Overview

The catalogue is the foundation of everything. Without clean, annotated frame data:
- The recommendation engine has nothing to query
- The generation pipeline has no product images to composite
- The buy links have no destination

This document is the complete plan: what to scrape, how to scrape it, how to process it, how to annotate it, and how to load it into the DB.

---

## Phase 1 — Understand Source Structure

### Source 1: Lenskart (lenskart.com)

**URL pattern for eyeglasses:**
```
https://www.lenskart.com/eyeglasses/men.html?pageNumber=0
https://www.lenskart.com/eyeglasses/women.html?pageNumber=0
```

**How Lenskart serves data:**
Lenskart exposes a semi-public API endpoint that returns product listings as JSON before the page renders. This is faster and more reliable than scraping rendered HTML.

```
GET https://www.lenskart.com/rest/v2/catalog/category/eyeglasses?
    page=0&pageSize=48&gender=men&format=json
```

**What the API returns per product:**
- `product_id`, `name`, `url_key`
- `price`, `special_price`
- `frame_shape` (rectangular, round, etc.)
- `frame_colour`
- `frame_material`
- `image_urls[]` (multiple angles — front, side, 3/4)
- `frame_size` string (e.g., "Medium-51")

**What must be scraped from the product page HTML:**
- Full spec table (lens width, bridge width, temple length)
- Rim type (rimless, semi-rimmed, full-rim)
- Gender tag
- "Suitable for face shape" if listed

**Estimated catalogue size:** ~8,000–12,000 eyeglass SKUs on Lenskart

---

### Source 2: Titan Eye+ (titaneyeplus.com)

**URL pattern:**
```
https://www.titaneyeplus.com/eyeglasses?page=1
https://www.titaneyeplus.com/eyeglasses/gender/men?page=1
https://www.titaneyeplus.com/eyeglasses/gender/women?page=1
```

**How Titan Eye+ serves data:**
Titan Eye+ is a JavaScript-rendered site (React/Next.js). Product data is loaded via internal API calls that can be intercepted.

Network tab shows calls to:
```
GET https://www.titaneyeplus.com/api/products?category=eyeglasses&page=1&limit=24
```

Returns product cards with: name, price, image URL, frame shape, colour, material, SKU.

Full product specs are on individual product pages:
```
https://www.titaneyeplus.com/product/{sku}
```

Spec table contains: lens width, bridge, temple length, rim type, material.

**Estimated catalogue size:** ~3,000–5,000 eyeglass SKUs

---

### Source 3: John Jacobs (johnjacobs.com — Lenskart owned)

**URL pattern:**
```
https://www.johnjacobs.com/eyeglasses/men.html
https://www.johnjacobs.com/eyeglasses/women.html
```

Same API structure as Lenskart (shared platform). Approx 500–800 SKUs. Premium positioning.

---

### Source 4: Rayban India (ray-ban.com/en_IN)

**URL pattern:**
```
https://www.ray-ban.com/en_IN/c/eyeglasses
```

Ray-Ban uses Salesforce Commerce Cloud. Product data available via:
```
GET https://www.ray-ban.com/api/product-search?category=eyeglasses&start=0&sz=24
```

**Note:** Ray-Ban has strict ToS on scraping. Strategy: scrape only the public product listing (name, price, style, image URL, buy URL). ~200–300 eyeglass SKUs on Ray-Ban India.

---

## Phase 2 — Scraper Architecture

### Tech stack for scraping
```
Playwright     — browser automation for JS-rendered pages
httpx          — async HTTP client for API endpoints
BeautifulSoup  — HTML parsing
asyncio        — concurrent scraping
```

### Project structure
```
frameAI/
└── scraper/
    ├── README.md
    ├── requirements.txt
    ├── run.py                  ← entry point, runs all scrapers
    ├── config.py               ← source URLs, rate limits, output paths
    ├── sources/
    │   ├── lenskart.py
    │   ├── titan.py
    │   ├── johnjacobs.py
    │   └── rayban.py
    ├── pipeline/
    │   ├── image_processor.py  ← download + normalise product images
    │   ├── auto_annotator.py   ← CLIP style tagger + colour extractor
    │   └── deduplicator.py     ← cross-source dedup by image hash
    ├── output/
    │   ├── raw/                ← raw JSON per source
    │   ├── processed/          ← cleaned, normalised records
    │   └── images/             ← downloaded product images
    └── annotation/
        ├── review_tool.py      ← CLI tool for manual annotation pass
        └── annotations.csv     ← human-written face_shape_tags + vibe_tags
```

---

## Phase 3 — Scraper Logic (per source)

### Step 3.1 — List scraper (get all product URLs + basic data)

For each source, scrape the listing pages to get:
- Product URL / SKU
- Name
- Price
- Front-facing image URL
- Basic frame shape / colour if available in listing

```python
# Pseudocode — lenskart.py
async def scrape_listing(page_num: int) -> list[dict]:
    url = f"https://www.lenskart.com/rest/v2/catalog/category/eyeglasses?page={page_num}&pageSize=48"
    response = await httpx_client.get(url, headers=HEADERS)
    products = response.json()["products"]
    return [extract_basic_fields(p) for p in products]

async def scrape_all_listings() -> list[dict]:
    # Paginate until empty page returned
    all_products = []
    page = 0
    while True:
        batch = await scrape_listing(page)
        if not batch:
            break
        all_products.extend(batch)
        page += 1
        await asyncio.sleep(RATE_LIMIT_SECONDS)  # 1–2s between requests
    return all_products
```

**Output:** `output/raw/lenskart_listings.json` — list of ~8,000 basic product records

---

### Step 3.2 — Detail scraper (get full specs per product)

For each product URL from Step 3.1, fetch the product page and extract the spec table.

```python
# Pseudocode — detail scraping via Playwright
async def scrape_product_detail(url: str) -> dict:
    page = await browser.new_page()
    await page.goto(url, wait_until="networkidle")
    
    # Extract spec table
    specs = await page.evaluate("""
        () => {
            const rows = document.querySelectorAll('.product-specs tr');
            return Object.fromEntries(
                [...rows].map(r => [
                    r.querySelector('th')?.textContent.trim(),
                    r.querySelector('td')?.textContent.trim()
                ])
            );
        }
    """)
    return specs
```

**Rate limiting:** Max 2 concurrent requests, 1.5s delay between requests per domain.
**Checkpoint saves:** Save progress every 100 products to `output/raw/lenskart_details_{checkpoint}.json`

---

### Step 3.3 — Image downloader

For each product, download the front-facing product image.

```python
async def download_product_image(product_id: str, image_url: str) -> str:
    # Download raw image
    response = await httpx_client.get(image_url)
    raw_path = f"output/images/raw/{product_id}.jpg"
    
    # Save raw
    with open(raw_path, "wb") as f:
        f.write(response.content)
    
    return raw_path
```

**Target image:** Front-facing, white/light background, glasses only (no model face).
**Selection logic:** If multiple images, prefer the one with "front" in filename or URL path. Avoid images with model faces in them — these cannot be used as the reference image in generation.

---

## Phase 4 — Processing Pipeline

After scraping, every record goes through a processing pipeline before entering the DB.

### Step 4.1 — Data normalisation

Map source-specific field names to our schema.

```python
STYLE_MAP = {
    # Lenskart naming → our schema
    "rectangular": "rectangular",
    "rectangle": "rectangular",
    "round": "round",
    "oval": "oval",
    "cat eye": "cat-eye",
    "cat-eye": "cat-eye",
    "wayfarer": "wayfarer",
    "aviator": "aviator",
    "clubmaster": "browline",
    "browline": "browline",
    "geometric": "geometric",
    "rimless": "rimless",
    "square": "square",
    # Titan naming
    "Rectangle": "rectangular",
    "Round": "round",
    # Add more as discovered
}

def normalise_style(raw_style: str) -> str | None:
    return STYLE_MAP.get(raw_style.strip().lower())

def normalise_price(raw_price: str) -> int | None:
    # Handle "₹1,899", "Rs. 1899", "1899.00"
    digits = re.sub(r"[^\d]", "", raw_price)
    return int(digits) if digits else None

def parse_dimensions(spec_string: str) -> dict:
    # Parse "51-18-140" or "Lens: 51mm | Bridge: 18mm | Temple: 140mm"
    ...
```

### Step 4.2 — Image normalisation

Every product image is normalised to a consistent format for generation.

```python
def normalise_image(input_path: str, output_path: str) -> bool:
    img = Image.open(input_path)
    
    # 1. Convert to RGBA
    img = img.convert("RGBA")
    
    # 2. Check background is white/light — reject if model face detected
    if has_human_face(img):
        log_skip(input_path, reason="model_face_detected")
        return False
    
    # 3. Crop to tight bounding box around glasses
    img = autocrop_to_glasses(img)
    
    # 4. Pad to square with white background
    img = pad_to_square(img, fill=(255, 255, 255, 255))
    
    # 5. Resize to 512x512
    img = img.resize((512, 512), Image.LANCZOS)
    
    # 6. Save as WebP
    img.save(output_path, "WebP", quality=90)
    return True
```

**Face detection for rejection:** Use InsightFace or OpenCV Haar cascade to detect if a human face is in the product image. Any image with a face is rejected — it cannot be used as the frame reference in generation.

### Step 4.3 — Auto-annotation (CLIP-based style tagger)

Use CLIP to automatically classify frame style and extract dominant colour.

```python
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

STYLE_LABELS = [
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
]

def classify_style_clip(image_path: str) -> tuple[str, float]:
    image = Image.open(image_path)
    inputs = processor(text=STYLE_LABELS, images=image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)
    best_idx = probs.argmax().item()
    label = STYLE_LABELS[best_idx].split(" eyeglasses")[0]
    confidence = probs[0][best_idx].item()
    return label, confidence
```

**Colour extraction:**
```python
from sklearn.cluster import KMeans
import numpy as np

def extract_dominant_colour(image_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).reshape(-1, 3)
    
    # Remove white/near-white pixels (background)
    mask = ~np.all(arr > 230, axis=1)
    arr = arr[mask]
    
    if len(arr) < 100:
        return "#000000"  # fallback
    
    kmeans = KMeans(n_clusters=3, n_init=10)
    kmeans.fit(arr)
    
    # Most common non-white cluster
    dominant = kmeans.cluster_centers_[0].astype(int)
    return "#{:02x}{:02x}{:02x}".format(*dominant)
```

---

## Phase 5 — Manual Annotation

Auto-annotation covers style and colour. Two fields require human judgment:
- `face_shape_tags` — which face shapes this frame suits
- `vibe_tags` — aesthetic tags (minimal, editorial, retro, bold, professional, sporty)

### Annotation process

1. Export all processed records to `annotation/to_annotate.csv`
2. Reviewer opens images in the annotation CLI tool
3. For each frame: assign face_shape_tags + vibe_tags
4. Save to `annotation/annotations.csv`
5. Merge back into processed records

### Annotation CLI tool

```bash
python annotation/review_tool.py --batch-size 50

# Shows image, displays current auto-tags, prompts for corrections
# Frame: JJ-1234 | Style: rectangular (auto, conf=0.89) | Colour: tortoiseshell
# Face shapes [oval, round, square, heart, diamond, oblong]: oval, square, heart
# Vibe tags [minimal, editorial, retro, bold, professional, sporty, classic]: professional, minimal
# Save? [y/n]: y
```

### Annotation target

For v1 prototype: annotate **top 500 frames** manually.
Selection criteria:
- Diverse styles (80+ per major style category)
- All price tiers represented (₹500–₹20,000)
- All major retailers represented
- Clean product images (no model faces, white background)

Full catalogue annotation (all scraped records) is a post-launch task.

---

## Phase 6 — Deduplication

The same physical frame may appear on both Lenskart and Titan Eye+.
Deduplication strategy:

```python
def deduplicate_catalogue(records: list[dict]) -> list[dict]:
    # 1. Hash-based: compute perceptual hash of each product image
    #    Frames with pHash distance < 10 are likely duplicates
    # 2. For duplicates: keep the record with most complete data
    #    Prefer: more spec fields > lower price > Lenskart > Titan
    # 3. Merge buy_url from both sources onto the surviving record
    #    (so user can buy from either retailer)
    ...
```

---

## Phase 7 — Load to Supabase

After processing, deduplication, and annotation:

```python
async def load_to_supabase(records: list[dict]):
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Upload images to R2 first
    for record in records:
        r2_key = f"frames/{record['frame_id']}.webp"
        await upload_to_r2(record["local_image_path"], r2_key)
        record["product_image_url"] = f"{R2_PUBLIC_URL}/{r2_key}"
    
    # Upsert to frames table (idempotent — safe to re-run)
    await client.table("frames").upsert(records).execute()
    
    print(f"Loaded {len(records)} frames to Supabase")
```

---

## Phase 8 — Refresh Strategy

Prices change. New frames get added. Old frames get discontinued.

**Refresh schedule:**
- **Weekly:** Re-scrape prices only (fast, lightweight)
- **Monthly:** Full re-scrape + re-process images for new SKUs
- **On discontinuation:** Mark frames as `is_active = false` rather than deleting
  (keeps buy links from erroring on old sessions)

**Price refresh (fast path):**
```python
async def refresh_prices():
    # Scrape listing pages only (no detail pages)
    # Update price_inr + scraped_at for existing records
    # Log any SKUs that 404 (discontinued) → mark is_active = false
```

---

## Realistic Timeline

| Phase | Task | Time estimate |
|---|---|---|
| 1 | Manually inspect source structure, verify API endpoints | 2–3 hours |
| 2 | Build Lenskart list + detail scrapers | 1 day |
| 3 | Build Titan Eye+ scraper | 1 day |
| 4 | Build John Jacobs + Ray-Ban scrapers | 0.5 day |
| 5 | Run all scrapers, collect raw data | 4–6 hours (IO-bound) |
| 6 | Image normalisation pipeline | 0.5 day |
| 7 | CLIP auto-annotation | 2–3 hours |
| 8 | Manual annotation of top 500 frames | 1–2 days (2 reviewers) |
| 9 | Deduplication + load to Supabase | 0.5 day |
| **Total** | | **~6–8 working days** |

---

## Known Risks

| Risk | Mitigation |
|---|---|
| Lenskart blocks scraper IP | Use rotating headers, 1.5–2s delay, max 2 concurrent. If blocked, fall back to manual data entry for seed catalogue. |
| Product images include model faces | Filter via face detection. Reject affected records. ~10–20% estimated rejection rate. |
| Titan Eye+ JS renders too slowly | Playwright with `wait_until="networkidle"` + 3s timeout fallback |
| Source TOS prohibits scraping | Scraping publicly available product data for personal/research use is generally permitted. Do not resell the raw data. Add `Referer` and `User-Agent` headers consistent with a real browser. |
| Frame dimensions missing from listing | Parse from product page spec table. If still missing, estimate from image using aspect ratio heuristic. |
| Style taxonomy mismatch between sources | STYLE_MAP normalisation in Step 4.1. Unknown styles logged to `output/unknown_styles.txt` for manual review. |

---

## Output Artefacts

After the full pipeline completes:

```
output/
├── raw/
│   ├── lenskart_listings.json       # ~8,000 records
│   ├── lenskart_details.json        # ~8,000 records with specs
│   ├── titan_listings.json          # ~3,500 records
│   ├── titan_details.json
│   ├── johnjacobs_listings.json     # ~700 records
│   └── rayban_listings.json         # ~250 records
├── processed/
│   └── catalogue.json               # ~10,000 deduplicated, normalised records
├── images/
│   ├── raw/                         # original downloaded images
│   └── normalised/                  # 512x512 WebP, white background, no faces
└── annotation/
    ├── to_annotate.csv              # records pending manual annotation
    └── annotations.csv             # completed manual annotations

DB (Supabase):
└── frames table: ~500 fully annotated records (v1 seed)
    + ~9,500 partially annotated records (auto-tagged only)

R2:
└── frames/ bucket: ~10,000 normalised product images
```

**v1 prototype uses only the 500 fully annotated records.**
The rest become available as annotation coverage improves.