"""
PitchBook Scraper

This module handles the scraping of company data from PitchBook.
"""

import asyncio
import json
from typing import Any, Dict

from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter
from utils.file_utils import save_to_json


async def fetch_api_data(page, url, endpoint_name):
    """
    Fetch data from a PitchBook API endpoint

    Args:
        page: The browser page instance
        url: The API endpoint URL
        endpoint_name: Name of the endpoint for logging

    Returns:
        The JSON response data
    """
    print(f"Fetching {endpoint_name} API endpoint: {url}")

    response = await page.evaluate(f"""
        async () => {{
            try {{
                const response = await fetch("{url}");
                if (response.ok) {{
                    const data = await response.json();
                    return data;
                }} else {{
                    return {{ error: "Failed to fetch {endpoint_name}", status: response.status }};
                }}
            }} catch (err) {{
                return {{ error: err.toString() }};
            }}
        }}
    """)

    print(f"{endpoint_name} API response received")
    save_to_json(response, f"{endpoint_name}_data.json")
    return response


async def setup_profile_interceptor(page, profile_url):
    """
    Set up an interceptor for profile data

    Args:
        page: The browser page instance
        profile_url: The profile URL to watch for

    Returns:
        None
    """
    profile_data = None

    async def on_response(response):
        nonlocal profile_data
        if profile_url in response.url:
            try:
                data = await response.json()
                print("🚀 Intercepted profile API data")
                profile_data = data
                save_to_json(data, "profile_data.json")
            except Exception as e:
                print("❗️ Failed to parse JSON:", e)

    page.on("response", on_response)
    return profile_data


async def scrape_company_data(controller: PageController, highlighter: ElementHighlighter, page: Any, company_id: str = "65298-34"):
    """
    Scrape company data from PitchBook

    Args:
        controller: The page controller instance
        highlighter: The element highlighter instance
        page: The browser page instance
        company_id: The PitchBook company ID

    Returns:
        Dictionary containing all scraped data
    """
    # Define API endpoints
    base_url = f"https://my.pitchbook.com"
    investors_url = f"{base_url}/web-api/profiles/{company_id}/company/investor-lead-partners"
    profile_url = f"{base_url}/profile/{company_id}/company/profile#investors"
    founders_api_url = f"{base_url}/web-api/profiles/{company_id}/company/executives/current?page=1&pageSize=10"
    general_info_url = f"{base_url}/web-api/profiles/{company_id}/company/general-info"

    # Initialize data containers
    profile_data = None
    investors_data = None
    general_info_data = None
    founders_data = None

    # Set up profile data interceptor
    profile_data = await setup_profile_interceptor(page, profile_url)

    try:
        # Navigate to the profile page
        await asyncio.wait_for(controller.navigate(profile_url), timeout=10)
        print("Successfully navigated to Pitchbook profile page")

        # Wait for page to load
        # await page.wait_for_load_state("networkidle", timeout=10000)

        # Fetch data from API endpoints
        investors_data = await fetch_api_data(page, investors_url, "investors")
        general_info_data = await fetch_api_data(page, general_info_url, "general_info")
        founders_data = await fetch_api_data(page, founders_api_url, "founders")

    except asyncio.TimeoutError:
        print("Navigation timed out, but continuing with execution")
    except Exception as e:
        print(f"Navigation error: {str(e)}, but continuing with execution")

    # Save all data to a combined JSON file if available
    combined_data = None
    if general_info_data:
        name = general_info_data.get("name", "Unknown")
        description = general_info_data.get("description", "")
        website = general_info_data.get("website", "")
        business_status = general_info_data.get("businessStatus", "")

        combined_data = {
            "name": name,
            "description": description,
            "website": website,
            "businessStatus": business_status,
            "investors_data": investors_data,
            "founders_data": founders_data,
            "general_info_data": general_info_data,
        }
        save_to_json(combined_data, "combined_data.json")

    return combined_data
