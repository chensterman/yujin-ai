"""
PitchBook Scraper

This script automates scraping company data from PitchBook profiles for multiple companies.
"""

from utils.file_utils import ensure_directory_exists
from scraping.scraper import scrape_company_data
from browser.browser_helpers import initialize_browser, shutdown_browser
import asyncio
import os
import sys
import csv
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
client = OpenAI()


async def search_company(controller, page, company_name):
    """
    Search for a company on PitchBook

    Args:
        controller: The page controller instance
        page: The browser page instance
        company_name: Name of the company to search for

    Returns:
        The company ID if found, None otherwise
    """
    try:
        # Navigate to the PitchBook homepage
        await controller.navigate("https://my.pitchbook.com/")
        print(f"Searching for company: {company_name}")

        # Wait for page to load
        await page.wait_for_load_state("networkidle", timeout=20000)

        # Find and click on the search box using the exact ID from the HTML
        print("Looking for search box...")
        try:
            search_box = await page.wait_for_selector('#general-search-input', timeout=10000)
            if not search_box:
                # Try alternate selectors if ID doesn't work
                search_box = await page.wait_for_selector('input[placeholder="Search PitchBook..."]', timeout=5000)
        except Exception as e:
            print(f"Error finding search box by ID: {str(e)}")
            # Try the placeholder as fallback
            search_box = await page.wait_for_selector('input[placeholder="Search PitchBook..."]', timeout=5000)

        if not search_box:
            print("Search box not found. Looking for any input element...")
            # Last resort: look for any input element
            search_box = await page.wait_for_selector('input', timeout=5000)

        if search_box:
            print("Search box found. Clicking and typing...")
            # Click the search box and type the company name
            await search_box.click()
            await search_box.fill(company_name)
            await page.keyboard.press("Enter")

            # Wait for search results
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Look for company results
            print("Looking for company results...")
            company_results = await page.query_selector_all('a[href*="/profile/"][href*="/company/"]')

            if company_results and len(company_results) > 0:
                print(f"Found {len(company_results)} company results")
                # Get the first result's href
                href = await company_results[0].get_attribute('href')
                if href:
                    # Extract company ID from the URL
                    import re
                    match = re.search(r'/profile/([^/]+)/company', href)
                    if match:
                        company_id = match.group(1)
                        print(f"Found company ID: {company_id}")
                        return company_id

            print("No company results found")
            return None
        else:
            print("Could not find search box")
            return None
    except Exception as e:
        print(f"Error during company search: {str(e)}")
        return None


async def process_company(controller, highlighter, page, company_name):
    """
    Process a single company: search and scrape data

    Args:
        controller: The page controller instance
        highlighter: The element highlighter instance
        page: The browser page instance
        company_name: Name of the company to process
    """
    try:
        # Search for the company
        company_id = await search_company(controller, page, company_name)

        if not company_id:
            print(f"Unable to find company ID for {company_name}. Skipping...")
            return

        # Perform scraping
        company_data = await scrape_company_data(
            controller,
            highlighter,
            page,
            company_id
        )

        if company_data:
            print(
                f"Successfully scraped data for {company_data.get('name', company_name)}")
            # Ensure we have a directory based on company name
            ensure_directory_exists(
                f"data/json/{company_name.replace(' ', '_')}")
            # Save the data with a company-specific filename
            from utils.file_utils import save_to_json
            save_to_json(
                company_data, f"data/json/{company_name.replace(' ', '_')}/company_data.json")
        else:
            print(f"Failed to scrape company data for {company_name}")

    except Exception as e:
        print(f"Error processing company {company_name}: {str(e)}")


async def main(csv_file_path=None):
    """
    Main function that orchestrates the scraping workflow for multiple companies

    Args:
        csv_file_path: Path to the CSV file containing company names
    """
    if not csv_file_path:
        csv_file_path = "/Users/emmythamakaison/Documents/yujin-ai/data/csv/portfolio_companies.csv"

    # Create necessary directories
    ensure_directory_exists("data/screenshots")
    ensure_directory_exists("data/json")
    ensure_directory_exists("logs")

    print(f"Starting PitchBook scraper for companies in {csv_file_path}")

    # Initialize browser
    browser_manager, page, highlighter, controller = await initialize_browser()
    print("Browser started successfully")

    try:
        # Read companies from CSV
        companies = []
        with open(csv_file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row and row[0]:  # Check if row is not empty
                    companies.append(row[0])
                    if len(companies) >= 5:  # Only process 5 companies for now
                        break

        print(f"Found {len(companies)} companies to process")

        # Process each company
        for i, company_name in enumerate(companies):
            print(f"Processing company {i+1}/{len(companies)}: {company_name}")
            await process_company(controller, highlighter, page, company_name)

            # Add a small delay between companies to avoid rate limiting
            await asyncio.sleep(2)

    except Exception as e:
        print(f"Error during processing: {str(e)}")
    finally:
        # Ensure browser is closed properly
        await shutdown_browser(browser_manager)
        print("Scraping process completed")


if __name__ == "__main__":
    # Parse command line arguments if any
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None

    # Run the scraper
    asyncio.run(main(csv_path))
