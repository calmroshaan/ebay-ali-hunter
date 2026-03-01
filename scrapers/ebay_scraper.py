# scrapers/ebay_scraper.py
# -----------------------------------------------
# Searches eBay for a keyword and extracts:
# title, price, shipping, sold count, seller rating
# Returns a list of product dictionaries.
# -----------------------------------------------

import re
from urllib.parse import urlencode
from playwright.async_api import BrowserContext, Page
from playwright_stealth import stealth_async
from config import EBAY_BASE_URL, MAX_EBAY_PAGES, PAGE_LOAD_DELAY, BETWEEN_ITEMS_DELAY
from utils.logger import get_logger
from utils.delays import human_delay

logger = get_logger(__name__)


def _parse_price(raw: str) -> float | None:
    """
    Extract a number from a price string.
    '$12.99'  →  12.99
    '$10.00 to $15.00'  →  10.00  (takes the first/lower price)
    """
    try:
        match = re.search(r"[\d,]+\.?\d*", raw.replace(",", ""))
        return float(match.group()) if match else None
    except Exception:
        return None


def _parse_sold(raw: str) -> int | None:
    """
    Extract sold count from strings like '1,234 sold'.
    '1,234 sold'  →  1234
    """
    try:
        match = re.search(r"[\d,]+", raw.replace(",", ""))
        return int(match.group()) if match else None
    except Exception:
        return None


async def scrape_ebay(context: BrowserContext, keyword: str) -> list[dict]:
    """
    Main function. Takes a browser context and keyword.
    Returns list of product dicts found on eBay.
    """
    results = []
    page: Page = await context.new_page()
    await stealth_async(page)
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        for page_num in range(1, MAX_EBAY_PAGES + 1):
            # Build the search URL
            params = {
                "_nkw": keyword,
                "_pgn": page_num,
            }
            url = f"{EBAY_BASE_URL}?{urlencode(params)}"
            logger.info(f"eBay | keyword='{keyword}' | page={page_num}")

            # Go to the page
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await human_delay(*PAGE_LOAD_DELAY, label="ebay_page_load")

            # Check if eBay blocked us
            if await _is_blocked(page):
                logger.warning(f"eBay block detected on page {page_num} for '{keyword}'")
                break

            # Find all product listing elements on the page
            items = await page.query_selector_all("ul.srp-results li")
            if not items:
                logger.info(f"No items found on page {page_num}, stopping")
                break

            # Extract data from each listing
            for item in items:
                await human_delay(*BETWEEN_ITEMS_DELAY, label="ebay_item")
                record = await _extract_item(item)
                if record:
                    results.append(record)

            logger.info(f"eBay | page {page_num} done | {len(results)} results so far")

    except Exception as e:
        logger.error(f"eBay scrape failed for '{keyword}': {e}", exc_info=True)
    finally:
        await page.close()

    return results


async def _is_blocked(page: Page) -> bool:
    """Check if eBay is showing a block or CAPTCHA page."""
    try:
        title = await page.title()
        # Only check the title — content check causes false positives
        blocked_signals = ["captcha", "robot", "unusual traffic", "access denied"]
        return any(s in title.lower() for s in blocked_signals)
    except Exception:
        return False


async def _extract_item(item) -> dict | None:
    """
    Extract all fields from one eBay listing element.
    Returns None if the listing is invalid or missing key data.
    """
    try:
        # Title
        title_el = await item.query_selector("div.s-card__title span.su-styled-text")
        title = (await title_el.inner_text()).strip() if title_el else None
        if not title or "opens in a new" in title.lower():
            return None

        url = None
        link_el = await item.query_selector("a.s-card__link")
        if link_el:
            url = await link_el.get_attribute("href")

        # Price
        price_el = await item.query_selector("span.s-card__price")
        price_raw = (await price_el.inner_text()).strip() if price_el else ""
        price = _parse_price(price_raw)

        # Shipping — find all secondary text spans, look for delivery info
        shipping = 0.0
        spans = await item.query_selector_all("span.su-styled-text.secondary.large")
        for span in spans:
            text = (await span.inner_text()).strip().lower()
            if "free delivery" in text or "free shipping" in text:
                shipping = 0.0
                break
            elif "delivery" in text or "shipping" in text:
                parsed = _parse_price(text)
                if parsed:
                    shipping = parsed
                break

        # Sold count — look for any span containing "sold"
        sold_count = None
        all_spans = await item.query_selector_all("span")
        for span in all_spans:
            text = (await span.inner_text()).strip().lower()
            if "sold" in text:
                sold_count = _parse_sold(text)
                break

        # Seller rating — look for span containing "% positive"
        seller_rating = None
        for span in all_spans:
            text = (await span.inner_text()).strip()
            if "% positive" in text:
                try:
                    seller_rating = float(re.search(r"[\d.]+", text).group())
                except Exception:
                    pass
                break

        if not title or price is None:
            return None

        return {
            "title": title,
            "ebay_price": price,
            "ebay_shipping": shipping,
            "sold_count": sold_count,
            "seller_rating": seller_rating,
            "ebay_url": url,
        }

    except Exception as e:
        logger.debug(f"Item extraction failed: {e}")
        return None