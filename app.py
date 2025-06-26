from flask import Flask, render_template, request, jsonify
import subprocess
import os
import threading
import uuid
import re 
import signal
import time 
import json # New: for handling creators cache
from datetime import datetime, timedelta # New: for cache logic
import logging # Already was, but mentioned for its use in cache
import logging.handlers

# Import the API client for Coomer/Kemono. Make sure this file exists in the same folder.
from coomer_api_client import CoomerApiClient
from cache_manager import (
    load_cache_from_file,
    save_cache_to_file,
    update_creators_cache_in_background,
    clear_cache
)

# Configuración de logging
LOG_FILE = 'logs/app.log'
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 3

# Configuración completa de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

# Logger principal
logger = logging.getLogger('coomer_scraper')
logger.setLevel(logging.INFO)

# Logger específico para la API
api_logger = logging.getLogger('coomer_scraper.api')
api_logger.setLevel(logging.INFO)

# Logger específico para las tareas de scraping
scrape_logger = logging.getLogger('coomer_scraper.scrape')
scrape_logger.setLevel(logging.INFO)

# Asegurarse que la carpeta de logs exista
os.makedirs('logs', exist_ok=True)

# Configuración de logging para Flask
app = Flask(__name__)
app.logger.name = 'coomer_scraper.flask'
app.logger.setLevel(logging.INFO)

# Configuración de logging para el API client
api_client = CoomerApiClient()
api_client.logger = api_logger

# Dictionary to store scraping task status
scrape_tasks = {}

# Inicializar la aplicación solo si se está ejecutando directamente
if __name__ == '__main__':
    # Cargar cache
    load_cache_from_file()
    # Iniciar actualización en background
    threading.Thread(target=update_creators_cache_in_background).start()

# Endpoint de health
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'cache_status': cache_status_message
    })

# =========================================================
# NEW: Cache Logic for Creators List (from search functionality)
# =========================================================
api_client = CoomerApiClient() # API client instance to get creators

CACHE_FILE = 'creators_cache.json' # File to save cache
creators_cache = {} # Dictionary to store creators by platform
cache_last_updated = {} # Last update date/time by platform
cache_status_message = {} # Status message by platform
cache_lock = threading.Lock() # Lock to protect shared cache access

CACHE_LIFESPAN_HOURS = 24 # Cache lifetime before attempting new download

# --- Cache Functions ---

def load_cache_from_file():
    """Attempts to load creators cache from local file."""
    global creators_cache, cache_last_updated, cache_status_message

    # Ensure creators_cache is always a dictionary
    if not isinstance(creators_cache, dict):
        creators_cache = {}

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if format is new (dictionary) or old (list)
                if isinstance(data, dict):
                    creators_cache = data.get('creators', {})
                    last_updated_data = data.get('last_updated', {})
                else:
                    # Old format (list) - migrate to new format
                    logging.info("Migrating cache from old format (list) to new format (dictionary)")
                    creators_cache = {'coomer': data if isinstance(data, list) else []}
                    last_updated_data = {}
                
                # Convert timestamps from string to datetime
                cache_last_updated = {}
                for platform, timestamp_str in last_updated_data.items():
                    if timestamp_str:
                        cache_last_updated[platform] = datetime.fromisoformat(timestamp_str)
                    else:
                        cache_last_updated[platform] = None
                
                # Initialize status messages
                cache_status_message = {}
                for platform in ['coomer', 'kemono']:
                    if platform in creators_cache:
                        count = len(creators_cache[platform])
                        cache_status_message[platform] = f"Loaded {count} creators from file."
                    else:
                        cache_status_message[platform] = "Cache not found on disk."
                
                logging.info(f"Cache loaded from '{CACHE_FILE}' with {sum(len(creators) for creators in creators_cache.values())} total elements.")
                return True
        except json.JSONDecodeError as e:
            logging.error(f"Error reading cache JSON file '{CACHE_FILE}': {e}")
            cache_status_message = {"coomer": "Error loading cache from file.", "kemono": "Error loading cache from file."}
            return False
        except Exception as e:
            logging.error(f"Unexpected error loading cache from '{CACHE_FILE}': {e}")
            cache_status_message = {"coomer": "Unexpected error loading cache.", "kemono": "Unexpected error loading cache."}
            return False
    else:
        logging.info(f"Cache file '{CACHE_FILE}' not found.")
        cache_status_message = {"coomer": "Cache not found on disk.", "kemono": "Cache not found on disk."}
        return False

def save_cache_to_file():
    """Saves current creators cache to local file."""
    global creators_cache, cache_last_updated
    try:
        # Convert datetime to string for JSON
        last_updated_str = {}
        for platform, timestamp in cache_last_updated.items():
            last_updated_str[platform] = timestamp.isoformat() if timestamp else None
        
        data = {
            'creators': creators_cache,
            'last_updated': last_updated_str
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Cache saved to '{CACHE_FILE}'.")
    except Exception as e:
        logging.error(f"Error saving cache to '{CACHE_FILE}': {e}")

def update_creators_cache_in_background(force_update=False, platform=None):
    """
    Downloads latest creators list in background.
    Uses lock to avoid concurrent updates.
    """
    global creators_cache, cache_last_updated, cache_status_message

    if not cache_lock.acquire(blocking=False): # Try to acquire lock without waiting
        logging.info("Background update attempt: cache lock already in use. Skipping this execution.")
        return # If lock is already in use, another update is already in progress

    try:
        # If no platform specified, update both
        platforms_to_update = [platform] if platform else ['coomer', 'kemono']
        
        for platform_name in platforms_to_update:
            current_time = datetime.now()
            # If not forced update and cache hasn't expired, do nothing
            if not force_update and platform_name in cache_last_updated and cache_last_updated[platform_name] and (current_time - cache_last_updated[platform_name]) < timedelta(hours=CACHE_LIFESPAN_HOURS):
                logging.info(f"Creators cache for {platform_name} updated less than 24 hours ago. No download required.")
                if platform_name not in cache_status_message:
                    cache_status_message[platform_name] = f"Loaded {len(creators_cache.get(platform_name, []))} creators (recent)."
                continue # Skip this platform

            logging.info(f"Attempting to download latest creators list from {platform_name} API...")
            cache_status_message[platform_name] = f"Downloading creators list from {platform_name}..." # Update visible status for frontend

            downloaded_creators = api_client.get_all_creators(platform_name) # Call API client

            if downloaded_creators:
                if platform_name not in creators_cache:
                    creators_cache[platform_name] = []
                creators_cache[platform_name] = downloaded_creators
                if platform_name not in cache_last_updated:
                    cache_last_updated[platform_name] = None
                cache_last_updated[platform_name] = datetime.now()
                save_cache_to_file() # Save updated cache to disk
                cache_status_message[platform_name] = f"Loaded {len(creators_cache[platform_name])} creators from {platform_name} (updated)."
                logging.info(f"Successful download from {platform_name}. Creators found: {len(creators_cache[platform_name])}")
            else:
                cache_status_message[platform_name] = f"Failed to download from {platform_name}. Keeping previous cache ({len(creators_cache.get(platform_name, []))} creators) if exists."
                logging.error(f"Failed to download creators from {platform_name}. Cache was not updated.")
    finally:
        cache_lock.release() # Ensure lock is always released

# Global API client instance
api_client = None

def initialize_app_on_startup():
    """Runs once when starting the application to load and update creators cache."""
    global cache_status_message, api_client
    
    # 1. Try to load cache from local file
    if load_cache_from_file():
        for platform in ['coomer', 'kemono']:
            if platform not in cache_status_message:
                cache_status_message[platform] = f"Loaded {len(creators_cache.get(platform, []))} creators from file."
    else:
        cache_status_message = {"coomer": "Empty cache. Starting background download.", "kemono": "Empty cache. Starting background download."}

    # 2. Initialize API client if not already initialized
    if api_client is None:
        api_client = CoomerApiClient()

    # 3. Start background update thread for both platforms
    thread = threading.Thread(target=update_creators_cache_in_background, args=(api_client,), daemon=True)
    thread.start()

# Inicializar la aplicación solo si se está ejecutando directamente
if __name__ == '__main__':
    # Initialize logging
    logger.setLevel(logging.INFO)
    api_logger.setLevel(logging.INFO)
    scrape_logger.setLevel(logging.INFO)
    
    # Initialize Flask app
    app = Flask(__name__)
    app.logger.name = 'coomer_scraper.flask'
    
    # Initialize the application
    initialize_app_on_startup()
    
    # Initialize cache
    initialize_app_on_startup()

# =========================================================
# FIN: Cache Logic for Creators List (from search functionality)
# =========================================================


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    # Validar datos requeridos
    required_fields = ['username', 'domain', 'service']
    if not all(request.form.get(field) for field in required_fields):
        return jsonify({
            "status": "error",
            "message": "Missing required fields: username, domain, and service"
        }), 400

    # Obtener datos del formulario
    username = request.form.get('username')
    domain = request.form.get('domain')
    service = request.form.get('service')
    
    # Construir URL
    final_url = f"https://{domain}/{service}/user/{username}"

    # Obtener opciones adicionales
    output_dir = request.form.get('output_dir', './mi_descarga')
    sub_folders = request.form.get('sub_folders') == 'on'
    skip_vids = request.form.get('skip_vids') == 'on'
    skip_imgs = request.form.get('skip_imgs') == 'on'
    full_hash = request.form.get('full_hash') == 'on'
    offset_start = request.form.get('offset_start')
    offset_end = request.form.get('offset_end')
    
    try:
        offset_start = int(offset_start) if offset_start else None
        offset_end = int(offset_end) if offset_end else None
    except ValueError:
        return jsonify({"status": "error", "message": "Offsets must be valid numbers."}), 400

    task_id = str(uuid.uuid4())
    
    scrape_tasks[task_id] = {
        'status': 'running',
        'message': f'Scraping {final_url} started in background...',
        'process': None, 
        'progress_info': 'Starting...',
        'final_download_count': 0 
    }

    command = ['python', 'scrape.py', final_url] 
    command.extend(['--out', output_dir])

    if sub_folders:
        command.append('--sub-folders')
    if skip_vids:
        command.append('--skip-vids')
    if skip_imgs:
        command.append('--skip-imgs')
    if full_hash:
        command.append('--full-hash')
    
    if offset_start is not None:
        command.extend(['--offset-start', str(offset_start)])
    if offset_end is not None:
        command.extend(['--offset-end', str(offset_end)])

    # --- NEW FUNCTIONS FOR READING STDOUT/STDERR IN SEPARATE THREADS ---
    def _read_stdout(pipe, buffer_list, task_id_arg, progress_regex):
        """Reads stdout and updates progress in task dictionary."""
        for line in iter(pipe.readline, ''): 
            buffer_list.append(line)
            match_progress = progress_regex.search(line)
            if match_progress:
                downloaded_count = int(match_progress.group(1)) 
                total_count = int(match_progress.group(2)) 
                if task_id_arg in scrape_tasks:
                    scrape_tasks[task_id_arg]['progress_info'] = f"Downloading: {downloaded_count} of {total_count} files"
                    scrape_tasks[task_id_arg]['message'] = scrape_tasks[task_id_arg]['progress_info']
                    scrape_tasks[task_id_arg]['final_download_count'] = downloaded_count 

    def _read_stderr(pipe, buffer_list, task_id_arg):
        """Reads stderr and adds to buffer."""
        for line in iter(pipe.readline, ''): 
            buffer_list.append(line)
    # --- END NEW FUNCTIONS ---

    def run_scraper_in_thread(cmd, task_id_arg):
        process = None
        full_stdout_accumulated = [] 
        full_stderr_accumulated = [] 
        
        progress_regex = re.compile(r'Successfully downloaded media from (\d+)/(\d+) URLs to')
        final_count_regex = re.compile(r'\[main\] INFO: Successfully downloaded \((\d+)\) additional media.') 

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
            
            if task_id_arg in scrape_tasks:
                scrape_tasks[task_id_arg]['process'] = process
            
            stdout_reader_thread = threading.Thread(target=_read_stdout, args=(process.stdout, full_stdout_accumulated, task_id_arg, progress_regex))
            stderr_reader_thread = threading.Thread(target=_read_stderr, args=(process.stderr, full_stderr_accumulated, task_id_arg))
            
            stdout_reader_thread.daemon = True 
            stderr_reader_thread.daemon = True
            
            stdout_reader_thread.start()
            stderr_reader_thread.start()

            process.wait()

            stdout_reader_thread.join(timeout=5) 
            stderr_reader_thread.join(timeout=5)
            
            final_stdout = "".join(full_stdout_accumulated)
            final_stderr = "".join(full_stderr_accumulated)

            match_final_count = final_count_regex.search(final_stdout) 

            download_count_from_regex = 0
            if match_final_count:
                download_count_from_regex = int(match_final_count.group(1)) 

            if task_id_arg in scrape_tasks:
                scrape_tasks[task_id_arg]['process'] = None 

            if process.returncode == 0: 
                if task_id_arg in scrape_tasks:
                    final_count_to_report = download_count_from_regex
                    if final_count_to_report == 0: 
                        final_count_to_report = scrape_tasks[task_id_arg]['final_download_count']
                    
                    scrape_tasks[task_id_arg]['status'] = 'finished'
                    scrape_tasks[task_id_arg]['message'] = f"Scraping completed successfully. {final_count_to_report} files downloaded."
                    scrape_tasks[task_id_arg]['progress_info'] = '' 
            else: 
                error_message = f"Scraping failed (code: {process.returncode}). Error message: {final_stderr.strip()}"
                
                if process.returncode < 0: 
                    if task_id_arg in scrape_tasks:
                        scrape_tasks[task_id_arg]['status'] = 'cancelled'
                        scrape_tasks[task_id_arg]['message'] = "Scraping cancelled by user."
                        scrape_tasks[task_id_arg]['progress_info'] = '' 
                else: 
                    if task_id_arg in scrape_tasks:
                        scrape_tasks[task_id_arg]['status'] = 'error'
                        scrape_tasks[task_id_arg]['message'] = error_message
                        scrape_tasks[task_id_arg]['progress_info'] = '' 
                    
        except Exception as e:
            error_message = f"Unexpected error occurred while executing scraper: {e}"
            if task_id_arg in scrape_tasks: 
                scrape_tasks[task_id_arg]['status'] = 'error'
                scrape_tasks[task_id_arg]['message'] = error_message
                scrape_tasks[task_id_arg]['progress_info'] = '' 
            if process: 
                try:
                    process.terminate()
                except Exception as term_e:
                    print(f"Error terminating scraper process: {term_e}")


    scraper_thread = threading.Thread(target=run_scraper_in_thread, args=(command, task_id))
    scraper_thread.start()

    return jsonify({"status": "processing", "message": "Scraping started. You can monitor progress.", "task_id": task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status_info_full = scrape_tasks.get(task_id, {
        'status': 'unknown', 
        'message': 'Task ID not found or task expired.',
        'progress_info': '',
        'final_download_count': 0 
    })
    
    status_info_clean = {k: v for k, v in status_info_full.items() if k != 'process'}
    
    return jsonify(status_info_clean)

@app.route('/stop_scrape/<task_id>', methods=['POST'])
def stop_scrape(task_id):
    task_info = scrape_tasks.get(task_id)
    if not task_info:
        return jsonify({"status": "error", "message": "Task not found."}), 404
    
    process_obj = task_info.get('process')
    if process_obj and process_obj.poll() is None: 
        try:
            process_obj.terminate() 
            return jsonify({"status": "success", "message": "Stop scraping request sent."})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error stopping scraping: {e}"}), 500
    else:
        return jsonify({"status": "info", "message": "Scraping not active or already finished."}), 200

# =========================================================
# NEW: API Routes for Creators List (from search functionality)
# =========================================================
@app.route('/api/creators')
def get_creators():
    """
    Returns cached creators list.
    If cache is expired or empty, starts background update.
    """
    platform = request.args.get('platform', 'coomer')  # Default coomer
    
    # Try to acquire lock, if not get in 5 seconds, return 503
    if not cache_lock.acquire(timeout=5): 
        logging.warning("Cache lock in use, unable to get creators list in time.")
        return jsonify({"message": "Creators cache is being updated. Please try again in a few seconds."}), 503

    try:
        creators_for_platform = creators_cache.get(platform, [])
        if creators_for_platform:
            current_time = datetime.now()
            # If cache expired, start silent background update
            if platform in cache_last_updated and cache_last_updated[platform] and (current_time - cache_last_updated[platform]) >= timedelta(hours=CACHE_LIFESPAN_HOURS):
                logging.info(f"Creators cache for {platform} expired. Starting silent background update.")
                threading.Thread(target=update_creators_cache_in_background, args=(False, platform)).start()
                
            # Return cache data
            return jsonify({
                'creators': creators_for_platform,
                'platform': platform,
                'last_updated': cache_last_updated.get(platform).isoformat() if cache_last_updated.get(platform) else None,
                'status': cache_status_message.get(platform, f"Status unavailable for {platform}")
            })
        else:
            # If cache empty, force update and notify client
            logging.warning(f"Creators cache for {platform} empty. Forcing update in background.")
            threading.Thread(target=update_creators_cache_in_background, args=(False, platform)).start()
            return jsonify({"message": f"Creators cache for {platform} empty. Starting download. Please refresh in a few seconds."}), 503
    finally:
        cache_lock.release() # Ensure lock is always released

@app.route('/api/update_creators', methods=['POST'])
def trigger_update_creators(): # Name changed to avoid conflict if both app.py exist in the same scope
    """Endpoint to force manual cache update for creators."""
    platform = request.json.get('platform') if request.is_json else request.form.get('platform')
    
    if platform:
        logging.info(f"Manual update request received for creators cache for {platform}.")
        threading.Thread(target=update_creators_cache_in_background, args=(True, platform)).start()
        return jsonify({"message": f"Creators cache update for {platform} started in background."}), 202
    else:
        logging.info("Manual update request received for all platforms.")
        threading.Thread(target=update_creators_cache_in_background, args=(True,)).start()
        return jsonify({"message": "Creators cache update for all platforms started in background."}), 202
# =========================================================
# FIN: API Routes for Creators List (from search functionality)
# =========================================================


if __name__ == '__main__':
    # --- MODIFICATION: Call cache initialization function ---
    initialize_app_on_startup() 
    # --- END MODIFICATION ---
    app.run(debug=True, threaded=True) # `threaded=True` is important for handling scraping threads
