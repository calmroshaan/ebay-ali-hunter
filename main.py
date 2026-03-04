# main.py
# -----------------------------------------------
# Entry point. Run this file to start the tool.
# Loads keywords → runs pipeline → saves results.
# -----------------------------------------------

import asyncio
from scrapers.browser import BrowserManager
from pipeline.runner import run_pipeline
from output.deduplicator import deduplicate
from output.exporter import export_results
from config import KEYWORDS_FILE
from utils.logger import get_logger

logger = get_logger(__name__)


def load_keywords(filepath: str) -> list[str]:
    """
    Reads keywords from a text file.
    One keyword per line. Skips empty lines and comments (#).

    Example keywords.txt:
        wireless earbuds
        phone case iphone 15
        # this line is ignored
        led strip lights
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        keywords = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                keywords.append(line)

        logger.info(f"Loaded {len(keywords)} keywords from {filepath}")
        return keywords

    except FileNotFoundError:
        logger.error(f"Keywords file not found: {filepath}")
        return []


async def main():
    logger.info("=== eBay Ali Hunter started ===")

    # --- Load keywords ---
    keywords = load_keywords(KEYWORDS_FILE)
    if not keywords:
        logger.error("No keywords found. Add keywords to data/keywords.txt and try again.")
        return

    # --- Start browser ---
    browser = BrowserManager()
    await browser.start()

    try:
        # --- Run pipeline ---
        results, ebay_top = await run_pipeline(browser, keywords)
        results = deduplicate(results)
        output_path = export_results(results, ebay_top)

        if output_path:
            print(f"\n✅ Done! Results saved to: {output_path}")
            print(f"   Total profitable products found: {len(results)}")
        else:
            print("\n⚠️  Pipeline finished but no profitable products found.")
            print("    Try adding more keywords to data/keywords.txt")

    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)

    finally:
        await browser.close()

    logger.info("=== eBay Ali Hunter finished ===")


asyncio.run(main())
