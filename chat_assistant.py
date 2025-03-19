"""
Bumble Chat Assistant

This script automates reading Bumble conversations, generating AI responses,
and sending them back to the chat.
"""

from utils.profile_selector import select_profile_interactive
from utils.config import Config
from utils.logger import setup_logger
from chat.ai_integration import AIAssistant
from chat.chat_responder import ChatResponder
from chat.chat_extractor import ChatExtractor
from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter
from browser.browser_manager import BrowserManager
import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")


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


async def automate_chats(controller: PageController, highlighter: ElementHighlighter):
    try:
        await asyncio.wait_for(controller.navigate("https://bumble.com/app/connections"), timeout=5)
        print("Successfully navigated to Bumble connections")
    except asyncio.TimeoutError:
        print("Navigation timed out, but continuing with execution")
    except Exception as e:
        print(f"Navigation error: {str(e)}, but continuing with execution")
    chat_extractor = ChatExtractor(controller)
    chat_responder = ChatResponder(controller)
    ai_assistant = AIAssistant()

    # # Get list of available chats
    chat_items = await chat_extractor.get_chat_list()
    print(len(chat_items))
    if not chat_items:
        print("No chat conversations found")
        return

    for chat in chat_items:
        await highlighter.highlight_specific_element(chat)
        await asyncio.sleep(1)

    # num_elements = await highlighter.find_and_highlight_interactive_elements(
    #     do_highlight=True,
    #     viewport_expansion=500  # Expand viewport by 500px in all directions
    # )


async def process_chats():
    browser_manager, page, highlighter, controller = await browser_init()
    print("Browser started successfully")
    await automate_chats(controller, highlighter)
    print("Automated set up successfully")
    await browser_manager.close()

    # # Process each chat
    # for i, chat_item in enumerate(chat_items):
    #     logger.info(f"Processing chat {i+1}/{len(chat_items)}")

    #     # Select the chat
    #     success = await chat_extractor.select_chat(chat_item)
    #     if not success:
    #         logger.warning(f"Failed to select chat {i+1}, skipping")
    #         continue

    #     # Extract conversation
    #     conversation = await chat_extractor.extract_conversation()
    #     if not conversation:
    #         logger.warning(f"No messages found in chat {i+1}, skipping")
    #         continue

    #     # Generate AI response
    #     response = await ai_assistant.generate_response(conversation)

    #     # Send the response
    #     await chat_responder.send_message(response)

    #     # Wait a bit before moving to next chat
    #     await asyncio.sleep(2)

    #     # Go back to chat list for next iteration
    #     await controller.navigate("https://bumble.com/app/connections")
    #     await page.wait_for_load_state("networkidle")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/screenshots", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Run the chat assistant
    asyncio.run(process_chats())
