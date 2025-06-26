import threading

# Configuración de cache
CACHE_FILE = 'logs/app.log'
CACHE_LIFESPAN_HOURS = 24
CACHE_LIFESPAN_SECONDS = CACHE_LIFESPAN_HOURS * 3600

# Diccionarios para cache
creators_cache = {}
cache_last_updated = {}
cache_status_message = {}

# Lock para operaciones de cache
cache_lock = threading.Lock()
