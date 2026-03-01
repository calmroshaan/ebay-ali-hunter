# matching/matcher.py
# -----------------------------------------------
# Compares eBay product titles against AliExpress
# candidates using two stage approach:
#   Stage 1 — RapidFuzz quick filter (free, instant)
#   Stage 2 — Claude AI for final decision (accurate)
# -----------------------------------------------

import os
import anthropic
from rapidfuzz import fuzz
from dotenv import load_dotenv
from config import SIMILARITY_THRESHOLD
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Initialize Anthropic client
_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def find_best_match(ebay_title: str, ali_results: list[dict]) -> dict | None:
    """
    Takes one eBay title and a list of AliExpress candidates.
    Stage 1 — RapidFuzz filters obvious non-matches quickly
    Stage 2 — Claude AI picks the best match from remaining candidates
    Returns best matching AliExpress product or None.
    """
    if not ali_results:
        logger.debug("No AliExpress candidates to match against")
        return None

    # --- Stage 1: RapidFuzz pre-filter ---
    # Keep only candidates with score above minimum threshold
    candidates = []
    for item in ali_results:
        ali_title = item.get("ali_title", "")
        if not ali_title:
            continue
        score = fuzz.token_sort_ratio(
            ebay_title.lower(),
            ali_title.lower()
        )
        if score >= SIMILARITY_THRESHOLD:
            candidates.append({**item, "fuzzy_score": score})

    # If no candidates passed fuzzy filter
    if not candidates:
        logger.debug(f"No fuzzy matches above {SIMILARITY_THRESHOLD} for '{ebay_title[:40]}'")
        return None

    # Sort by fuzzy score — best first
    candidates.sort(key=lambda x: x["fuzzy_score"], reverse=True)

    # Keep top 5 candidates for AI to evaluate
    top_candidates = candidates[:5]

    # If only one candidate — no need for AI
    if len(top_candidates) == 1:
        match = top_candidates[0]
        match["match_score"] = match["fuzzy_score"]
        logger.info(f"Single match | '{ebay_title[:30]}' -> '{match['ali_title'][:30]}'")
        return match

    # --- Stage 2: Claude AI picks best match ---
    best = _ai_pick_best(ebay_title, top_candidates)
    return best


def _ai_pick_best(ebay_title: str, candidates: list[dict]) -> dict | None:
    """
    Sends eBay title and AliExpress candidates to Claude.
    Claude picks the best matching product or says NONE.
    """
    # Build candidate list for prompt
    candidate_text = ""
    for i, c in enumerate(candidates):
        candidate_text += f"{i+1}. {c['ali_title']} (Price: ${c['ali_price']})\n"

    prompt = f"""You are a product matching assistant for dropshipping.

eBay Product: "{ebay_title}"

AliExpress Candidates:
{candidate_text}

Which AliExpress candidate is the best match for the eBay product?
Consider: same product type, similar specs, compatible use case.

Reply with ONLY a single number (1, 2, 3, 4, or 5) for the best match.
If none are a good match reply with: NONE"""

    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response.content[0].text.strip().upper()
        logger.debug(f"AI reply: '{reply}' for '{ebay_title[:40]}'")

        if reply == "NONE":
            logger.debug(f"AI found no match for '{ebay_title[:40]}'")
            return None

        # Parse the number
        index = int(reply) - 1
        if 0 <= index < len(candidates):
            match = candidates[index]
            match["match_score"] = match["fuzzy_score"]
            logger.info(f"AI match | '{ebay_title[:30]}' -> '{match['ali_title'][:30]}'")
            return match

        return None

    except Exception as e:
        logger.error(f"AI matching failed: {e}")
        # Fallback to best fuzzy match if AI fails
        logger.info("Falling back to fuzzy match")
        match = candidates[0]
        match["match_score"] = match["fuzzy_score"]
        return match