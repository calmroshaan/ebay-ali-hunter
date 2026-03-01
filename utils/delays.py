# utils/delays.py
# -----------------------------------------------
# Provides human-like random delays between actions.
# Uses gaussian (bell curve) distribution —
# most waits land near the average, some shorter,
# some longer. Much harder to detect than fixed delays.
# -----------------------------------------------

import asyncio
import random
from utils.logger import get_logger

logger = get_logger(__name__)


async def human_delay(mean: float, std_dev: float, label: str = "") -> None:
    """
    Wait for a random amount of time.

    mean    = average wait in seconds
    std_dev = how much it varies
    label   = just a name shown in logs so you know which delay fired

    Example:
        await human_delay(4.0, 1.2, "page_load")
        # waits roughly 4 seconds, sometimes 2.8, sometimes 5.2
    """
    duration = max(0.5, random.gauss(mean, std_dev))
    logger.debug(f"Delay [{label}]: {duration:.2f}s")
    await asyncio.sleep(duration)