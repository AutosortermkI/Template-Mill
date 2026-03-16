"""Base class for all Playwright scrapers with common patterns."""

import asyncio
import random
from typing import Self

from playwright.async_api import Browser, Page, async_playwright

from src.shared.config import settings
from src.shared.exceptions import CaptchaDetectedError, SelectorChangedError
from src.shared.logger import get_logger

logger = get_logger("scraper_base")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


class ScraperBase:
    """Base class for Playwright-based scrapers."""

    def __init__(self, headless: bool | None = None) -> None:
        self.headless = headless if headless is not None else settings.SCRAPE_HEADLESS
        self._browser: Browser | None = None
        self._playwright = None

    async def __aenter__(self) -> Self:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        logger.info("browser_launched", headless=self.headless)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("browser_closed")

    async def new_page(self) -> Page:
        """Create a new browser page with randomized user agent."""
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")
        context = await self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
        )
        return await context.new_page()

    async def random_delay(
        self,
        min_sec: float | None = None,
        max_sec: float | None = None,
    ) -> None:
        """Sleep for a random duration within configured bounds."""
        min_s = min_sec if min_sec is not None else settings.SCRAPE_MIN_DELAY
        max_s = max_sec if max_sec is not None else settings.SCRAPE_MAX_DELAY
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)

    async def check_captcha(self, page: Page) -> None:
        """Check for CAPTCHA presence and raise if detected."""
        captcha_selectors = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "#captcha",
            ".captcha-container",
        ]
        for selector in captcha_selectors:
            if await page.locator(selector).count() > 0:
                logger.warning("captcha_detected", url=page.url)
                raise CaptchaDetectedError(f"CAPTCHA detected on {page.url}")

    async def safe_query(self, page: Page, selector: str, description: str) -> list[str]:
        """Query elements with a selector, raising SelectorChangedError if none found."""
        elements = page.locator(selector)
        count = await elements.count()
        if count == 0:
            logger.warning("selector_empty", selector=selector, description=description, url=page.url)
            raise SelectorChangedError(
                f"Selector '{selector}' ({description}) returned no results on {page.url}"
            )
        return await elements.all_text_contents()
