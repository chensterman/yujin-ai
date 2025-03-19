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
from utils.face_analysis import ensure_shape_predictor_exists, process_image_from_url
import tempfile
import cv2
import pathlib
from playwright.async_api import Page
import asyncio
import os
import sys
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def browser_init():
    """Setup browser automation."""

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


async def demo_element_highlighting(controller: PageController, highlighter: ElementHighlighter):
    """Navigate to Bumble and highlight interactive elements."""

    # Navigate to Bumble (but don't actually log in)
    await controller.navigate("https://bumble.com/app")

    # Use the highlighter to find and highlight all interactive elements
    num_elements = await highlighter.find_and_highlight_interactive_elements(
        do_highlight=True,
        viewport_expansion=500  # Expand viewport by 500px in all directions
    )
    await controller.page.wait_for_load_state("domcontentloaded")
    await controller.page.wait_for_timeout(2000)


async def profile_rating(controller: PageController, highlighter: ElementHighlighter):
    """Rate profiles based on attractiveness."""

    # Highlight all text on profile, wait for user to see the highlights, then remove
    encounters_selector = "div.encounters-album__stories-container"
    await highlighter.highlight_all_text(encounters_selector)
    await controller.page.wait_for_timeout(3000)
    await highlighter.remove_all_highlights()

    # Try multiple selectors for profile photos
    profile_photo_selectors = [
        'img.media-box__picture-image',
        'img.profile__photo',
        'div.encounters-story-profile-image img',
        'div[data-qa-role="profile-card"] img',
        'div[data-qa-role="profile-photo"] img',
        'img[alt*="profile"]',
        'img[alt*="photo"]'
    ]

    profile_photos = []

    # Try each selector
    for selector in profile_photo_selectors:
        photos = await controller.page.query_selector_all(selector)
        if photos and len(photos) > 0:
            profile_photos = photos
            break

    if not profile_photos:
        print("No profile photos found with any of the known selectors.")
        return False

    # Extract src URLs from all photos
    photo_urls = []
    for photo in profile_photos:
        try:
            src = await photo.get_attribute('src')
            if src:
                # Add HTTPS prefix if missing
                if not src.startswith('https:'):
                    src = 'https:' + src
                # Filter out SVG files
                if not src.endswith('.svg'):
                    photo_urls.append(src)
        except Exception as e:
            print(f"Error extracting src from photo: {e}")

    if not photo_urls:
        print("No valid photo URLs found. The page structure might have changed.")
        return False

    # Download the shape predictor model if needed
    await ensure_shape_predictor_exists()

    root_dir = pathlib.Path(__file__).parent.absolute()
    js_file_path = os.path.join(root_dir, "static", "js", "photo_display.js")

    # Read the JavaScript file
    with open(js_file_path, 'r') as file:
        js_code = file.read()

    # Inject the JavaScript into the page
    await controller.page.add_script_tag(content=js_code)

    # Cycle through each photo and gather total + count for attractiveness
    total_attractiveness = 0
    count = 0
    for i, url in enumerate(photo_urls):
        try:
            # Process the image using the face_analysis module
            landmarks, attractiveness_score, metrics, image_dimensions = await process_image_from_url(url, i)

            # Use the injected JavaScript to display the photo with landmarks and metrics
            if landmarks and attractiveness_score and metrics and image_dimensions:

                # Update total attractiveness and count
                total_attractiveness += attractiveness_score
                count += 1

                # Convert landmarks to a format that can be passed to JavaScript
                landmarks_js = [[point[0], point[1]] for point in landmarks]

                # Create a data object to pass to JavaScript
                data = {
                    'url': url,
                    'landmarks': landmarks_js,
                    'score': attractiveness_score,
                    'metrics': metrics,
                    'originalWidth': image_dimensions[0],
                    'originalHeight': image_dimensions[1]
                }

                # Pass the data to the JavaScript function
                await controller.page.evaluate("""
                    (data) => {
                        window.photoDisplay.displayPhoto(
                            data.url, 
                            data.landmarks, 
                            data.score, 
                            data.metrics,
                            data.originalWidth,
                            data.originalHeight
                        );
                    }
                """, data)
            else:
                # If no landmarks were detected, just display the photo
                await controller.page.evaluate("(url) => window.photoDisplay.displayPhoto(url, null, null, null)", url)

            # Wait for the specified duration
            # Display each photo for 2 seconds
            await controller.page.wait_for_timeout(2000)

        except Exception as e:
            print(f"Error processing photo: {e}")

    # Remove the display container at the end
    await controller.page.evaluate("() => window.photoDisplay.removePhotoDisplay()")

    # Calculate average attractiveness and return True if average attractiveness is greater than 7.0
    average_attractiveness = total_attractiveness / count if count > 0 else 0
    if average_attractiveness > 7.0:
        return True
    return False


async def swipe(swipe_right: bool, controller: PageController, highlighter: ElementHighlighter):
    if swipe_right:
        like_button_selector = "div.encounters-action.tooltip-activator.encounters-action--like"
        await highlighter.highlight_and_click(
            selector=like_button_selector,
            color="rgba(0, 255, 0, 0.5)",  # Green highlight
            pre_click_delay=2000,  # Wait 2 seconds before clicking
            post_click_delay=2000   # Wait 2 seconds after clicking
        )
    else:
        dislike_button_selector = "div.encounters-action.tooltip-activator.encounters-action--dislike"
        await highlighter.highlight_and_click(
            selector=dislike_button_selector,
            color="rgba(255, 0, 0, 0.5)",  # Red highlight
            pre_click_delay=2000,  # Wait 2 seconds before clicking
            post_click_delay=2000   # Wait 2 seconds after clicking
        )

    # Wait for the swipe animation to complete
    await controller.page.wait_for_timeout(1000)

    # If match occurs, check for "continue bumbling" button and click it if present
    continue_button = "button.button.button--size-m:has-text('Continue Bumbling')"
    await highlighter.highlight_and_click(
        selector=continue_button,
        color="rgba(0, 255, 0, 0.5)",  # Green highlight
        pre_click_delay=2000,  # Wait 2 seconds before clicking
        post_click_delay=2000   # Wait 2 seconds after clicking
    )


# Define main async function
async def main():
    # Run automations
    browser_manager, page, highlighter, controller = await browser_init()
    await demo_element_highlighting(controller, highlighter)
    print("set up browser ")
    # Run automations
    await navigate_to_bumble(controller)
    for i in range(3):
        swipe_right = await profile_rating(controller, highlighter)
        await swipe(swipe_right, controller, highlighter)

    # Close browser
    await browser_manager.close()

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/screenshots", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    os.makedirs("models", exist_ok=True)

    # Run the main function
    asyncio.run(main())
