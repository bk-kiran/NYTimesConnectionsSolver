"""
NYT Connections Puzzle API Fetcher

Fetches puzzle data directly from the NYT Connections API endpoint.
"""

import requests
import json
import random
from datetime import datetime
from typing import Dict, Any, List


def fetch_puzzle(date: str = None) -> Dict[str, Any]:
    """
    Fetches today's NYT Connections puzzle words from the API.
    
    Args:
        date: Optional date string in YYYY-MM-DD format. If None, uses today's date.
    
    Returns:
        Dictionary with keys:
        - words: List of 16 shuffled puzzle words
        - puzzle_id: Puzzle ID number
        - date: Puzzle date in YYYY-MM-DD format
        
    Raises:
        Exception: If fetching fails or data cannot be extracted
    """
    # Get today's date in YYYY-MM-DD format if not provided
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date}")
    
    # Construct API endpoint
    api_url = f"https://www.nytimes.com/svc/connections/v2/{date}.json"
    
    # Set headers (more complete set to match browser)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nytimes.com/games/connections',
        'Origin': 'https://www.nytimes.com',
    }
    
    try:
        # Use a session to maintain cookies (like a browser)
        session = requests.Session()
        session.headers.update(headers)
        
        # Make GET request with increased timeout and retry logic
        import time
        max_retries = 3
        retry_delay = 2  # seconds
        response = None
        
        for attempt in range(max_retries):
            try:
                response = session.get(api_url, timeout=30)
                break  # Success, exit retry loop
            except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    print(f"Connection timeout (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...", file=__import__('sys').stderr)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"Network error: Failed to connect to NYT API after {max_retries} attempts. This might be due to network connectivity issues, firewall, or the API being temporarily unavailable. Error: {str(e)}")
        
        if response is None:
            raise Exception("Failed to get response after retries")
        
        # Handle 404 specifically with more debugging info
        if response.status_code == 404:
            # Try alternative date formats
            alt_formats = [
                date.replace('-', ''),  # 20260114
                date.replace('-', '/'),  # 2026/01/14
            ]
            
            for alt_date in alt_formats:
                alt_url = f"https://www.nytimes.com/svc/connections/v2/{alt_date}.json"
                alt_response = requests.get(alt_url, headers=headers, timeout=10)
                if alt_response.status_code == 200:
                    # Found it with alternative format, update URL and continue
                    api_url = alt_url
                    response = alt_response
                    break
            
            if response.status_code == 404:
                raise Exception(
                    f"Puzzle not found for date {date} at {api_url}. "
                    "Status: 404. Please check the exact URL format in browser network tab."
                )
        
        response.raise_for_status()
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")
        
        # Validate response structure
        if not isinstance(data, dict):
            raise Exception("Response is not a JSON object")
        
        if 'status' not in data:
            raise Exception("Response missing 'status' field")
        
        if data.get('status') != 'OK':
            raise Exception(f"API returned non-OK status: {data.get('status')}")
        
        # Extract puzzle metadata
        puzzle_id = data.get('id')
        puzzle_date = data.get('print_date') or date
        
        # Extract words from all categories
        if 'categories' not in data:
            raise Exception("Response missing 'categories' field")
        
        if not isinstance(data['categories'], list):
            raise Exception("'categories' is not a list")
        
        words = []
        
        # Loop through all categories
        for category in data['categories']:
            if not isinstance(category, dict):
                continue
            
            # Get cards from this category
            if 'cards' not in category:
                continue
            
            if not isinstance(category['cards'], list):
                continue
            
            # Extract word from each card
            for card in category['cards']:
                if not isinstance(card, dict):
                    continue
                
                # Get the word content
                content = card.get('content')
                if content and isinstance(content, str):
                    content = content.strip()
                    if content:  # Only add non-empty words
                        words.append(content)
        
        # Validate we have exactly 16 words
        if len(words) != 16:
            raise Exception(
                f"Expected 16 words, but found {len(words)} words. "
                f"Words found: {words}"
            )
        
        # IMPORTANT: Shuffle the words randomly so they're not grouped by answer
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)
        
        return {
            "words": shuffled_words,
            "puzzle_id": puzzle_id,
            "date": puzzle_date
        }
        
    except requests.RequestException as e:
        raise Exception(f"Network error fetching puzzle: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing puzzle data: {str(e)}")


def test_url(date: str = "2026-01-14"):
    """Debug function to test different URL formats"""
    formats = [
        f"https://www.nytimes.com/svc/connections/v2/{date}.json",
        f"https://www.nytimes.com/svc/connections/v2/{date.replace('-', '')}.json",
        f"https://www.nytimes.com/svc/connections/v2/{date.replace('-', '/')}.json",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nytimes.com/games/connections',
        'Origin': 'https://www.nytimes.com',
    }
    
    for url in formats:
        print(f"\nTesting: {url}")
        try:
            r = requests.get(url, headers=headers, timeout=5)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                print(f"  ✓ SUCCESS! Found working URL: {url}")
                return url
            elif r.status_code != 404:
                print(f"  Response: {r.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    return None


if __name__ == "__main__":
    """Test the API fetcher"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test-url':
        # Test URL formats
        test_url("2026-01-14")
    else:
        try:
            date = sys.argv[1] if len(sys.argv) > 1 else None
            if date:
                print(f"Fetching NYT Connections puzzle for {date}...")
                result = fetch_puzzle(date)
            else:
                print("Fetching today's NYT Connections puzzle...")
                result = fetch_puzzle()
            
            print("\n✓ Puzzle fetched successfully!")
            print(f"Date: {result['date']}")
            print(f"Puzzle ID: {result['puzzle_id']}")
            print(f"\nWords ({len(result['words'])}):")
            for i, word in enumerate(result['words'], 1):
                print(f"  {i:2d}. {word}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            print("\nTip: Run with '--test-url' to test different URL formats")
            print("     Or check the exact URL in your browser's network tab")

