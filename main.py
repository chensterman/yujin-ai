"""
Tinder Automation Main Script

This script demonstrates browser automation with element highlighting
for Tinder swiping and messaging.
"""

from utils.config import Config
from browser import PageController, ElementHighlighter, BrowserManager
from swipe import swipe_on_latest
from chat import chat_to_latest
import os
import asyncio


async def browser_init():
    """Setup browser automation."""

    config = Config()

    # Initialize the browser
    browser_manager = BrowserManager(
        headless=config.get("browser.headless", False),
        slow_mo=config.get("browser.slow_mo", 50),
        viewport_size=config.get("browser.viewport_size", {
                                 "width": 1080, "height": 1920}),
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


# Define main async function
async def main():
    # Initialize browser classes
    browser_manager, page, highlighter, controller = await browser_init()
    
    # Swipe on one profile
    await swipe_on_latest(controller, highlighter, testing=True)
    
    # Chat to latest unresponded message (if any)
    await chat_to_latest(controller, highlighter, testing=True)
    
    # Close browser
    await browser_manager.close()


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/screenshots", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # Run the main function
    asyncio.run(main())
