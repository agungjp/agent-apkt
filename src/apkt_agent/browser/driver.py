"""Playwright browser driver management (sync API)."""

from pathlib import Path
from typing import Tuple, Any

from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

from ..errors import BrowserError
from ..logging_ import get_logger
from ..workspace import RunContext
from ..config import Config


def open_browser(ctx: RunContext, config: Config) -> Tuple[Playwright, Browser, BrowserContext, Page]:
    """Open browser with Playwright sync API.
    
    Args:
        ctx: Run context with directories
        config: Configuration object
        
    Returns:
        Tuple of (playwright, browser, context, page)
        
    Raises:
        BrowserError: If browser fails to launch
    """
    logger = get_logger()
    
    try:
        headless = config.get('runtime.headless', False)
        download_dir = str(ctx.excel_dir)
        
        logger.info(f"Opening browser (headless={headless})")
        logger.info(f"Download directory: {download_dir}")
        
        # Start Playwright with timeout
        import time
        start_time = time.time()
        playwright = sync_playwright().start()
        elapsed = time.time() - start_time
        logger.info(f"Playwright started in {elapsed:.2f}s")
        
        # Launch Chromium browser with timeout and args
        logger.info("Launching Chromium...")
        browser = playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            timeout=60000
        )
        logger.info("Chromium launched")
        
        # Create context with download settings
        context = browser.new_context(
            accept_downloads=True,
        )
        
        # Set default timeout to 30 seconds
        context.set_default_timeout(30000)
        
        # Create page
        page = context.new_page()
        logger.info("Page created")
        
        logger.info("Browser opened successfully")
        
        return playwright, browser, context, page
        
    except Exception as e:
        logger.error(f"Failed to open browser: {e}", exc_info=True)
        raise BrowserError(f"Failed to open browser: {e}")


def close_browser(playwright: Playwright, browser: Browser, context: BrowserContext) -> None:
    """Close browser and cleanup resources.
    
    Args:
        playwright: Playwright instance
        browser: Browser instance
        context: Browser context
    """
    logger = get_logger()
    
    try:
        if context:
            logger.info("Closing browser context")
            context.close()
        
        if browser:
            logger.info("Closing browser")
            browser.close()
        
        if playwright:
            logger.info("Stopping Playwright")
            playwright.stop()
            
        logger.info("Browser closed successfully")
        
    except Exception as e:
        logger.warning(f"Error during browser cleanup: {e}")


# Keep class for backward compatibility (deprecated)
class BrowserDriver:
    """Manages Playwright browser instance (deprecated - use open_browser/close_browser)."""
    
    def __init__(self, headless: bool = True):
        """Initialize browser driver.
        
        Args:
            headless: Run browser in headless mode
        """
        self.logger = get_logger()
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
