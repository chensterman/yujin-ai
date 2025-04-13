"""
Bumble Chat Assistant

This script automates reading Bumble conversations, generating AI responses,
and sending them back to the chat.
"""

from utils.config import Config
from chat.ai_integration import AIAssistant
from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter
from browser.browser_manager import BrowserManager
from playwright.async_api import Page, ElementHandle
import asyncio
import random
import os
import sys
from typing import List, Dict, Any, Optional
import logging


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


async def navigate_to_bumble(controller: PageController):
    # Navigate to Bumble (assuming logged in) and wait for page to load
    await controller.navigate("https://bumble.com/app")
    await controller.page.wait_for_load_state("domcontentloaded")
    await controller.page.wait_for_timeout(2000)


async def get_latest_conversation(controller: PageController, highlighter: ElementHighlighter) -> List[Dict[str, str]]:
    # Select next chat that is your turn
    # Try both possible selectors for finding the next conversation
    try:
        # First try the notification mark
        notification_selector = "div.contact__notification-mark"
        notification_exists = await controller.page.locator(notification_selector).count() > 0
        
        if notification_exists:
            await highlighter.highlight_and_click(
                selector=notification_selector,
                color="rgba(0, 255, 0, 0.5)",  # Green highlight
                pre_click_delay=1000,  # Wait 1 second before clicking
                post_click_delay=1000   # Wait 1 second after clicking
            )
        else:
            # If notification mark doesn't exist, try the move label
            move_label_selector = "div.contact__move-label"
            await highlighter.highlight_and_click(
                selector=move_label_selector,
                color="rgba(0, 255, 0, 0.5)",  # Green highlight
                pre_click_delay=1000,  # Wait 1 second before clicking
                post_click_delay=1000   # Wait 1 second after clicking
            )
    except Exception as e:
        print(f"Error selecting next conversation: {str(e)}")

    # Get all message elements
    message_elements = await controller.page.locator("div.message").all()
    conversation = []
    for msg_element in message_elements:
        # Highlight the message element
        await highlighter.highlight_element(msg_element,
            color="rgba(0, 255, 0, 0.3)",
            duration=3000)
        # Determine if message is from self or other person
        is_self = await msg_element.evaluate("""
            element => element.classList.contains('message--out')
        """)
        text = await msg_element.text_content()
        # Clean up the text content
        text = text.strip()
        # Skip empty messages
        if text:
            # Determine sender based on message direction
            sender = "self" if is_self else "match"
            # Add message to conversation
            conversation.append({
                "sender": sender,
                "text": text
            })

    return conversation


async def generate_and_send_response(
    controller: PageController, 
    highlighter: ElementHighlighter, 
    conversation: List[Dict[str, str]],
    testing: bool
):
    # Initialize AI assistant
    ai_assistant = AIAssistant()

    # Generate response
    response = await ai_assistant.generate_response(conversation, testing)
    
    # Find the message input field
    input_selector = "div[data-qa-role='chat-input']"
    input_field = await controller.page.query_selector(input_selector)
    await highlighter.highlight_element(input_field,
            color="rgba(0, 255, 0, 0.3)",
            duration=3000)

    if not input_field:
        controller.logger.error("Could not find message input field")
        return False

    # Clear any existing text
    await input_field.click()
    await input_field.press("Control+A")
    await input_field.press("Backspace")

    # Type message with human-like typing
    await type_human_like(input_field, response)

    # Find and click the send button
    send_button = await controller.page.query_selector("button[class='message-field__send']")
    await highlighter.highlight_element(send_button,
            color="rgba(0, 255, 0, 0.5)",
            duration=1000)

    # Actually send the message if testing mode is off
    if not testing:
        await send_button.click()
        await asyncio.sleep(1)


async def type_human_like(element: ElementHandle, text: str):
    """
    Type text with human-like delays and variations.
    Splits text into words and types them with random delays.
    Adds spaces between words except after the last.

    Args:
        element: Element to type into
        text: Text to type
    """
    words = text.split()
    for i, word in enumerate(words):
        await element.type(word, delay=random.randint(50, 100))
        if i < len(words) - 1:
            await element.type(" ")


async def chat_to_latest(
    controller: PageController, 
    highlighter: ElementHighlighter,
    testing: bool = False
):    
    # Navigate to Bumble (assuming logged in) and wait for page to load
    await controller.navigate("https://bumble.com/app")
    await controller.page.wait_for_load_state("domcontentloaded")

    # Purely visual purposes
    await highlighter.find_and_highlight_interactive_elements()
    await asyncio.sleep(1)
    await highlighter.remove_all_highlights()

    # Get latest conversation messages
    conversation = await get_latest_conversation(controller, highlighter)

    # Generate and send response
    if conversation:
        await generate_and_send_response(controller, highlighter, conversation, testing)
    else:
        print("All conversations have been responded to.")
    
