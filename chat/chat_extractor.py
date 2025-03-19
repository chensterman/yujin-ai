"""
Chat Extractor for Bumble Automation

This module handles extracting chat conversations from Bumble.
"""

import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import Page, ElementHandle
import logging

from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter


class ChatExtractor:
    """Extracts chat conversations from Bumble."""

    def __init__(self, page_controller: PageController):
        """
        Initialize the chat extractor.

        Args:
            page_controller: PageController instance for page interactions
        """
        self.controller = page_controller
        self.page = page_controller.page
        self.highlighter = page_controller.highlighter
        self.logger = logging.getLogger("ChatExtractor")

    async def navigate_to_chats(self) -> bool:
        """Navigate to the Bumble chat section."""
        try:
            # Navigate to the connections/chat page
            await self.controller.navigate("https://bumble.com/app/connections")
            self.logger.info("Navigated to Bumble connections page")

            # Wait for the chat interface to load
            await self.page.wait_for_load_state("networkidle")
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to chats: {str(e)}")
            return False

    async def get_chat_list(self) -> List[ElementHandle]:
        """
        Get list of available chat conversations.

        Returns:
            List of ElementHandles for chat conversations
        """
        try:
            # Wait for chat list to load
            await self.page.wait_for_selector("div[data-qa-role='conversation-item']",
                                              timeout=10000)

            # Get all chat items
            chat_items = await self.page.query_selector_all("div[data-qa-role='conversation-item']")

            # Highlight all chat items if available
            if self.highlighter and chat_items:
                for i, chat in enumerate(chat_items):
                    await self.highlighter.highlight(chat,
                                                     color="rgba(255, 165, 0, 0.3)",
                                                     duration=500)
                    await asyncio.sleep(0.1)  # Small delay between highlights

            self.logger.info(f"Found {len(chat_items)} chat conversations")
            return chat_items
        except Exception as e:
            self.logger.error(f"Error getting chat list: {str(e)}")
            return []

    async def select_chat(self, chat_item: ElementHandle) -> bool:
        """
        Select a specific chat conversation.

        Args:
            chat_item: ElementHandle for the chat to select

        Returns:
            True if chat was successfully selected
        """
        try:
            # Highlight the chat we're about to click
            if self.highlighter:
                await self.highlighter.highlight(chat_item,
                                                 color="rgba(0, 255, 0, 0.5)",
                                                 duration=1000)

            # Click on the chat item
            await chat_item.click()

            # Wait for chat to load
            await self.page.wait_for_selector("div[data-qa-role='message-text']",
                                              timeout=5000)

            self.logger.info("Chat conversation selected successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to select chat: {str(e)}")
            return False

    async def extract_conversation(self) -> List[Dict[str, str]]:
        """
        Extract the current conversation messages.

        Returns:
            List of message dictionaries with 'sender' and 'text' keys
        """
        try:
            # Wait for messages to load
            await self.page.wait_for_selector("div[data-qa-role='message']",
                                              timeout=5000)

            # Get all message elements
            message_elements = await self.page.query_selector_all("div[data-qa-role='message']")

            conversation = []

            for msg_element in message_elements:
                # Determine if message is from self or other person
                is_self = await msg_element.evaluate("""
                    element => element.classList.contains('message--outgoing')
                """)

                # Get message text
                text_element = await msg_element.query_selector("div[data-qa-role='message-text']")
                if text_element:
                    text = await text_element.text_content()

                    # Add to conversation
                    conversation.append({
                        'sender': 'user' if is_self else 'match',
                        'text': text.strip()
                    })

                    # Highlight each message as we process it
                    if self.highlighter:
                        color = "rgba(173, 216, 230, 0.5)" if is_self else "rgba(255, 192, 203, 0.5)"
                        await self.highlighter.highlight(msg_element, color=color, duration=300)

            self.logger.info(
                f"Extracted {len(conversation)} messages from conversation")
            return conversation
        except Exception as e:
            self.logger.error(f"Error extracting conversation: {str(e)}")
            return []
