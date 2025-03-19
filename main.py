"""
Tinder Automation Main Script

This script demonstrates browser automation with element highlighting
for Tinder swiping and messaging.
"""

import asyncio
import os
import sys
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser.browser_manager import BrowserManager
from browser.element_highlighter import ElementHighlighter
from browser.page_controller import PageController
from utils.logger import setup_logger
from utils.config import Config
from utils.profile_selector import select_profile_interactive

async def browser_init():
    """Setup browser automation."""
    
    config = Config()
    
    # Initialize the browser
    browser_manager = BrowserManager(
        headless=config.get("browser.headless", False),
        slow_mo=config.get("browser.slow_mo", 50),
        viewport_size=config.get("browser.viewport_size", {"width": 1920, "height": 1080}),
        user_agent=config.get("browser.user_agent"),
        enable_stealth_mode=config.get("browser.stealth_mode", True),
        randomize_behavior=config.get("browser.randomize_behavior", True),
        bypass_webdriver_flags=config.get("browser.bypass_webdriver_flags", True),
        proxy=config.get("browser.proxy"),
    )
    
    # Initialize the highlighter and page controller
    page = await browser_manager.start()
    highlighter = ElementHighlighter(page)
    await highlighter.setup()  # Call the setup method to initialize the highlighter
    controller = PageController(page, highlighter)
    await controller.setup()  # Call the setup method on the controller

    return browser_manager, page, highlighter, controller
    

async def demo_element_highlighting(controller: PageController, highlighter: ElementHighlighter):
    """Navigate to Bumble and highlight interactive elements."""
    
    # Navigate to Bumble (but don't actually log in)
    await controller.navigate("https://bumble.com/app")
    
    # Use the highlighter to find and highlight all interactive elements
    num_elements = await highlighter.find_and_highlight_interactive_elements(
        do_highlight=True,
        viewport_expansion=500  # Expand viewport by 500px in all directions
    )

# Define main async function
async def main():
    # Run automations
    browser_manager, page, highlighter, controller = await browser_init()
    await demo_element_highlighting(controller, highlighter)
    await browser_manager.close()

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/screenshots", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Run the main function
    asyncio.run(main())