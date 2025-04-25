"""
Browser Helpers

This module provides helper functions for browser initialization and management.
"""

import asyncio
from typing import Tuple, Any

from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter
from browser.browser_manager import BrowserManager
from utils.config import Config


async def initialize_browser() -> Tuple[BrowserManager, Any, ElementHighlighter, PageController]:
    """
    Initialize the browser environment with all necessary components

    Returns:
        Tuple containing (browser_manager, page, highlighter, controller)
    """
    config = Config()

    # Initialize the browser
    browser_manager = BrowserManager(
        headless=config.get("browser.headless", False),
        slow_mo=config.get("browser.slow_mo", 50),
        viewport_size=config.get("browser.viewport_size", {
                                 "width": 1920, "height": 1080}),
        user_agent=config.get("browser.user_agent"),
        enable_stealth_mode=config.get("browser.stealth_mode", True),
        randomize_behavior=config.get("browser.randomize_behavior", True),
        bypass_webdriver_flags=config.get(
            "browser.bypass_webdriver_flags", True),
        proxy=config.get("browser.proxy"),
    )

    # Initialize the highlighter and page controller
    page = await browser_manager.start()
    highlighter = ElementHighlighter(page)
    await highlighter.setup()  # Call the setup method to initialize the highlighter
    controller = PageController(page, highlighter)
    await controller.setup()  # Call the setup method on the controller

    return browser_manager, page, highlighter, controller


async def shutdown_browser(browser_manager: BrowserManager, wait_time: int = 5) -> None:
    """
    Properly shutdown the browser

    Args:
        browser_manager: The browser manager instance
        wait_time: Time to wait before closing (in seconds)
    """
    # Sleep for a moment before closing the browser
    await asyncio.sleep(wait_time)
    print("Closing browser...")
    await browser_manager.close()
