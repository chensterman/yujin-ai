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
        viewport_size=config.get("browser.viewport_size", {"width": 1280, "height": 800}),
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
        
        # Navigate to a demo site first
        logger.info("Navigating to a demo site to show highlighting")
        await controller.navigate("https://www.google.com")
        
        # Highlight the search box
        logger.info("Highlighting the search box")
        search_selector = 'textarea[name="q"]'
        await highlighter.highlight(
            search_selector,
            color=config.get("highlighting.default_color", "rgba(255, 105, 180, 0.5)"),
            duration=3000,
            pulse_effect=True
        )
        
        # Fill the search box
        await page.fill(search_selector, "Tinder automation")
        
        # Highlight and click the search button
        logger.info("Highlighting and clicking the search button")
        await controller.click_element(
            'input[name="btnK"]', 
            highlight_color=config.get("highlighting.success_color", "rgba(0, 255, 0, 0.5)"),
            pre_click_delay=1000
        )
        
        # Wait for search results
        await controller.wait_for_navigation()
        
        # Highlight search results
        logger.info("Highlighting search results")
        results = await page.query_selector_all("h3")
        for i, result in enumerate(results[:5]):  # Highlight first 5 results
            # Create a selector for this specific result
            result_selector = f"h3:nth-of-type({i+1})"
            
            # Highlight with different colors
            color = f"rgba({50 + i * 40}, {100 + i * 30}, {200 - i * 20}, 0.5)"
            await highlighter.highlight(result_selector, color=color, duration=2000 + i * 500)
            
            # Small delay between highlights
            await page.wait_for_timeout(300)
        
        # Wait a bit to see all highlights
        logger.info("Waiting to see all highlights")
        await page.wait_for_timeout(3000)
        
        # Now navigate to Tinder (but don't actually log in)
        logger.info("Navigating to Tinder")
        await controller.navigate("https://tinder.com")
        
        # Wait for the page to load
        await page.wait_for_timeout(2000)
        
        # Highlight some UI elements on Tinder's homepage
        logger.info("Highlighting UI elements on Tinder's homepage")
        
        # Try to find and highlight login buttons
        buttons = [
            'a[href="/"]',  # Logo
            'a[href*="download"]',  # Download buttons
            'a[href*="login"]',  # Login buttons
            'button',  # Generic buttons
        ]
        
        for selector in buttons:
            elements = await page.query_selector_all(selector)
            for i, element in enumerate(elements):
                try:
                    # Create a more specific selector
                    specific_selector = f"{selector}:nth-of-type({i+1})"
                    
                    # Highlight with a random color
                    color = f"rgba({100 + i * 30}, {150 - i * 10}, {200}, 0.5)"
                    await highlighter.highlight(specific_selector, color=color, duration=2000)
                    
                    # Small delay between highlights
                    await page.wait_for_timeout(300)
                except Exception as e:
                    logger.warning(f"Failed to highlight element {specific_selector}: {str(e)}")
        
        # Take a screenshot
        screenshots_dir = config.get("storage.screenshots_dir", "data/screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshots_dir, "tinder_demo.png")
        await controller.screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
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
