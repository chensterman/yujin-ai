import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

# Import functions from other modules
from researcher.pimeyes_api import img_to_urls
from researcher.url_scraper import batch_scrape
from researcher.llm_aggregate import aggregate_person_info

def research_image(
    image_url: str, 
    person_context: str,
    delay: float = 0.1, 
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Process an image through the complete pipeline:
    1. Extract URLs from Pimeyes using the image
    2. Scrape content from those URLs
    3. Aggregate person information from scraped content
    
    Args:
        image_url (str): URL to the image file
        person_context (str): Context about the person
        delay (float): Delay between URL scraping requests
        verbose (bool): Whether to print detailed progress information
        
    Returns:
        Dictionary with structured information about the person or None if processing failed
    """ 
    # Step 1: Get URLs from Pimeyes using the image
    if verbose:
        print(f"\n=== Processing image: {image_url} ===")
    
    pimeyes_results = img_to_urls(image_url)
    
    if not pimeyes_results:
        print("Error: Failed to get results from Pimeyes.")
        return None
        
    # Extract URLs from Pimeyes results
    urls = []
    try:
        for result in pimeyes_results:
            url = result.get('sourceUrl')
            if url and url not in urls:
                urls.append(url)
                
        if verbose:
            print(f"\n=== Found {len(urls)} unique URLs ===")
            for i, url in enumerate(urls[:10]):
                print(f"{i+1}. {url}")
            if len(urls) > 10:
                print(f"...and {len(urls) - 10} more")
    except Exception as e:
        print(f"Error extracting URLs from Pimeyes results: {e}")
        return None
        
    if not urls:
        print("No URLs found in Pimeyes results.")
        return None
        
    # Step 2: Scrape content from the URLs
    if verbose:
        print(f"\n=== Scraping {len(urls)} URLs ===")
        
    scraped_results = batch_scrape(pimeyes_results, delay=delay)
    
    successful_scrapes = [result for result in scraped_results if result.get('success')]
    if verbose:
        print(f"Successfully scraped {len(successful_scrapes)}/{len(urls)} URLs")
        
    if not successful_scrapes:
        print("No successful URL scrapes.")
        return None
        
    # Step 3: Aggregate person information from scraped content
    if verbose:
        print("\n=== Aggregating person information ===")
        
    person_info = aggregate_person_info(successful_scrapes, person_context)
    
    if not person_info:
        print("Failed to aggregate person information.")
        return None
    
    # Person info contains:
    # - name
    # - description
    # - source_urls
    # - image_url
    return person_info