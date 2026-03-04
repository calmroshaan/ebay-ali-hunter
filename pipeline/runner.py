# pipeline/runner.py
# -----------------------------------------------
# Core pipeline. Loops through keywords and:
#   1. Scrapes eBay for that keyword
#   2. Scrapes AliExpress for that keyword
#   3. Matches each eBay product to best Ali match
#   4. Calculates profit on each match
#   5. Collects all profitable products
# Returns the full results list to main.py or UI
# -----------------------------------------------

from config import BETWEEN_KEYWORDS_DELAY, BETWEEN_SITES_DELAY
from scrapers.ebay_scraper import scrape_ebay
from scrapers.ali_scraper import scrape_aliexpress
from matching.matcher import find_best_match
from logic.profit_calculator import calculate_profit
from utils.delays import human_delay
from utils.logger import get_logger

logger = get_logger(__name__)


async def run_pipeline(browser_manager, keywords: list[str], log_callback=None, market: str = "US") -> list[dict]:
    """
    Main pipeline loop.
    Takes the browser manager, list of keywords and market (US or UK).
    log_callback — optional function to send live logs to UI.
    Returns list of all profitable matched products.
    """

    def log(msg: str):
        """Log to both file logger and UI if callback provided."""
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    all_results = []
    all_ebay_top = []

    for i, keyword in enumerate(keywords):
        log(f"--- Keyword {i+1}/{len(keywords)}: '{keyword}' ---")

        try:
            # --- Step 1: Scrape eBay ---
            log(f"🔎 Scraping eBay [{market}] for '{keyword}'...")
            ebay_context  = await browser_manager.new_context("ebay")
            ebay_products = await scrape_ebay(ebay_context, keyword, market=market)
            await browser_manager.save_state(ebay_context, "ebay")
            await ebay_context.close()

            log(f"✅ eBay [{market}]: {len(ebay_products)} products found") 

            if not ebay_products:
                log(f"⚠️ No eBay results for '{keyword}' — skipping")
                continue

            # --- Delay between sites ---
            log("⏳ Waiting before AliExpress search...")
            await human_delay(*BETWEEN_SITES_DELAY, label="between_sites")

            # --- Step 2: Scrape AliExpress ---
            log(f"🔎 Searching AliExpress for '{keyword}'...")
            ali_context  = await browser_manager.new_context("aliexpress")
            ali_products = await scrape_aliexpress(ali_context, keyword)
            await browser_manager.save_state(ali_context, "aliexpress")
            await ali_context.close()

            log(f"✅ AliExpress: {len(ali_products)} products found")

            if not ali_products:
                log(f"⚠️ No AliExpress results for '{keyword}' — skipping")
                continue
# --- Collect eBay Top 5 Sellers regardless of matching ---
            ebay_top5 = sorted(
                ebay_products,
                key=lambda x: x.get("sold_count") or 0,
                reverse=True
            )[:5]

            for ebay_item in ebay_top5:
                ebay_record = {
                    "keyword"       : keyword,
                    "market"        : ebay_item.get("market", "US"),
                    "currency"      : ebay_item.get("currency", "USD"),
                    "symbol"        : ebay_item.get("symbol", "$"),
                    "title"         : ebay_item["title"],
                    "ebay_price"    : ebay_item["ebay_price"],
                    "ebay_shipping" : ebay_item["ebay_shipping"],
                    "ebay_url"      : ebay_item.get("ebay_url", ""),
                    "sold_count"    : ebay_item.get("sold_count"),
                    "seller_rating" : ebay_item.get("seller_rating"),
                    "welcome_deal"  : ebay_item.get("welcome_deal", False),
                }
                all_ebay_top.append(ebay_record)

            # --- Step 3 & 4: Match + Profit ---
            keyword_results = []

            for ebay_item in ebay_products:
                match = find_best_match(ebay_item["title"], ali_products)
                if not match:
                    continue

                profit_data = calculate_profit(
                    ebay_price    = ebay_item["ebay_price"],
                    ebay_shipping = ebay_item["ebay_shipping"],
                    ali_price     = match["ali_price"],
                    ali_shipping  = match["ali_shipping"],
                )
                if not profit_data:
                    continue

                record = {
                    "keyword"       : keyword,
                    "market"        : ebay_item.get("market", "US"),
                    "currency"      : ebay_item.get("currency", "USD"),
                    "symbol"        : ebay_item.get("symbol", "$"),
                    "title"         : ebay_item["title"],
                    "ebay_price"    : ebay_item["ebay_price"],
                    "ebay_shipping" : ebay_item["ebay_shipping"],
                    "ebay_url"      : ebay_item.get("ebay_url", ""),
                    "sold_count"    : ebay_item.get("sold_count"),
                    "seller_rating" : ebay_item.get("seller_rating"),
                    "welcome_deal"  : ebay_item.get("welcome_deal", False),
                    "ali_title"     : match["ali_title"],
                    "ali_price"     : match["ali_price"],
                    "ali_shipping"  : match["ali_shipping"],
                    "ali_url"       : match.get("ali_url", ""),
                    "match_score"   : match["match_score"],
                    **profit_data,
                }

                keyword_results.append(record)

            # Sort by sold count first, then margin as tiebreaker
            keyword_results.sort(
                key=lambda x: (
                    x.get("sold_count") or 0,
                    x.get("margin_pct") or 0
                ),
                reverse=True
            )

            # Keep only top 5 per keyword
            top5 = keyword_results[:5]

            log(f"✅ '{keyword}': {len(keyword_results)} matches found — keeping top {len(top5)}")
            all_results.extend(top5)

        except Exception as e:
            log(f"❌ Pipeline error for '{keyword}': {e}")
            logger.error(f"Pipeline failed for '{keyword}'", exc_info=True)

        # --- Delay before next keyword ---
        if i < len(keywords) - 1:
            log("⏳ Waiting before next keyword...")
            await human_delay(*BETWEEN_KEYWORDS_DELAY, label="between_keywords")

    log(f"🏁 Pipeline complete. Total profitable products: {len(all_results)}")
    log(f"🏁 Total eBay top sellers collected: {len(all_ebay_top)}")
    return all_results, all_ebay_top