import requests
import html2text
import time
import os
import pprint
from bs4 import BeautifulSoup
from readability import Document
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

# Get Firecrawl API key from environment variable
FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY')


def _url_scraper(url, delay=0.1, min_content_length=50):
    """
    Scrape the content of a URL and convert it to markdown format
    
    Args:
        url (str): The URL to scrape
        delay (int): Delay in seconds between requests to avoid rate limiting
        min_content_length (int): Minimum length of markdown content before trying Firecrawl
        
    Returns:
        tuple: (success status, markdown content or error message)
    """
    try:
        # Add delay to avoid rate limiting
        time.sleep(delay)
        
        # Send request to get the HTML content with realistic browser headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML content using readability
        doc = Document(response.text)
        title = doc.title()
        content = doc.summary()
        
        # Use BeautifulSoup to clean up the HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'iframe', 'noscript']):
            element.decompose()
            
        # Convert HTML to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0  # No wrapping
        markdown_content = h.handle(str(soup))
        
        # Check if content is too short and try Firecrawl as fallback
        if len(markdown_content) < min_content_length:
            try:
                app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
                response = app.scrape_url(url=url, params={
                    'formats': ['markdown'],
                    'excludeTags': ['img', 'picture', 'svg', 'canvas', 'figure', 'iframe', 'video', 'audio', 'source', 'track']
                })
                
                if "markdown" in response:
                    firecrawl_markdown = response['markdown']
                    if len(firecrawl_markdown) > len(markdown_content):
                        markdown_content = firecrawl_markdown
            except Exception as e:
                print(f"Error using Firecrawl API: {e}")
    
        # Return success and markdown content
        return True, markdown_content
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching URL: {e}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error processing content: {e}"
        print(error_msg)
        return False, error_msg


def batch_scrape(data: List[Dict[str, Any]], delay=0.1) -> List[Dict[str, Any]]:
    """
    Scrape multiple URLs and convert them to markdown format
    
    Args:
        data (list): List of data dicts
        delay (int): Delay in seconds between requests
        
    Returns:
        list: List of dictionaries with URL, success status, and content
    """
    results = []
    
    for item in data:
        # Skip items with low likeness score
        likeness_score = item.get('quality', 0)
        if likeness_score < 0.8:
            continue

        # Check if sourceUrl exists and is valid
        source_url = item.get('sourceUrl')
        if not source_url or not isinstance(source_url, str):
            continue
            
        # Validate URL format
        if not source_url.startswith(('http://', 'https://')):
            continue
            
        # Check URL accessibility with error handling
        try:
            source_response = requests.get(source_url, timeout=2)
            if source_response.status_code != 200:
                continue
        except requests.exceptions.RequestException as e:
            continue
            
        # Check if thumbnailUrl exists and is valid (optional)
        thumbnail_url = item.get('thumbnailUrl')
        if thumbnail_url and isinstance(thumbnail_url, str) and thumbnail_url.startswith(('http://', 'https://')):
            try:
                thumbnail_response = requests.get(thumbnail_url, timeout=2)
                if thumbnail_response.status_code != 200:
                    continue
            except requests.exceptions.RequestException as e:
                continue
        
        success, content = _url_scraper(source_url, delay)
        results.append({
            "url": source_url, 
            "success": success, 
            "content": content,
            "thumbnailUrl": thumbnail_url,
            "likenessScore": likeness_score
        })
        
    return results