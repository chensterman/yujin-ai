"""
Tinder Automation Main Script

This script demonstrates browser automation with element highlighting
for Tinder swiping and messaging.
"""

from utils.profile_selector import select_profile_interactive
from utils.config import Config
from utils.logger import setup_logger
from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter
from browser.browser_manager import BrowserManager
import asyncio
import os
import sys
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def swipe():
    """Helper function for swiping/not swiping"""

    logger = setup_logger("TinderAutomation")
    config = Config()

    logger.info("Starting swiping automation")

    # Allow user to select a Chrome profile
    user_data_dir = select_profile_interactive()
    if user_data_dir:
        logger.info(f"Using Chrome profile at: {user_data_dir}")
    else:
        logger.info("Using a fresh browser instance (no profile)")

    # Initialize the browser
    browser_manager = BrowserManager(
        headless=config.get("browser.headless", False),
        slow_mo=config.get("browser.slow_mo", 50),
        viewport_size=config.get("browser.viewport_size", {
                                 "width": 1280, "height": 800}),
        user_agent=config.get("browser.user_agent"),
        user_data_dir=user_data_dir
    )

    try:
        # Start the browser
        page = await browser_manager.start()
        logger.info("Browser started successfully")

        # Initialize the highlighter and page controller
        highlighter = ElementHighlighter(page)
        await highlighter.setup()  # Call the setup method to initialize the highlighter
        controller = PageController(page, highlighter)
        await controller.setup()  # Call the setup method on the controller

        # Navigate to tinder
        logger.info("Navigating to Tinder")
        await controller.navigate("https://bumble.com/app/connections")

        # Wait for the page to load
        await page.wait_for_timeout(2000)

        logger.info("Looking for the Like button")
        try:
            # Try to find the Like button using multiple selectors for better reliability
            like_button = page.get_by_role("button", name="Like", exact=True)
            if like_button:
                logger.info(
                    f"Found Like button using selector")
                # Highlight the Like button before clicking with a bright red border
                await highlighter.highlight(like_button,
                                            color="rgba(255, 0, 0, 0.3)",
                                            border_width=3,
                                            duration=2000,
                                            pulse_effect=True)
                await page.wait_for_timeout(1000)
                # Click the Like button
                logger.info("Clicking the Like button")
                await like_button.click()
                logger.info("Like button clicked successfully")
                await page.wait_for_timeout(2000)

            if not like_button:
                logger.warning(
                    "Could not find the Like button with any of the selectors")

        except Exception as e:
            logger.error(
                f"Error when trying to click the Like button: {str(e)}")

    except Exception as e:
        logger.error(f"Error during demo: {str(e)}")
    finally:
        # Close the browser
        await browser_manager.close()
        logger.info("Browser closed")


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/screenshots", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Run the demo
    asyncio.run(swipe())
