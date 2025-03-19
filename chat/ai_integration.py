"""
AI Integration for Bumble Chat Assistant

This module handles integration with OpenAI for generating chat responses.
"""

import os
import json
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")


class AIAssistant:
    """Handles integration with OpenAI for chat responses."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the AI assistant.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")

        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger("AIAssistant")

    def format_conversation(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format conversation for OpenAI API.

        Args:
            messages: List of message dictionaries with 'sender' and 'text' keys

        Returns:
            Formatted messages for OpenAI API
        """
        formatted_messages = [
            {"role": "system", "content": "You are a helpful assistant providing dating advice. Be friendly, engaging, and respectful. Keep responses concise and natural."}
        ]

        for msg in messages:
            role = "user" if msg["sender"] == "match" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg["text"]
            })

        # Add a final user message asking for a response
        formatted_messages.append({
            "role": "user",
            "content": "Please provide a thoughtful response to continue this conversation."
        })

        return formatted_messages

    async def generate_response(self, conversation: List[Dict[str, str]]) -> str:
        """
        Generate a response based on the conversation.

        Args:
            conversation: List of message dictionaries with 'sender' and 'text' keys

        Returns:
            Generated response text
        """
        try:
            formatted_messages = self.format_conversation(conversation)

            self.logger.info(
                f"Sending request to OpenAI with {len(formatted_messages)} messages")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=150,
                temperature=0.7
            )

            reply = response.choices[0].message.content.strip()
            self.logger.info(f"Generated response: {reply[:50]}...")

            return reply
        except Exception as e:
            self.logger.error(f"Error generating AI response: {str(e)}")
            return "I'm having trouble connecting to my brain right now. Let me try again later!"
