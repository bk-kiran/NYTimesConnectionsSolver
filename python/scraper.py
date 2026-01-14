"""
NYT Connections Puzzle Scraper

Scrapes puzzle data from the New York Times Connections game page.
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime

# Try to import Selenium, but make it optional
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def scrape_nyt_connections() -> Dict[str, Any]:
    """
    Scrapes NYT Connections puzzle words from the game page.
    
    Returns:
        Dictionary with keys:
        - words: List of 16 puzzle words
        - date: Puzzle date in YYYY-MM-DD format
        - puzzle_id: Puzzle ID number
        
    Raises:
        Exception: If scraping fails or data cannot be extracted
    """
    url = "https://www.nytimes.com/games/connections"
    
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Make GET request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 0: Try to find and call API endpoints mentioned in the page
        words = []
        date = None
        puzzle_id = None
        
        # Look for API endpoints in script tags or data attributes
        api_endpoints = []
        script_tags = soup.find_all('script')
        for script in script_tags:
            script_content = script.string
            if not script_content:
                continue
            # Look for API endpoint patterns - more comprehensive
            api_patterns = [
                r'["\']([^"\']*api[^"\']*connections[^"\']*)["\']',
                r'["\']([^"\']*games[^"\']*connections[^"\']*)["\']',
                r'["\']([^"\']*svc[^"\']*connections[^"\']*)["\']',
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.(?:get|post)\(["\']([^"\']+)["\']',
                r'\.get\(["\']([^"\']+)["\']',
                r'url:\s*["\']([^"\']+)["\']',
            ]
            for pattern in api_patterns:
                matches = re.findall(pattern, script_content, re.I)
                api_endpoints.extend(matches)
        
        # Remove duplicates and filter
        api_endpoints = list(set(api_endpoints))
        api_endpoints = [e for e in api_endpoints if 'connections' in e.lower() or 'game' in e.lower()]
        
        # Try API endpoints if found
        for endpoint in api_endpoints[:5]:  # Try up to 5 endpoints
            if not endpoint.startswith('http'):
                # Make it absolute if relative
                if endpoint.startswith('/'):
                    endpoint = f"https://www.nytimes.com{endpoint}"
                elif endpoint.startswith('./') or endpoint.startswith('../'):
                    # Skip relative paths that aren't absolute
                    continue
                else:
                    endpoint = f"https://www.nytimes.com/{endpoint}"
            try:
                api_response = requests.get(endpoint, headers=headers, timeout=5)
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    words, date, puzzle_id = _extract_from_game_data(api_data)
                    if words and len(words) >= 16:
                        break
            except Exception:
                continue
        
        # Look for embedded JSON data in script tags
        # NYT Connections typically embeds data in window.__NEXT_DATA__ or similar
        
        # Method 1: Look for window.__NEXT_DATA__ (Next.js app)
        if not words:
            for script in script_tags:
                script_content = script.string
                if not script_content:
                    continue
                    
                # Try to find __NEXT_DATA__ pattern - improved regex to capture full JSON
                if '__NEXT_DATA__' in script_content:
                    # Try multiple patterns to extract the full JSON object
                    patterns = [
                        r'__NEXT_DATA__\s*=\s*({.+?})\s*</script>',  # Until script end
                        r'__NEXT_DATA__\s*=\s*({.+?})(?=\s*<)',  # Until next tag
                        r'__NEXT_DATA__\s*=\s*({.+?})',  # Original pattern
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script_content, re.DOTALL)
                        if match:
                            try:
                                # Try to parse the JSON
                                json_str = match.group(1)
                                # Find the matching closing brace
                                brace_count = json_str.count('{') - json_str.count('}')
                                if brace_count > 0:
                                    # Need to find more closing braces
                                    remaining = script_content[match.end():]
                                    for i, char in enumerate(remaining):
                                        if char == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                json_str = script_content[match.start(1):match.end(1)+i+1]
                                                break
                                
                                next_data = json.loads(json_str)
                                
                                # Recursively search for game data in the entire structure
                                game_data = _find_game_data_recursive(next_data)
                                
                                if game_data:
                                    words, date, puzzle_id = _extract_from_game_data(game_data)
                                    if words and len(words) >= 16:
                                        break
                                    
                                    # Also try extracting from the entire next_data structure
                                    words, date, puzzle_id = _extract_from_game_data(next_data)
                                    if words and len(words) >= 16:
                                        break
                            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                                continue
                    
                    if words and len(words) >= 16:
                        break
                
                # Method 2: Look for window.gameData or similar patterns
                patterns = [
                    r'window\.gameData\s*=\s*({.+?});',
                    r'gameData\s*=\s*({.+?});',
                    r'puzzleData\s*=\s*({.+?});',
                    r'connectionsData\s*=\s*({.+?});',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script_content, re.DOTALL)
                    if match:
                        try:
                            game_data = json.loads(match.group(1))
                            words, date, puzzle_id = _extract_from_game_data(game_data)
                            if words:
                                break
                        except (json.JSONDecodeError, KeyError, TypeError):
                            continue
                
                if words:
                    break
        
        # Method 3: Look for JSON-LD structured data
        if not words:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    words, date, puzzle_id = _extract_from_game_data(data)
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
        
        # Method 4: Try known NYT Games API endpoints and GraphQL
        if not words:
            # NYT Connections might use a specific API endpoint
            today = datetime.now().strftime('%Y-%m-%d')
            api_endpoints_to_try = [
                f"https://www.nytimes.com/svc/connections/v1/{today}.json",
                f"https://www.nytimes.com/svc/games/v3/connections/{today}.json",
                "https://www.nytimes.com/svc/connections/v1/puzzle.json",
                "https://www.nytimes.com/svc/games/v3/connections/puzzle.json",
                f"https://www.nytimes.com/svc/games/v1/connections/{today}.json",
                "https://www.nytimes.com/svc/games/v1/connections/puzzle.json",
            ]
            
            for api_url in api_endpoints_to_try:
                try:
                    api_response = requests.get(api_url, headers=headers, timeout=5)
                    if api_response.status_code == 200:
                        api_data = api_response.json()
                        words, date, puzzle_id = _extract_from_game_data(api_data)
                        if words and len(words) >= 16:
                            break
                except Exception:
                    continue
            
            # Try GraphQL endpoint (samizdat-graphql.nytimes.com)
            if not words:
                graphql_headers = headers.copy()
                graphql_headers['Content-Type'] = 'application/json'
                graphql_query = {
                    "query": """
                    query GetConnectionsPuzzle($date: String) {
                        connections(date: $date) {
                            id
                            date
                            words
                            groups {
                                words
                            }
                        }
                    }
                    """,
                    "variables": {"date": today}
                }
                try:
                    graphql_response = requests.post(
                        "https://samizdat-graphql.nytimes.com/graphql",
                        json=graphql_query,
                        headers=graphql_headers,
                        timeout=5
                    )
                    if graphql_response.status_code == 200:
                        graphql_data = graphql_response.json()
                        if 'data' in graphql_data and 'connections' in graphql_data['data']:
                            puzzle_data = graphql_data['data']['connections']
                            words, date, puzzle_id = _extract_from_game_data(puzzle_data)
                except Exception:
                    pass
        
        # Method 5: Look for data attributes in HTML elements
        if not words:
            # Try to find words in data attributes or specific HTML structures
            # Look for various possible selectors
            selectors = [
                {'class': re.compile(r'word|tile|card', re.I)},
                {'data-word': True},
                {'data-tile': True},
                {'data-card': True},
            ]
            
            for selector in selectors:
                word_elements = soup.find_all(['div', 'span', 'button'], selector)
                for elem in word_elements:
                    # Try data attributes first
                    text = (
                        elem.get('data-word') or
                        elem.get('data-tile') or
                        elem.get('data-card') or
                        elem.get_text(strip=True)
                    )
                    if text and len(text.split()) == 1 and text not in words:  # Single word, not duplicate
                        words.append(text)
                        if len(words) >= 16:
                            break
                if len(words) >= 16:
                    break
        
        # Method 6: Search all script tags for any JSON that might contain words
        if not words:
            for script in script_tags:
                script_content = script.string
                if not script_content or len(script_content) < 100:
                    continue
                
                # Look for any JSON-like structures that might contain words
                # Search for patterns like: ["word1", "word2", ...]
                word_list_pattern = r'\[(?:["\']([^"\']+)["\'],?\s*){4,}'
                matches = re.findall(word_list_pattern, script_content)
                if matches:
                    # Check if we found 16 words
                    potential_words = [m for m in matches if len(m.split()) == 1]
                    if len(potential_words) >= 16:
                        words = potential_words[:16]
                        break
                
                # Also try to find any JSON objects with "words" key
                json_pattern = r'\{[^{}]*"words"\s*:\s*\[([^\]]+)\][^{}]*\}'
                json_matches = re.findall(json_pattern, script_content)
                for match in json_matches:
                    # Extract quoted strings
                    word_matches = re.findall(r'["\']([^"\']+)["\']', match)
                    if len(word_matches) >= 16:
                        words = word_matches[:16]
                        break
                
                if words:
                    break
        
        # Method 7: Search the entire response text for JSON structures
        if not words:
            # Look for large JSON objects in the response
            # Try to find JSON objects that might contain puzzle data
            json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response.text, re.DOTALL)
            for json_str in json_objects[:20]:  # Limit to first 20 to avoid too much processing
                if len(json_str) > 500:  # Only check reasonably sized JSON
                    try:
                        parsed = json.loads(json_str)
                        words, date, puzzle_id = _extract_from_game_data(parsed)
                        if words and len(words) >= 16:
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        # Method 8: Use Selenium to execute JavaScript and wait for data to load
        # Run Selenium if we don't have 16 words yet
        if len(words) < 16 and SELENIUM_AVAILABLE:
            try:
                print("Attempting to use Selenium to extract puzzle data...")
                selenium_words, selenium_date, selenium_id = _scrape_with_selenium(url)
                if selenium_words and len(selenium_words) >= 16:
                    words = selenium_words
                    date = selenium_date or date
                    puzzle_id = selenium_id or puzzle_id
                    print(f"Successfully extracted {len(words)} words using Selenium")
                elif selenium_words:
                    print(f"Selenium found {len(selenium_words)} words (need 16)")
            except Exception as e:
                # Log the error but continue
                print(f"Warning: Selenium scraping failed: {str(e)}")
                import traceback
                traceback.print_exc()
                pass
        
        if not words or len(words) != 16:
            # Provide more helpful error message
            selenium_note = ""
            if not SELENIUM_AVAILABLE:
                selenium_note = "\nNote: Selenium is not installed. Install it with: pip install selenium webdriver-manager\n"
            
            error_msg = (
                f"Could not extract 16 words. Found {len(words)} words. "
                "The page structure may have changed.\n"
                "Possible reasons:\n"
                "1. The puzzle data is loaded dynamically via JavaScript after page load\n"
                "2. The page structure has changed\n"
                "3. Authentication or cookies may be required\n"
                "4. The API endpoint format has changed\n\n"
                f"{selenium_note}"
                "The scraper will attempt to use Selenium if available to execute JavaScript."
            )
            raise ValueError(error_msg)
        
        # Set default date if not found
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            "words": words[:16],  # Ensure exactly 16 words
            "date": date,
            "puzzle_id": puzzle_id
        }
        
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch page: {str(e)}")
    except Exception as e:
        raise Exception(f"Scraping error: {str(e)}")


def _scrape_with_selenium(url: str) -> tuple[List[str], Optional[str], Optional[int]]:
    """
    Use Selenium to load the page, execute JavaScript, and extract puzzle data.
    
    Args:
        url: URL to scrape
        
    Returns:
        Tuple of (words list, date string, puzzle_id int)
    """
    words = []
    date = None
    puzzle_id = None
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Enable performance logging to capture network requests
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = None
    try:
        print("Initializing Chrome driver...")
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"Loading page: {url}")
        # Load the page
        driver.get(url)
        print("Page loaded, waiting for JavaScript to execute...")
        
        # Monitor network requests to find API calls
        print("Monitoring network requests for puzzle data...")
        time.sleep(5)  # Wait for network requests to complete
        
        # Check performance logs for API responses
        try:
            logs = driver.get_log('performance')
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response_url = message['message']['params']['response']['url']
                    if 'connections' in response_url.lower() or 'puzzle' in response_url.lower() or 'game' in response_url.lower():
                        if 'json' in response_url or 'api' in response_url or 'svc' in response_url:
                            print(f"Found potential API endpoint: {response_url}")
                            try:
                                # Try to get the response body
                                request_id = message['message']['params']['requestId']
                                response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                if response_body and 'body' in response_body:
                                    api_data = json.loads(response_body['body'])
                                    extracted_words, extracted_date, extracted_id = _extract_from_game_data(api_data)
                                    if extracted_words and len(extracted_words) >= 16:
                                        print(f"Found {len(extracted_words)} words from API response!")
                                        return extracted_words, extracted_date, extracted_id
                            except Exception as e:
                                print(f"Could not extract from API response: {str(e)}")
                                # Try fetching the URL directly
                                try:
                                    api_response = requests.get(response_url, timeout=5)
                                    if api_response.status_code == 200:
                                        api_data = api_response.json()
                                        extracted_words, extracted_date, extracted_id = _extract_from_game_data(api_data)
                                        if extracted_words and len(extracted_words) >= 16:
                                            print(f"Found {len(extracted_words)} words from direct API call!")
                                            return extracted_words, extracted_date, extracted_id
                                except Exception:
                                    pass
        except Exception as e:
            print(f"Error monitoring network requests: {str(e)}")
        
        # Wait for the page to load and JavaScript to execute
        wait = WebDriverWait(driver, 20)
        
        # Wait a bit for JavaScript to execute
        time.sleep(3)
        
        # Try multiple strategies to get the data:
        # 1. Check window.gameData - wait for it to be populated
        print("Checking window.gameData...")
        try:
            # Wait for gameData to be defined and not undefined
            game_data = wait.until(lambda d: d.execute_script("return window.gameData && window.gameData !== undefined && typeof window.gameData === 'object' ? window.gameData : null;"))
            if game_data:
                print(f"Found gameData: {type(game_data)}")
                words, date, puzzle_id = _extract_from_game_data(game_data)
                if words and len(words) >= 16:
                    print(f"Successfully extracted {len(words)} words from gameData")
                    return words, date, puzzle_id
                else:
                    print(f"Extracted {len(words)} words from gameData (need 16)")
        except (TimeoutException, Exception) as e:
            print(f"Timeout waiting for gameData: {str(e)}")
            # Try direct access without waiting
            try:
                game_data = driver.execute_script("return window.gameData;")
                print(f"Direct gameData check: {game_data}")
                if game_data and game_data != 'undefined' and game_data is not None:
                    words, date, puzzle_id = _extract_from_game_data(game_data)
                    if words and len(words) >= 16:
                        return words, date, puzzle_id
            except Exception as ex:
                print(f"Error accessing gameData directly: {str(ex)}")
                pass
        
        # 2. Try to get data from React component state or other JS variables
        try:
            # Check for React component data
            react_data = driver.execute_script("""
                // Try to find React component data
                if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                    return window.__REACT_DEVTOOLS_GLOBAL_HOOK__.renderers;
                }
                return null;
            """)
        except Exception:
            pass
        
        # 3. Wait for puzzle tiles/words to appear in the DOM
        print("Searching for word elements in DOM...")
        try:
            # Wait longer for React to render the puzzle
            print("Waiting for puzzle to render...")
            time.sleep(5)
            
            # Try to wait for the game container to be ready
            try:
                wait.until(EC.presence_of_element_located((By.ID, "pz-game-root")))
                time.sleep(2)  # Additional wait for content to populate
            except TimeoutException:
                print("Game root not found, continuing anyway...")
            
            # Try multiple selectors for word elements
            selectors = [
                "[data-word]",
                "[data-tile]",
                "[data-card]",
                "button[class*='word']",
                "button[class*='tile']",
                "div[class*='word']",
                "div[class*='tile']",
                "[class*='word']",
                "[class*='tile']",
                "[class*='card']",
            ]
            
            for selector in selectors:
                try:
                    word_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"Selector '{selector}' found {len(word_elements)} elements")
                    
                    for i, elem in enumerate(word_elements):
                        try:
                            # Try multiple ways to get the text
                            text = None
                            
                            # First try data attributes
                            text = (
                                elem.get_attribute('data-word') or
                                elem.get_attribute('data-tile') or
                                elem.get_attribute('data-card') or
                                elem.get_attribute('data-text') or
                                elem.get_attribute('aria-label')
                            )
                            
                            # If no data attribute, try text content
                            if not text or not text.strip():
                                text = elem.text
                            
                            # Also try innerHTML if text is empty
                            if not text or not text.strip():
                                text = elem.get_attribute('innerHTML')
                                # Clean HTML tags if present
                                if text:
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(text, 'html.parser')
                                    text = soup.get_text()
                            
                            text = text.strip() if text else ""
                            
                            # Debug: print first few elements
                            if i < 3:
                                print(f"  Element {i}: text='{text}', tag={elem.tag_name}, class={elem.get_attribute('class')}")
                            
                            # Validate it's a single word
                            if text and len(text) > 0:
                                # Check if it's a single word (no spaces, reasonable length)
                                if len(text.split()) == 1 and 2 <= len(text) <= 30 and text not in words:
                                    words.append(text)
                                    print(f"  Added word: '{text}' (total: {len(words)})")
                                    if len(words) >= 16:
                                        print(f"Found 16 words from DOM elements")
                                        break
                        except Exception as e:
                            print(f"  Error extracting text from element {i}: {str(e)}")
                            continue
                    
                    if len(words) >= 16:
                        break
                except Exception as e:
                    print(f"Error with selector '{selector}': {str(e)}")
                    continue
            
            print(f"Total words found from DOM: {len(words)}")
            
            # If we still don't have enough words, try to get all text from the game root
            if len(words) < 16:
                print("Trying to extract from game root container...")
                try:
                    game_root = driver.find_element(By.ID, "pz-game-root")
                    all_text = game_root.text
                    print(f"Game root text length: {len(all_text)}")
                    # Split by whitespace and look for potential words
                    potential_words = [w.strip() for w in all_text.split() if 2 <= len(w.strip()) <= 30]
                    for word in potential_words:
                        if word not in words and word.isalpha():
                            words.append(word)
                            if len(words) >= 16:
                                break
                    print(f"After game root extraction: {len(words)} words")
                except Exception as e:
                    print(f"Error extracting from game root: {str(e)}")
                    
        except Exception as e:
            print(f"Error searching DOM: {str(e)}")
            import traceback
            traceback.print_exc()
            pass
        
        # 4. Try to extract from any JavaScript variables
        try:
            # Check for various possible data structures
            scripts_to_check = [
                "return window.gameData;",
                "return window.puzzleData;",
                "return window.connectionsData;",
                "return window.__NEXT_DATA__;",
                "return window.connectionsArchiveDate;",
                # Try to get from React state
                "return document.querySelector('#pz-game-root')?.__reactInternalInstance || null;",
            ]
            
            for script in scripts_to_check:
                try:
                    data = driver.execute_script(script)
                    if data and data != 'undefined' and data is not None:
                        extracted_words, extracted_date, extracted_id = _extract_from_game_data(data)
                        if extracted_words and len(extracted_words) >= 16:
                            words = extracted_words
                            date = extracted_date or date
                            puzzle_id = extracted_id or puzzle_id
                            break
                except Exception:
                    continue
        except Exception:
            pass
        
        # 5. Try to intercept network requests or check localStorage/sessionStorage
        try:
            # Check localStorage and sessionStorage
            local_data = driver.execute_script("return JSON.stringify(localStorage);")
            session_data = driver.execute_script("return JSON.stringify(sessionStorage);")
            
            for storage_data in [local_data, session_data]:
                if storage_data:
                    try:
                        parsed = json.loads(storage_data)
                        for key, value in parsed.items():
                            if 'game' in key.lower() or 'puzzle' in key.lower() or 'connections' in key.lower():
                                try:
                                    value_parsed = json.loads(value) if isinstance(value, str) else value
                                    extracted_words, extracted_date, extracted_id = _extract_from_game_data(value_parsed)
                                    if extracted_words and len(extracted_words) >= 16:
                                        words = extracted_words
                                        date = extracted_date or date
                                        puzzle_id = extracted_id or puzzle_id
                                        break
                                except Exception:
                                    continue
                        if words and len(words) >= 16:
                            break
                    except Exception:
                        pass
        except Exception:
            pass
        
        # 4. Try to get data from the page source after JavaScript execution
        if not words:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for data in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_content = script.string
                if not script_content:
                    continue
                
                # Look for JSON data
                if 'gameData' in script_content or 'words' in script_content:
                    # Try to extract JSON
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script_content, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(0))
                            words, date, puzzle_id = _extract_from_game_data(parsed)
                            if words and len(words) >= 16:
                                break
                        except Exception:
                            continue
        
    except Exception as e:
        raise Exception(f"Selenium scraping failed: {str(e)}")
    finally:
        if driver:
            driver.quit()
    
    return words, date, puzzle_id


def _find_game_data_recursive(obj: Any, depth: int = 0, max_depth: int = 10) -> Optional[Dict]:
    """
    Recursively search through a nested structure to find game data.
    
    Args:
        obj: Object to search through
        depth: Current recursion depth
        max_depth: Maximum recursion depth
        
    Returns:
        Dictionary containing game data if found, None otherwise
    """
    if depth > max_depth:
        return None
    
    if isinstance(obj, dict):
        # Check if this dict looks like game data
        keys = obj.keys()
        game_indicators = ['words', 'tiles', 'cards', 'answers', 'groups', 'puzzle', 'game', 'connections']
        if any(key.lower() in game_indicators for key in keys):
            # Check if it has words or similar data
            if any(key in obj for key in ['words', 'tiles', 'cards', 'answers']):
                return obj
        
        # Recursively search values
        for value in obj.values():
            result = _find_game_data_recursive(value, depth + 1, max_depth)
            if result:
                return result
                
    elif isinstance(obj, list):
        # Check if list contains game data structures
        for item in obj:
            result = _find_game_data_recursive(item, depth + 1, max_depth)
            if result:
                return result
    
    return None


def _extract_from_game_data(game_data: Any) -> tuple[List[str], Optional[str], Optional[int]]:
    """
    Helper function to extract words, date, and puzzle_id from game data structure.
    
    Args:
        game_data: Dictionary containing game data
        
    Returns:
        Tuple of (words list, date string, puzzle_id int)
    """
    words = []
    date = None
    puzzle_id = None
    
    # Try various possible data structures
    # Common patterns in game data:
    
    # Pattern 1: Direct words array
    if isinstance(game_data, dict):
        # Look for words in various keys
        words = (
            game_data.get('words') or
            game_data.get('tiles') or
            game_data.get('cards') or
            game_data.get('items') or
            game_data.get('answers') or
            []
        )
        
        # If words is a list of objects, extract text
        if words and isinstance(words[0], dict):
            words = [item.get('text') or item.get('word') or item.get('label') or str(item) 
                    for item in words if item]
        
        # Extract date
        date = (
            game_data.get('date') or
            game_data.get('puzzleDate') or
            game_data.get('publishedDate') or
            game_data.get('gameDate')
        )
        
        # Extract puzzle_id
        puzzle_id = (
            game_data.get('id') or
            game_data.get('puzzleId') or
            game_data.get('puzzle_id') or
            game_data.get('gameId')
        )
        
        # If date is a timestamp, convert it
        if date and isinstance(date, (int, float)):
            try:
                date = datetime.fromtimestamp(date / 1000).strftime('%Y-%m-%d')
            except (ValueError, OSError):
                pass
        
        # Pattern 2: Nested structure (e.g., gameData.answers or gameData.groups)
        if not words:
            answers = game_data.get('answers') or game_data.get('groups') or []
            if answers:
                for group in answers:
                    if isinstance(group, list):
                        words.extend([str(item) for item in group if item])
                    elif isinstance(group, dict):
                        group_words = group.get('words') or group.get('items') or group.get('members') or []
                        words.extend([str(w) for w in group_words if w])
        
        # Pattern 3: Look for nested data structures
        if not words:
            # Try common nested patterns
            for key in ['data', 'puzzle', 'game', 'connections', 'board', 'grid']:
                nested = game_data.get(key)
                if nested and isinstance(nested, dict):
                    nested_words, nested_date, nested_id = _extract_from_game_data(nested)
                    if nested_words:
                        words = nested_words
                        date = nested_date or date
                        puzzle_id = nested_id or puzzle_id
                        break
        
        # Pattern 4: Look for flat structure with all words in one array
        if not words:
            # Sometimes words are stored as a flat list in the root
            all_values = []
            for key, value in game_data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Check if this list might contain words
                    if all(isinstance(item, str) and len(item.split()) == 1 for item in value[:5]):
                        all_values.extend(value)
            if len(all_values) >= 16:
                words = all_values[:16]
    
    elif isinstance(game_data, list):
        # If game_data is directly a list
        words = [str(item) for item in game_data if item]
        # Check if it's a list of lists (groups)
        if words and isinstance(words[0], list):
            # Flatten the list of lists
            words = [str(item) for sublist in words for item in sublist if item]
    
    # Clean and validate words
    words = [w.strip() for w in words if w and isinstance(w, str) and w.strip() and len(w) > 0]
    # Remove duplicates while preserving order
    seen = set()
    words = [w for w in words if not (w in seen or seen.add(w))]
    
    return words, date, puzzle_id


def debug_page_structure(save_html: bool = False) -> None:
    """
    Debug function to inspect the page structure and help identify where data might be.
    
    Args:
        save_html: If True, save the HTML to a file for inspection
    """
    url = "https://www.nytimes.com/games/connections"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("=== Page Structure Debug ===")
    print(f"Response status: {response.status_code}")
    print(f"Response length: {len(response.text)} characters")
    print(f"\nNumber of script tags: {len(soup.find_all('script'))}")
    
    # Check for __NEXT_DATA__
    has_next_data = '__NEXT_DATA__' in response.text
    print(f"Contains __NEXT_DATA__: {has_next_data}")
    
    # Look for API endpoints
    api_patterns = re.findall(r'["\']([^"\']*(?:api|svc|games)[^"\']*connections[^"\']*)["\']', response.text, re.I)
    print(f"\nFound {len(api_patterns)} potential API endpoints:")
    for endpoint in api_patterns[:10]:
        print(f"  - {endpoint}")
    
    # Check for common data patterns
    patterns_to_check = [
        ('"words"', 'words key'),
        ('"tiles"', 'tiles key'),
        ('"cards"', 'cards key'),
        ('"answers"', 'answers key'),
        ('"groups"', 'groups key'),
        ('gameData', 'gameData variable'),
        ('puzzleData', 'puzzleData variable'),
    ]
    
    print("\nPattern matches in response:")
    for pattern, name in patterns_to_check:
        count = response.text.count(pattern)
        print(f"  {name}: {count} occurrences")
    
    if save_html:
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nHTML saved to debug_page.html")


if __name__ == "__main__":
    """Test the scraper"""
    import sys
    
    # Add debug mode
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        debug_page_structure(save_html=True)
    else:
        try:
            result = scrape_nyt_connections()
            print("Scraping successful!")
            print(f"Date: {result['date']}")
            print(f"Puzzle ID: {result['puzzle_id']}")
            print(f"Words ({len(result['words'])}):")
            for i, word in enumerate(result['words'], 1):
                print(f"  {i}. {word}")
        except Exception as e:
            print(f"Error: {e}")
            print("\nTip: Run with '--debug' flag to inspect page structure:")
            print("  python python/scraper.py --debug")

