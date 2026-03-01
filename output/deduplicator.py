# output/deduplicator.py
# -----------------------------------------------
# Removes duplicate products from final results.
# Same eBay listing can appear under multiple
# keywords — we keep only the first occurrence.
# Deduplication is based on eBay URL.
# If no URL, falls back to title comparison.
# -----------------------------------------------

from utils.logger import get_logger

logger = get_logger(__name__)


def deduplicate(results: list[dict]) -> list[dict]:
    """
    Takes a list of matched product dicts.
    Returns a new list with duplicates removed.

    Example:
        Input:  10 products, 3 are the same eBay listing
        Output: 7 products — duplicates dropped
    """
    seen_urls   = set()
    seen_titles = set()
    unique      = []

    for product in results:
        url   = product.get("ebay_url", "").strip()
        title = product.get("title", "").strip().lower()

        # Prefer URL-based deduplication (most reliable)
        if url:
            if url in seen_urls:
                logger.debug(f"Duplicate (URL) skipped: {title[:50]}")
                continue
            seen_urls.add(url)

        # Fallback: title-based deduplication
        else:
            if title in seen_titles:
                logger.debug(f"Duplicate (title) skipped: {title[:50]}")
                continue
            seen_titles.add(title)

        unique.append(product)

    removed = len(results) - len(unique)
    logger.info(f"Deduplication: {len(results)} -> {len(unique)} results ({removed} duplicates removed)")

    return unique
