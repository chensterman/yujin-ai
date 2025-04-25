"""
PitchBook Scraper (Test Version)

This script is a test version that only processes the first 3 companies from the CSV file.
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
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
client = OpenAI()

# Rate limiting settings
MAX_REQUESTS_PER_HOUR = 300  # Maximum number of requests per hour


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
        # await page.wait_for_load_state("networkidle", timeout=10000)

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
            print("Entered Search")

            # # Wait for search results
            # await page.wait_for_load_state("networkidle", timeout=10000)

            # Look for company results
            print("Looking for company results...")
            # company_results = await page.query_selector_all('a[href*="/profile/"][href*="/company/"]')
            company_results = await page.wait_for_selector('div[data-testid="page-result-card"]', timeout=10000)

            if company_results:
                print(f"Found company results")
                await company_results.click()
                print("Clicked on the first company result...")

                # Wait for the company profile page to load
                # await page.wait_for_load_state("networkidle", timeout=10000)

                # Extract company ID from the current URL
                current_url = page.url
                import re
                match = re.search(r'/profile/([^/]+)/company', current_url)
                if match:
                    company_id = match.group(1)
                    print(f"Found company ID: {company_id}")
                    return company_id
                else:
                    print("Could not extract company ID from URL")
                    return None

            print("No company results found")
            return None
        else:
            print("Could not find search box")
            return None
    except Exception as e:
        print(f"Error during company search: {str(e)}")
        return None


async def process_company(controller, highlighter, page, company_name, request_tracker):
    """
    Process a single company: search and scrape data

    Args:
        controller: The page controller instance
        highlighter: The element highlighter instance
        page: The browser page instance
        company_name: Name of the company to process
        request_tracker: Dictionary tracking request timestamps for rate limiting
    """
    try:
        # Check rate limits before proceeding
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)

        # Remove timestamps older than 1 hour
        request_tracker["timestamps"] = [
            ts for ts in request_tracker["timestamps"] if ts > hour_ago]

        # Check if we've hit the hourly rate limit
        if len(request_tracker["timestamps"]) >= MAX_REQUESTS_PER_HOUR:
            wait_time = (request_tracker["timestamps"]
                         [0] - hour_ago).total_seconds()
            print(
                f"Rate limit reached. Waiting {wait_time:.2f} seconds before next request.")
            # Wait until we're under the limit again
            await asyncio.sleep(wait_time + 1)
            # Clean up the timestamps again after waiting
            current_time = datetime.now()
            hour_ago = current_time - timedelta(hours=1)
            request_tracker["timestamps"] = [
                ts for ts in request_tracker["timestamps"] if ts > hour_ago]

        # Add current request to the tracker
        request_tracker["timestamps"].append(current_time)

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
            company_dir = company_name.replace(' ', '_')
            ensure_directory_exists(f"data/json/{company_dir}")
            # Save the data with a company-specific filename
            from utils.file_utils import save_to_json
            save_to_json(company_data, f"{company_dir}/company_data.json")
        else:
            print(f"Failed to scrape company data for {company_name}")

    except Exception as e:
        print(f"Error processing company {company_name}: {str(e)}")


async def main(csv_file_path=None):
    """
    Main function that orchestrates the scraping workflow for a limited number of companies

    Args:
        csv_file_path: Path to the CSV file containing company names
    """
    if not csv_file_path:
        csv_file_path = "/Users/emmythamakaison/Documents/yujin-ai/data/csv/portfolio_companies.csv"

    # Create necessary directories
    ensure_directory_exists("data/screenshots")
    ensure_directory_exists("data/json")
    ensure_directory_exists("logs")

    print(
        f"Starting PitchBook scraper with rate limit of {MAX_REQUESTS_PER_HOUR} requests per hour")

    # Initialize browser
    browser_manager, page, highlighter, controller = await initialize_browser()
    print("Browser started successfully")

    # Initialize request tracker for rate limiting
    request_tracker = {"timestamps": []}

    try:
        # Read companies from CSV
        companies = []
        with open(csv_file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row and row[0]:  # Check if row is not empty
                    companies.append(row[0])

        print(f"Found {len(companies)} companies in CSV file")

        # Track companies to process and companies to skip
        companies_to_process = []
        companies_skipped = []

        # Check which companies have already been processed
        for company_name in companies:
            company_dir = company_name.replace(' ', '_')
            company_path = f"data/json/{company_dir}"
            if os.path.exists(company_path) and os.path.isdir(company_path):
                # Check if company_data.json exists in the directory
                if os.path.exists(f"{company_path}/company_data.json"):
                    companies_skipped.append(company_name)
                    continue
            companies_to_process.append(company_name)

        print(f"Skipping {len(companies_skipped)} already processed companies")
        print(f"Processing {len(companies_to_process)} companies")

        # Process each company
        for i, company_name in enumerate(companies_to_process):
            print(
                f"Processing company {i+1}/{len(companies_to_process)}: {company_name}")
            await process_company(controller, highlighter, page, company_name, request_tracker)

            # Add a delay between companies to avoid rate limiting
            await asyncio.sleep(5)

            # Log current rate limit status
            current_time = datetime.now()
            hour_ago = current_time - timedelta(hours=1)
            request_tracker["timestamps"] = [
                ts for ts in request_tracker["timestamps"] if ts > hour_ago]
            print(
                f"Rate limit status: {len(request_tracker['timestamps'])}/{MAX_REQUESTS_PER_HOUR} requests in the last hour")

    except Exception as e:
        print(f"Error during processing: {str(e)}")
    finally:
        # Ensure browser is closed properly
        await shutdown_browser(browser_manager)
        print("Scraping process completed")


if __name__ == "__main__":
    # Parse command line arguments if any
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    # Set max number of companies to process if specified
    max_companies = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    # Run the test scraper
    asyncio.run(main(csv_path))
