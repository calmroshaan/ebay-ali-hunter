# matching/matcher.py
# -----------------------------------------------
# Compares eBay product titles against AliExpress
# candidate pool and returns the best match.
# Uses fuzzy matching so titles don't need to be
# identical — just similar enough.
# -----------------------------------------------

from rapidfuzz import fuzz
from config import SIMILARITY_THRESHOLD
from utils.logger import get_logger

logger = get_logger(__name__)


def find_best_match(ebay_title: str, ali_results: list[dict]) -> dict | None:
    """
    Takes one eBay title and a list of AliExpress candidates.
    Returns the best matching AliExpress product or None.

    Example:
        ebay_title = "Sony WF-1000XM5 Wireless Earbuds Bluetooth"
        ali_results = [{"ali_title": "Sony WF1000XM5 BT Earbuds", ...}]
        → returns the ali result with highest similarity score
    """
    if not ali_results:
        logger.debug("No AliExpress candidates to match against")
        return None

    best_match = None
    best_score = 0

    for item in ali_results:
        ali_title = item.get("ali_title", "")
        if not ali_title:
            continue

        # token_sort_ratio handles word order differences well
        # "Wireless Sony Earbuds" vs "Sony Wireless Earbuds" = 100
        score = fuzz.token_sort_ratio(
            ebay_title.lower(),
            ali_title.lower()
        )

        logger.debug(
            f"Score {score} | "
            f"eBay: '{ebay_title[:40]}' | "
            f"Ali: '{ali_title[:40]}'"
        )

        if score > best_score:
            best_score = score
            best_match = item

    # Reject if best score is below threshold
    if best_score < SIMILARITY_THRESHOLD:
        logger.debug(
            f"No match above {SIMILARITY_THRESHOLD} threshold "
            f"for '{ebay_title[:40]}' — best was {best_score}"
        )
        return None

    logger.info(
        f"Match found | score={best_score} | "
        f"'{ebay_title[:30]}' -> '{best_match['ali_title'][:30]}'"
    )

    # Return the match with score attached
    return {**best_match, "match_score": best_score}
