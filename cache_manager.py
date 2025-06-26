import json
import os
from datetime import datetime, timedelta
import logging
import threading

# Configuración de cache
class CacheConfig:
    CACHE_FILE = 'tests/test_cache.json'
    CACHE_LIFESPAN_HOURS = 24
    CACHE_LIFESPAN_SECONDS = CACHE_LIFESPAN_HOURS * 3600

# Diccionarios para cache
creators_cache = {}
cache_last_updated = {}
cache_status_message = {}

# Lock para operaciones de cache
cache_lock = threading.Lock()

# Logger específico para el cache
cache_logger = logging.getLogger('coomer_scraper.cache')

def load_cache_from_file():
    """Attempts to load creators cache from local file."""
    global creators_cache, cache_last_updated, cache_status_message

    # Clear existing cache
    creators_cache.clear()
    cache_last_updated.clear()
    cache_status_message.clear()

    if os.path.exists(CacheConfig.CACHE_FILE):
        try:
            with open(CacheConfig.CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if format is new (dictionary) or old (list)
                if isinstance(data, dict):
                    creators_cache.update(data.get('creators', {}))
                    last_updated_data = data.get('last_updated', {})
                else:
                    # Old format (list) - migrate to new format (dictionary)
                    cache_logger.info("Migrating cache from old format (list) to new format (dictionary)")
                    creators_cache.update({'coomer': data if isinstance(data, list) else []})
                    last_updated_data = {}
                
                # Convert timestamps from string to datetime
                cache_last_updated.update({
                    platform: datetime.fromisoformat(timestamp_str) if timestamp_str else None
                    for platform, timestamp_str in last_updated_data.items()
                })
                
                # Initialize status messages
                cache_status_message.update({
                    platform: f"Loaded {len(creators_cache.get(platform, []))} creators from file."
                    if platform in creators_cache else "Cache not found on disk."
                    for platform in ['coomer', 'kemono']
                })
                
                cache_logger.info(f"Cache loaded from '{CacheConfig.CACHE_FILE}' with {sum(len(creators) for creators in creators_cache.values())} total elements.")
                return True
        except json.JSONDecodeError as e:
            cache_logger.error(f"Error reading cache JSON file '{CacheConfig.CACHE_FILE}': {e}")
            cache_status_message = {"coomer": "Error loading cache from file.", "kemono": "Error loading cache from file."}
            return False
        except Exception as e:
            cache_logger.error(f"Unexpected error loading cache from '{CacheConfig.CACHE_FILE}': {e}")
            cache_status_message = {"coomer": "Unexpected error loading cache.", "kemono": "Unexpected error loading cache."}
            return False
    else:
        cache_logger.info(f"Cache file '{CacheConfig.CACHE_FILE}' not found.")
        cache_status_message = {"coomer": "Cache not found on disk.", "kemono": "Cache not found on disk."}
        return False

def save_cache_to_file():
    """Saves current creators cache to local file."""
    global creators_cache, cache_last_updated
    try:
        cache_logger.debug(f"Saving cache. Current state: creators={len(creators_cache)}, last_updated={cache_last_updated}")
        
        # Convert timestamps to strings for JSON
        last_updated_str = {}
        for platform, timestamp_str in cache_last_updated.items():
            # If it's already a string, keep it as is
            if isinstance(timestamp_str, str):
                last_updated_str[platform] = timestamp_str
            # If it's None, keep it as None
            elif timestamp_str is None:
                last_updated_str[platform] = None
            # If it's a datetime, convert to string
            else:
                last_updated_str[platform] = timestamp_str.isoformat()
        
        data = {
            'creators': creators_cache,
            'last_updated': last_updated_str
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(CacheConfig.CACHE_FILE), exist_ok=True)
        
        with open(CacheConfig.CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            cache_logger.debug(f"Cache data written to file: {data}")
        
        cache_logger.info(f"Cache saved to '{CacheConfig.CACHE_FILE}'.")
        return True
    except Exception as e:
        cache_logger.error(f"Error saving cache to '{CacheConfig.CACHE_FILE}': {e}")
        return False

def update_creators_cache_in_background(api_client=None, force_update=False, platform=None):
    """
    Downloads latest creators list in background.
    Uses lock to avoid concurrent updates.
    """
    global creators_cache, cache_last_updated, cache_status_message
    
    def update_platform(platform_name):
        """Updates cache for a specific platform"""
        try:
            # Try to acquire lock
            if not cache_lock.acquire(blocking=False):
                cache_logger.info(f"Background update attempt for {platform_name}: cache lock already in use. Skipping this execution.")
                return
                
            try:
                # Check if cache is expired or if we're forcing update
                if force_update or (platform_name in cache_last_updated and 
                    (datetime.now() - cache_last_updated[platform_name]).total_seconds() > CacheConfig.CACHE_LIFESPAN_SECONDS):
                    
                    # Download new creators list
                    if api_client:
                        downloaded_creators = api_client.get_all_creators(platform_name) # Call API client
                        if downloaded_creators is not None:
                            # Update cache
                            creators_cache[platform_name] = downloaded_creators
                            cache_last_updated[platform_name] = datetime.now()
                            cache_status_message[platform_name] = f"Updated {len(downloaded_creators)} creators from API."
                            cache_logger.info(f"Creators cache for {platform_name} updated successfully.")
                            save_cache_to_file()
                        else:
                            cache_logger.error(f"Failed to download creators for {platform_name}")
                            cache_status_message[platform_name] = f"Failed to download creators for {platform_name}"
                    else:
                        cache_logger.error(f"API client not initialized for {platform_name}")
                        cache_status_message[platform_name] = f"API client not initialized"
                else:
                    cache_logger.info(f"Creators cache for {platform_name} updated less than {CacheConfig.CACHE_LIFESPAN_HOURS} hours ago. No download required.")
                    cache_status_message[platform_name] = f"Cache updated less than {CacheConfig.CACHE_LIFESPAN_HOURS} hours ago. No download required."
            finally:
                cache_lock.release()
        except Exception as e:
            cache_logger.error(f"Error updating cache for {platform_name}: {e}")
            cache_status_message[platform_name] = f"Error updating cache: {str(e)}"
    
    # Start thread for each platform if no specific platform is specified
    if platform is None:
        for platform_name in ['coomer', 'kemono']:
            threading.Thread(target=update_platform, args=(platform_name,), daemon=True).start()
    else:
        # Start thread for specific platform
        threading.Thread(target=update_platform, args=(platform,), daemon=True).start()

def clear_cache():
    """Limpia completamente el estado del cache"""
    global creators_cache, cache_last_updated, cache_status_message
    creators_cache.clear()
    cache_last_updated.clear()
    cache_status_message.clear()
    cache_logger.info("Cache cleared")
