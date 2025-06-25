import requests
import json
import time
from datetime import datetime

class CoomerApiClient:
    """
    Client to interact with Coomer and Kemono APIs to get the creators list.
    Includes retry logic and error handling.
    """
    
    # API URLs
    COOMER_API_URL = 'https://coomer.party/api/v1/creators'
    KEMONO_API_URL = 'https://kemono.su/api/v1/creators'
    
    # Fallback URLs if main ones fail
    COOMER_API_URL_FALLBACK = 'https://coomer.su/api/v1/creators'
    KEMONO_API_URL_FALLBACK = 'https://kemono.su/api/v1/creators'
    
    MAX_RETRIES = 5 # Maximum number of attempts if request fails
    RETRY_DELAY = 10 # Seconds to wait between retries
    TIMEOUT = 60     # Seconds to wait for HTTP request

    def __init__(self):
        pass

    def get_all_creators(self, platform='coomer'):
        """
        Attempts to get the complete list of creators from the specified API.
        
        Args:
            platform (str): 'coomer' or 'kemono' to select the platform
        
        Returns:
            list: A list of creator objects if the request was successful.
            None: If the request fails after all retries.
        """
        # Determine base URL based on platform
        if platform.lower() == 'kemono':
            primary_url = self.KEMONO_API_URL
            fallback_url = self.KEMONO_API_URL_FALLBACK
            platform_name = "Kemono"
        else:  # coomer by default
            primary_url = self.COOMER_API_URL
            fallback_url = self.COOMER_API_URL_FALLBACK
            platform_name = "Coomer"
        
        for attempt in range(self.MAX_RETRIES):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Attempt {attempt + 1}/{self.MAX_RETRIES}: Downloading creators list from {platform_name} ({primary_url})")
            try:
                # Try with primary URL
                response = requests.get(primary_url, headers={'accept': 'application/json'}, timeout=self.TIMEOUT)
                response.raise_for_status() # Raises exception if HTTP status is an error (4xx or 5xx)

                creators_data = response.json()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successful download from {platform_name}. Creators found: {len(creators_data)}")
                return creators_data
                
            except requests.exceptions.Timeout:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Timeout error connecting to {primary_url}.")
            except requests.exceptions.ConnectionError as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connection error with {primary_url}: {e}.")
                # Try with fallback URL if different
                if fallback_url != primary_url:
                    try:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Trying with fallback URL: {fallback_url}")
                        response = requests.get(fallback_url, headers={'accept': 'application/json'}, timeout=self.TIMEOUT)
                        response.raise_for_status()
                        creators_data = response.json()
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successful download using fallback. Creators found: {len(creators_data)}")
                        return creators_data
                    except Exception as fallback_error:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fallback also failed: {fallback_error}")
            except requests.exceptions.HTTPError as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HTTP Error: {e}. Status code: {response.status_code}.")
            except json.JSONDecodeError:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error decoding JSON response. Content is not valid JSON.")
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unexpected error during download: {e}.")
            
            if attempt < self.MAX_RETRIES - 1:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Retrying in {self.RETRY_DELAY} seconds...")
                time.sleep(self.RETRY_DELAY)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FAILURE: Could not get creators list from {platform_name} after {self.MAX_RETRIES} attempts.")
        return None

# Usage example (only for testing the module directly)
if __name__ == '__main__':
    client = CoomerApiClient()
    
    # Test with Coomer
    print("Testing with Coomer...")
    creators_coomer = client.get_all_creators('coomer')
    if creators_coomer:
        print(f"Retrieved {len(creators_coomer)} creators from Coomer.")
    
    # Test with Kemono
    print("\nTesting with Kemono...")
    creators_kemono = client.get_all_creators('kemono')
    if creators_kemono:
        print(f"Retrieved {len(creators_kemono)} creators from Kemono.")