# utils/session_manager.py
# -----------------------------------------------
# Manages persistent browser profiles.
# Saves cookies and browser state between runs.
# Makes the tool look like a returning human user
# instead of a fresh bot every single time.
# -----------------------------------------------

import os
from config import PROFILES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def get_profile_path(site: str) -> str:
    """
    Returns the folder path for a site's browser profile.

    site = "ebay" or "aliexpress"

    Example:
        get_profile_path("ebay")
        # returns "data/profiles/ebay_profile"
    """
    path = os.path.join(PROFILES_DIR, f"{site}_profile")
    os.makedirs(path, exist_ok=True)  # creates folder if it doesn't exist yet
    logger.debug(f"Profile path for [{site}]: {path}")
    return path
