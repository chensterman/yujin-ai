import requests
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Pimeyes email and password from environment variables
PIMEYES_EMAIL = os.environ.get('PIMEYES_EMAIL')
PIMEYES_PASSWORD = os.environ.get('PIMEYES_PASSWORD')

def _login_to_pimeyes(email=PIMEYES_EMAIL, password=PIMEYES_PASSWORD):
    """Login to Pimeyes using email and password
    
    Args:
        email (str): Email address for login
        password (str): Password for login
        user_id (str): Pimeyes user ID
        
    Returns:
        tuple: (API response JSON, session cookies dict)
    """
    url = "https://pimeyes.com/api/login/login-form"
    
    # Prepare the login payload
    payload = {
        "email": email,
        "password": password,
        "remember": True
    }
    
    try:
        # Make the POST request for login
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print(f"Login Status Code: {response.status_code}")
        print(f"Login Response: {response.json()}")
        
        # Extract cookies from the response
        login_cookies = {}
        for cookie in response.cookies:
            login_cookies[cookie.name] = cookie.value
            print(f"Got login cookie: {cookie.name} = {cookie.value[:20]}...")
        
        return response.json(), login_cookies
    
    except requests.exceptions.RequestException as e:
        print(f"Error during login: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Error Response: {e.response.text}")
            except:
                pass
        return None, {}


def _check_premium_token_status(login_cookies=None):
    """Check the status of the premium token from Pimeyes API and return session cookies
    
    Args:
        user_id (str): Pimeyes user ID
        
    Returns:
        tuple: (API response JSON, session cookies dict)
    """
    url = "https://pimeyes.com/api/premium-token/status"
    headers = {}
    
    # Convert login cookies to Cookie header format, then add to headers
    if not login_cookies:
        print("No login cookies provided.")
        return None, {}
    cookie_header = "; ".join([f"{k}={v}" for k, v in login_cookies.items()])
    headers["Cookie"] = cookie_header
    
    try:
        # Use headers for cookies instead of cookies parameter
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Print status code and response
        print(f"Status Check Status Code: {response.status_code}")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error in status check request: {e}")
        return None


def _upload_image(image_url, login_cookies=None):
    """Upload an image file to Pimeyes API using session cookies
    
    Args:
        image_url (str): URL to the image file
        login_cookies (dict): Login cookies from login_to_pimeyes
        
    Returns:
        dict: JSON response from the API
    """
    # Read and encode the image
    try:
        # Read the image file
        image_data = requests.get(image_url).content
        # Encode image to base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
            
        # Get image format
        image_format = os.path.splitext(image_url)[1].lower().replace('.', '')
        if image_format == 'jpg':
            image_format = 'jpeg'  # Convert jpg to jpeg for MIME type
        
        # Create data URI
        data_uri = f"data:image/{image_format};base64,{encoded_image}"
    except Exception as e:
        print(f"Error reading image file: {e}")
        return None
    
    # API endpoint
    url = "https://pimeyes.com/api/upload/file"
    
    # Headers
    headers = {}
    
    # Convert login cookies to Cookie header format, then add to headers
    if not login_cookies:
        print("No login cookies provided.")
        return None
    cookie_header = "; ".join([f"{k}={v}" for k, v in login_cookies.items()])
    headers["Cookie"] = cookie_header
    
    # Prepare the JSON payload with the base64 encoded image in data URI format
    payload = {
        "image": data_uri
    }
    
    try:
        # Make the POST request with cookies in header instead of cookies parameter
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        print(f"Upload Status Code: {response.status_code}")
        response_json = response.json()
        
        # Extract face IDs from the response
        face_ids = []
        if 'faces' in response_json and isinstance(response_json['faces'], list):
            for face in response_json['faces']:
                if 'id' in face:
                    face_ids.append(face['id'])
        else:
            print("No face IDs found in response")
        
        return face_ids
    
    except requests.exceptions.RequestException as e:
        print(f"Error in upload request: {e}")
        return None


def _search_faces(face_ids, login_cookies=None, search_type="PREMIUM_SEARCH", time_range="any"):
    """Search for faces using the Pimeyes search API
    
    Args:
        face_ids (list): List of face IDs to search for
        login_cookies (dict): Login cookies from login_to_pimeyes
        search_type (str): Type of search (e.g., "PREMIUM_SEARCH")
        time_range (str): Time range for search (e.g., "any")
        
    Returns:
        dict: JSON response from the API
    """
    url = "https://pimeyes.com/api/search/new"
    
    headers = {}
    
    # Convert login cookies to Cookie header format, then add to headers
    if not login_cookies:
        print("No login cookies provided.")
        return None
    cookie_header = "; ".join([f"{k}={v}" for k, v in login_cookies.items()])
    headers["Cookie"] = cookie_header
    
    # Prepare the JSON payload with face IDs
    payload = {
        "faces": face_ids,
        "time": time_range,
        "type": search_type
    }
    
    try:
        # Make the POST request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        print(f"Search Status Code: {response.status_code}")
        response_json = response.json()
        
        # Extract searchHash and apiUrl
        search_hash = response_json.get('searchHash')
        api_url = response_json.get('apiUrl')
            
        # Return a tuple with searchHash and apiUrl
        return search_hash, api_url
    
    except requests.exceptions.RequestException as e:
        print(f"Error in search request: {e}")
        return None, None
        

def _get_search_results(api_url, search_hash):
    """Get search results using the API URL and search hash
    
    Args:
        api_url (str): The API URL to fetch results from
        search_hash (str): The search hash to identify the search
        
    Returns:
        dict: JSON response with search results
    """
    # Prepare the payload with the search hash
    payload = {
        "hash": search_hash,
        "limit": 250,
        "offset": 0,
        "resultsCategory": None,
        "retryCount": 0
    }
    
    try:
        # Make the POST request to get search results
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        print(f"Results Status Code: {response.status_code}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error getting search results: {e}")
        return None


def img_to_urls(image_url):
    # Login to Pimeyes
    print("\n=== Logging in to Pimeyes ===")
    login_response, login_cookies = _login_to_pimeyes()
    
    # Get session cookies from status check
    print("\n=== Checking Premium Token Status ===")
    status_response = _check_premium_token_status(login_cookies)
    print(f"Status Check Response: {status_response}")
    
    # Upload the image with session cookies
    print("\n=== Uploading Image ===")
    face_ids = _upload_image(image_url, login_cookies)
    print(f"Extracted {len(face_ids)} face IDs: {face_ids}")
    
    if not face_ids:
        print("\nUpload failed or no faces detected.")
        return
    
    # Call search API with the face IDs
    print("\n=== Searching for Faces ===")
    search_hash, api_url = _search_faces(face_ids, login_cookies)
    print(f"Search Hash: {search_hash}")
    print(f"API URL: {api_url}")
    
    if not search_hash or not api_url:
        print("\nSearch failed or missing required information.")
        return
    
    # Get search results using the API URL
    print("\n=== Getting Search Results ===")
    results = _get_search_results(api_url, search_hash)['results']
    print(f"Search Results: {results}")
    return results