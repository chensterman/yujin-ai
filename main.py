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


async def demo_element_highlighting():
    """Demonstrate element highlighting capabilities."""
    
    logger = setup_logger("TinderAutomation")
    config = Config()
    
    logger.info("Starting browser automation demo with element highlighting")
    
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
        viewport_size=config.get("browser.viewport_size", {"width": 1920, "height": 1080}),
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
        
        # Now navigate to Tinder (but don't actually log in)
        logger.info("Navigating to Tinder")
        await controller.navigate("https://tinder.com")
        
        # Wait for the page to load
        await page.wait_for_timeout(2000)
        
        # Highlight some UI elements on Tinder's homepage
        logger.info("Highlighting interactive elements on Tinder's homepage")
        
        # Use the highlighter to find and highlight all interactive elements
        num_elements = await highlighter.find_and_highlight_interactive_elements(
            do_highlight=True,
            viewport_expansion=500  # Expand viewport by 500px in all directions
        )
        
        logger.info(f"Found and highlighted {num_elements} interactive elements")
        
        # Wait for user to see the demo
        logger.info("Demo completed.")
        await page.wait_for_timeout(5000)
        
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
    asyncio.run(demo_element_highlighting())