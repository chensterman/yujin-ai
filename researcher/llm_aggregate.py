import os
import json
from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

def aggregate_person_info(scraped_results: List[Dict[str, Any]], person_context: str) -> Optional[Dict[str, str]]:
    """
    Analyze scraped content using ChatGPT API to extract structured information about a person.
    
    Args:
        scraped_results: List of dictionaries with keys 'url', 'success', and 'content'
        
    Returns:
        Dictionary with structured information about the person (name and description)
        or None if no valid information could be extracted
    """
    if not OPENAI_API_KEY:
        print("Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return None
        
    # Filter for successful scrapes only
    successful_scrapes = [result for result in scraped_results if result.get('success')]
    
    if not successful_scrapes:
        print("No successful scrapes to analyze")
        return None
    
    # Combine content from all successful scrapes
    combined_content = ""
    for scrape in successful_scrapes:
        content = scrape.get('content', '')
        url = scrape.get('url', '')
        if content and isinstance(content, str):
            # Add URL as context and limit content length to avoid token limits
            content_snippet = content[:5000] if len(content) > 5000 else content
            combined_content += f"\n\nContent from {url}:\n{content_snippet}"
    
    # Prepare prompt for ChatGPT
    system_prompt = """
    You are an AI assistant tasked with extracting structured information about a person from various web sources.
    Analyze the provided content and extract the following information about the person of interest:
    1. Name: The full name of the person
    2. Description: A concise description of who this person is, their background, and notable information
    
    All of the web sources you are given are likely to be about the same person. There may be some noise. 
    Do your best to isolate the information about the person of interest.
    If you cannot determine certain information with confidence, indicate this with 'Unknown'.
    Format your response as a JSON object with the keys 'name' and 'description'.
    """
    
    user_prompt = f"""
    Here is some context about the person of interest (scraped from a dating app):
    {person_context}
    
    You will be given scraped data from various web pages where the person of interest
    had their image featured. Your task is to extract structured information about the
    person of interest from this data, if it exists on the web pages given. Include the
    context provided in your response, along with any info from the web pages.

    Web page data:
    \n\n{combined_content}
    """
    
    try:
        # Call ChatGPT API
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        # Extract and parse the response
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # Ensure the expected keys are present
        if 'name' not in result_json or 'description' not in result_json:
            print("Error: API response missing required fields")
            return None
            
        metadata = [{"url": result.get('url'), "thumbnailUrl": result.get('thumbnailUrl'), "likenessScore": result.get('likenessScore')} for result in successful_scrapes]
        return {
            'name': result_json['name'],
            'description': result_json['description'],
            'metadata': metadata
        }
        
    except Exception as e:
        print(f"Error calling ChatGPT API: {e}")
        return None


def analyze_multiple_people(batch_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process multiple sets of scraped results, each potentially about a different person.
    
    Args:
        batch_results: List of lists of scraped results, where each inner list represents
                      content about a potentially different person
                      
    Returns:
        List of dictionaries with structured information about each person
    """
    results = []
    
    for i, person_results in enumerate(batch_results):
        print(f"Analyzing person {i+1}/{len(batch_results)}...")
        person_info = aggregate_person_info(person_results)
        
        if person_info:
            # Add the original URLs to the result
            results.append(person_info)
        
    return results
