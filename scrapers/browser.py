# scrapers/browser.py
# -----------------------------------------------
# Creates and manages the Playwright browser.
# Applies anti-detection settings.
# Uses persistent profiles from session_manager
# so cookies are saved between runs.
# -----------------------------------------------

import random
from playwright.async_api import async_playwright, Browser, BrowserContext
from playwright_stealth import stealth_async
from config import VIEWPORT, USER_AGENTS, HEADLESS
from utils.logger import get_logger
from utils.session_manager import get_profile_path

logger = get_logger(__name__)


class BrowserManager:
    """
    Use this class to start the browser and create
    a new context (tab session) for each site.

    Usage in other files:
        manager = BrowserManager()
        await manager.start()
        context = await manager.new_context("ebay")
        # ... do scraping ...
        await manager.close()
    """

    def __init__(self):
        self._playwright = None
        self._browser: Browser = None

    async def start(self):
        """Launch the browser. Call this once at the start."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=HEADLESS,   # True = no visible window. Change to False to watch it work.
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1366,768",
            ]
        )
        logger.info("Browser launched")

    async def new_context(self, site: str) -> BrowserContext:
        """
        Create a new browser session for a site.
        Loads the saved profile for that site.

        site = "ebay" or "aliexpress"
        """
        user_agent = random.choice(USER_AGENTS)
        profile_path = get_profile_path(site)

        context = await self._browser.new_context(
            viewport=VIEWPORT,
            user_agent=user_agent,
            locale="en-US",
            timezone_id="America/New_York",
            java_script_enabled=True,
            storage_state=self._load_state(site),
        )

        logger.debug(f"New context for [{site}] | UA: {user_agent[:50]}...")
        return context

    def _load_state(self, site: str):
        """
        Load saved cookies if they exist.
        Returns None on first run — that's fine.
        """
        import os, json
        state_file = os.path.join(get_profile_path(site), "state.json")
        if os.path.exists(state_file):
            logger.debug(f"Loading saved session state for [{site}]")
            with open(state_file, "r") as f:
                return json.load(f)
        logger.debug(f"No saved state for [{site}] — starting fresh")
        return None

    async def save_state(self, context: BrowserContext, site: str):
        """
        Save cookies and session after scraping.
        Call this after each scraping session.
        """
        import os
        state_file = os.path.join(get_profile_path(site), "state.json")
        state = await context.storage_state()
        with open(state_file, "w") as f:
            import json
            json.dump(state, f)
        logger.debug(f"Session state saved for [{site}]")

    async def close(self):
        """Shut down the browser cleanly."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")