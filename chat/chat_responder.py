"""
Chat Responder for Bumble Automation

This module handles sending AI-generated responses to Bumble chats.
"""

import asyncio
import random
from typing import Optional
import logging
from playwright.async_api import Page, ElementHandle

from browser.page_controller import PageController


class ChatResponder:
    """Sends responses to Bumble chats."""

    def __init__(self, page_controller: PageController):
        """
        Initialize the chat responder.

        Args:
            page_controller: PageController instance for page interactions
        """
        self.controller = page_controller
        self.page = page_controller.page
        self.highlighter = page_controller.highlighter
        self.logger = logging.getLogger("ChatResponder")

    async def send_message(self, message: str) -> bool:
        """
        Send a message in the current chat.

        Args:
            message: Message text to send

        Returns:
            True if message was sent successfully
        """
        try:
            # Find the message input field
            input_selector = "textarea[data-qa-role='messenger-input']"
            input_field = await self.page.query_selector(input_selector)

            if not input_field:
                self.logger.error("Could not find message input field")
                return False

            # Highlight the input field
            if self.highlighter:
                await self.highlighter.highlight(input_field,
                                                 color="rgba(0, 255, 0, 0.3)",
                                                 duration=1000)

            # Clear any existing text
            await input_field.click()
            await input_field.press("Control+A")
            await input_field.press("Backspace")

            # Type message with human-like typing
            await self.type_human_like(input_field, message)

            # Find and click the send button
            send_button = await self.page.query_selector("button[data-qa-role='send-message']")

            if not send_button:
                self.logger.error("Could not find send button")
                return False

            # Highlight the send button
            if self.highlighter:
                await self.highlighter.highlight(send_button,
                                                 color="rgba(0, 255, 0, 0.5)",
                                                 duration=1000)

            # Click the send button
            await send_button.click()

            # Wait for message to be sent
            await asyncio.sleep(1)

            self.logger.info(f"Message sent successfully: {message[:30]}...")
            return True
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False

    async def type_human_like(self, element: ElementHandle, text: str):
        """
        Type text with human-like delays and variations.

        Args:
            element: Element to type into
            text: Text to type
        """
        # Split text into chunks to simulate natural typing rhythm
        words = text.split()

        for i, word in enumerate(words):
            # Type the word
            await element.type(word, delay=random.randint(50, 150))

            # Add space after word (except for last word)
            if i < len(words) - 1:
                await element.type(" ")

                # Occasionally pause as if thinking
                if random.random() < 0.2:
                    await asyncio.sleep(random.uniform(0.5, 1.5))
