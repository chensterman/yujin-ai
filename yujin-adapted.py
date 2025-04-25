"""
Bumble Chat Assistant (Legacy Entry Point)

This script provides backward compatibility with the original script.
It's recommended to use pitchbook_scraper.py directly for new development.
"""

from utils.file_utils import ensure_directory_exists
from scraping.scraper import scrape_company_data
from browser.browser_helpers import initialize_browser, shutdown_browser
import asyncio
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
client = OpenAI()

# Import from the new modular structure


async def browser_init():
    """Legacy wrapper for browser initialization."""
    return await initialize_browser()


def save_to_json(data, filename):
    """Legacy wrapper for save_to_json."""
    from utils.file_utils import save_to_json as new_save_to_json
    new_save_to_json(data, filename)


async def automate_scraping(controller, highlighter, page):
    """Legacy wrapper for scrape_company_data."""
    return await scrape_company_data(controller, highlighter, page)


async def process_chats():
    """Legacy wrapper for the main process."""
    # Create necessary directories
    ensure_directory_exists("data/screenshots")
    ensure_directory_exists("logs")

    # Initialize browser
    browser_manager, page, highlighter, controller = await browser_init()
    print("Browser started successfully")

    # Scrape data
    await automate_scraping(controller, highlighter, page)

    # Close browser
    await shutdown_browser(browser_manager)


if __name__ == "__main__":
    # Create necessary directories
    ensure_directory_exists("data/screenshots")
    ensure_directory_exists("logs")

    # Run the chat assistant
    asyncio.run(process_chats())
