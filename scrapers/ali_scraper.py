# scrapers/ali_scraper.py
# -----------------------------------------------
# Finds AliExpress prices via Google search.
# Searches "site:aliexpress.com keyword" on Google.
# No VPN needed. Works from any region.
# -----------------------------------------------

import re
from urllib.parse import urlencode
from playwright.async_api import BrowserContext, Page
from playwright_stealth import stealth_async
from config import ALI_BASE_URL, MAX_ALI_RESULTS, PAGE_LOAD_DELAY
from utils.logger import get_logger
from utils.delays import human_delay

logger = get_logger(__name__)


def _clean_keyword(keyword: str) -> str:
    """Remove noise words for cleaner search."""
    noise = ["for", "with", "new", "lot", "set", "pack", "free", "fast", "usa", "and"]
    words = keyword.lower().split()
    cleaned = " ".join(w for w in words if w not in noise)
    return cleaned[:60]


async def scrape_aliexpress(context: BrowserContext, keyword: str) -> list[dict]:
    """
    Searches Google for AliExpress products.
    Returns list of candidate products with prices.
    """
    results = []
    page: Page = await context.new_page()
    await stealth_async(page)
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    try:
        query = _clean_keyword(keyword)
        params = {
            "q": f"site:aliexpress.com {query} welcome deal price",
            "num": 20,
            "hl": "en",
        }
        url = f"{ALI_BASE_URL}?{urlencode(params)}"
        logger.info(f"Google-AliExpress | keyword='{query}'")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(*PAGE_LOAD_DELAY, label="google_page_load")

        # Check for Google CAPTCHA
        if await _is_blocked(page):
            logger.warning("Google CAPTCHA — waiting and retrying")
            await human_delay(30.0, 5.0, label="google_block_wait")
            await page.reload(wait_until="domcontentloaded", timeout=30000)
            await human_delay(*PAGE_LOAD_DELAY, label="google_retry")
            if await _is_blocked(page):
                logger.error("Google still blocked — skipping")
                return results

        # Save debug file to inspect if needed
        content = await page.content()
        with open("debug_ali.html", "w", encoding="utf-8") as f:
            f.write(content)

        # Extract search result blocks
        items = await page.query_selector_all("div.g")
        if not items:
            items = await page.query_selector_all("div[jscontroller]")

        logger.info(f"Google-AliExpress | found {len(items)} raw results")

        for item in items[:MAX_ALI_RESULTS]:
            record = await _extract_item(item)
            if record:
                results.append(record)

        logger.info(f"Google-AliExpress | extracted {len(results)} valid products")

    except Exception as e:
        logger.error(f"Google→Ali failed for '{keyword}': {e}", exc_info=True)
    finally:
        await page.close()

    return results


async def _is_blocked(page: Page) -> bool:
    try:
        title = await page.title()
        blocked_signals = ["captcha", "unusual traffic", "robot", "verify"]
        return any(s in title.lower() for s in blocked_signals)
    except Exception:
        return False


async def _extract_item(item) -> dict | None:
    """
    Extract title and price from a Google result
    pointing to AliExpress.
    """
    try:
        # Only keep results linking to AliExpress
        link_el = await item.query_selector("a")
        if not link_el:
            return None
        href = await link_el.get_attribute("href") or ""

        # Google wraps real URLs — extract actual AliExpress link
        if "aliexpress.com" not in href:
            return None

        # Clean up Google redirect wrapper if present
        if href.startswith("/url?"):
            from urllib.parse import urlparse, parse_qs
            parsed = parse_qs(urlparse(href).query)
            href = parsed.get("q", [href])[0]
        # Title from h3
        title_el = await item.query_selector("h3")
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        # Price — search full item text for $ amount
        full_text = (await item.inner_text()).strip()
        price = None

        # Look for patterns like $12.99 or US $12.99
        matches = re.findall(r"\$\s*[\d,]+\.?\d*", full_text)
        if matches:
            # Take the first/lowest price found
            for m in matches:
                val = float(re.sub(r"[^\d.]", "", m))
                if val > 0:
                    price = val
                    break

        if price is None:
            return None
        if price > 150:
            return None
        if len(title) < 15:
            return None
        
        clean_url = _fix_ali_url(href)
        if not clean_url:
            return None

        return {
            "ali_title": title,
            "ali_price": price,
            "ali_shipping": 0.0,
            "ali_url"     : clean_url,
        }

    except Exception as e:
        logger.debug(f"Google result extraction failed: {e}")
        return None
    
def _fix_ali_url(href: str) -> str | None:
    """
    Cleans up AliExpress URLs from Google results.
    - Removes Google redirect wrappers
    - Keeps only valid item pages
    - Adds language=en to avoid blank pages
    """
    try:
        # Unwrap Google redirect if present
        if "/url?" in href:
            from urllib.parse import urlparse, parse_qs
            parsed = parse_qs(urlparse(href).query)
            href   = parsed.get("q", [href])[0]

        # Must be AliExpress
        if "aliexpress.com" not in href:
            return None

        # Must be a product page not search or category
        if "/item/" not in href:
            return None

        # Strip query params and add our own
        base = href.split("?")[0]
        return base + "?language=en&ship_to=US"

    except Exception:
        return None