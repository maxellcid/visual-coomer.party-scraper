from flask import Flask, render_template, request, jsonify
import subprocess
import os
import threading
import uuid
import re 
import signal
import time 
import json # Nuevo: para manejar la caché de creadores
from datetime import datetime, timedelta # Nuevo: para la lógica de caché
import logging # Ya estaba, pero lo menciono por su uso en la caché

# Importa el cliente API para Coomer/Kemono. Asegúrate de que este archivo exista en la misma carpeta.
from coomer_api_client import CoomerApiClient

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

app = Flask(__name__)

# Diccionario para almacenar el estado de las tareas de scraping
scrape_tasks = {}

# =========================================================
# NUEVO: Lógica de Caché para la lista de Creadores (del buscador)
# =========================================================
api_client = CoomerApiClient() # Instancia del cliente API para obtener creadores

CACHE_FILE = 'creators_cache.json' # Archivo para guardar la caché
creators_cache = [] # Lista global para almacenar los creadores
cache_last_updated = None # Fecha/hora de la última actualización de la caché
cache_status_message = "Cargando lista de creadores..." # Mensaje de estado inicial
cache_lock = threading.Lock() # Bloqueo para proteger el acceso a la caché compartida

CACHE_LIFESPAN_HOURS = 24 # Tiempo de vida de la caché antes de intentar una nueva descarga

# --- Funciones de la caché ---

def load_cache_from_file():
    """Intenta cargar la caché de creadores desde un archivo local."""
    global creators_cache, cache_last_updated, cache_status_message

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                creators_cache = data.get('creators', [])
                last_updated_str = data.get('last_updated')
                if last_updated_str:
                    cache_last_updated = datetime.fromisoformat(last_updated_str)
                else:
                    cache_last_updated = None
                
                logging.info(f"Caché cargada desde '{CACHE_FILE}' con {len(creators_cache)} elementos.")
                logging.info(f"Última actualización del archivo: {cache_last_updated.strftime('%Y-%m-%d %H:%M:%S') if cache_last_updated else 'Nunca'}")
                cache_status_message = f"Cargado {len(creators_cache)} creadores desde archivo."
                return True
        except json.JSONDecodeError as e:
            logging.error(f"Error al leer el archivo de caché JSON '{CACHE_FILE}': {e}")
            cache_status_message = "Error al cargar la caché desde el archivo."
            return False
        except Exception as e:
            logging.error(f"Error inesperado al cargar la caché desde '{CACHE_FILE}': {e}")
            cache_status_message = "Error inesperado al cargar la caché."
            return False
    else:
        logging.info(f"Archivo de caché '{CACHE_FILE}' no encontrado.")
        cache_status_message = "Caché no encontrada en disco."
        return False

def save_cache_to_file():
    """Guarda la caché de creadores actual en un archivo local."""
    global creators_cache, cache_last_updated
    try:
        data = {
            'creators': creators_cache,
            'last_updated': cache_last_updated.isoformat() if cache_last_updated else None
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Caché guardada en '{CACHE_FILE}'.")
    except Exception as e:
        logging.error(f"Error al guardar la caché en '{CACHE_FILE}': {e}")

def update_creators_cache_in_background(force_update=False):
    """
    Descarga la última lista de creadores en segundo plano.
    Utiliza un bloqueo para evitar actualizaciones concurrentes.
    """
    global creators_cache, cache_last_updated, cache_status_message

    if not cache_lock.acquire(blocking=False): # Intenta adquirir el bloqueo sin esperar
        logging.info("Intento de actualización en segundo plano: el bloqueo de la caché ya está en uso. Saltando esta ejecución.")
        return # Si el bloqueo ya está en uso, otra actualización ya está en curso

    try:
        current_time = datetime.now()
        # Si no es una actualización forzada y la caché no ha caducado, no hacer nada
        if not force_update and cache_last_updated and (current_time - cache_last_updated) < timedelta(hours=CACHE_LIFESPAN_HOURS):
            logging.info("Caché de creadores actualizada hace menos de 24 horas. No se requiere descarga.")
            cache_status_message = f"Cargado {len(creators_cache)} creadores (reciente)."
            return # Salir si no se necesita actualizar

        logging.info("Intentando descargar la última lista de creadores de Coomer API...")
        cache_status_message = "Descargando la lista de creadores..." # Actualiza el estado visible para el frontend

        downloaded_creators = api_client.get_all_creators() # Llama al cliente API

        if downloaded_creators:
            creators_cache = downloaded_creators
            cache_last_updated = datetime.now()
            save_cache_to_file() # Guarda la caché actualizada en el disco
            cache_status_message = f"Cargado {len(creators_cache)} creadores (actualizado)."
            logging.info(f"Descarga exitosa. Creadores encontrados: {len(creators_cache)}")
        else:
            cache_status_message = f"Fallo al descargar. Se mantiene la caché anterior ({len(creators_cache)} creadores) si existe."
            logging.error("Fallo la descarga de creadores. La caché no fue actualizada.")
    finally:
        cache_lock.release() # Asegura que el bloqueo se libere siempre

def initialize_app_on_startup():
    """Se ejecuta una vez al iniciar la aplicación para cargar y actualizar la caché de creadores."""
    global cache_status_message
    
    # 1. Intentar cargar la caché del archivo local
    if load_cache_from_file():
        cache_status_message = f"Cargado {len(creators_cache)} creadores desde archivo."
    else:
        cache_status_message = "Caché vacía. Iniciando descarga en segundo plano."

    # 2. Iniciar el hilo de actualización en segundo plano
    threading.Thread(target=update_creators_cache_in_background).start()
# =========================================================
# FIN: Lógica de Caché para la lista de Creadores
# =========================================================


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url_from_frontend = request.form.get('url')
    
    if not url_from_frontend:
        username = request.form.get('username')
        domain = request.form.get('domain')
        service = request.form.get('service')

        if not username:
            return jsonify({"status": "error", "message": "El nombre de usuario o la URL son obligatorios."}), 400
        
        final_url = f"https://{domain}/{service}/user/{username}"
    else:
        final_url = url_from_frontend

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
        return jsonify({"status": "error", "message": "Los offsets deben ser números válidos."}), 400

    task_id = str(uuid.uuid4())
    
    scrape_tasks[task_id] = {
        'status': 'running',
        'message': f'Scraping de {final_url} iniciado en segundo plano...',
        'process': None, 
        'progress_info': 'Iniciando...',
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

    # --- NUEVAS FUNCIONES PARA LEER STDOUT/STDERR EN HILOS SEPARADOS ---
    def _read_stdout(pipe, buffer_list, task_id_arg, progress_regex):
        """Lee stdout y actualiza el progreso en el diccionario de tareas."""
        for line in iter(pipe.readline, ''): 
            buffer_list.append(line)
            match_progress = progress_regex.search(line)
            if match_progress:
                downloaded_count = int(match_progress.group(1)) 
                total_count = int(match_progress.group(2)) 
                if task_id_arg in scrape_tasks:
                    scrape_tasks[task_id_arg]['progress_info'] = f"Descargando: {downloaded_count} de {total_count} archivos"
                    scrape_tasks[task_id_arg]['message'] = scrape_tasks[task_id_arg]['progress_info']
                    scrape_tasks[task_id_arg]['final_download_count'] = downloaded_count 

    def _read_stderr(pipe, buffer_list, task_id_arg):
        """Lee stderr y lo añade al buffer."""
        for line in iter(pipe.readline, ''): 
            buffer_list.append(line)
    # --- FIN NUEVAS FUNCIONES ---

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
                    scrape_tasks[task_id_arg]['message'] = f"Scraping completado con éxito. Se descargaron {final_count_to_report} archivos."
                    scrape_tasks[task_id_arg]['progress_info'] = '' 
            else: 
                error_message = f"Scraping fallido (código: {process.returncode}). Mensaje de error: {final_stderr.strip()}"
                
                if process.returncode < 0: 
                    if task_id_arg in scrape_tasks:
                        scrape_tasks[task_id_arg]['status'] = 'cancelled'
                        scrape_tasks[task_id_arg]['message'] = "Scraping cancelado por el usuario."
                        scrape_tasks[task_id_arg]['progress_info'] = '' 
                else: 
                    if task_id_arg in scrape_tasks:
                        scrape_tasks[task_id_arg]['status'] = 'error'
                        scrape_tasks[task_id_arg]['message'] = error_message
                        scrape_tasks[task_id_arg]['progress_info'] = '' 
                    
        except Exception as e:
            error_message = f"Ocurrió un error inesperado al ejecutar el scraper: {e}"
            if task_id_arg in scrape_tasks: 
                scrape_tasks[task_id_arg]['status'] = 'error'
                scrape_tasks[task_id_arg]['message'] = error_message
                scrape_tasks[task_id_arg]['progress_info'] = '' 
            if process: 
                try:
                    process.terminate()
                except Exception as term_e:
                    print(f"Error al terminar el proceso de scraper: {term_e}")


    scraper_thread = threading.Thread(target=run_scraper_in_thread, args=(command, task_id))
    scraper_thread.start()

    return jsonify({"status": "processing", "message": "Scraping iniciado. Puedes monitorear el progreso.", "task_id": task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status_info_full = scrape_tasks.get(task_id, {
        'status': 'unknown', 
        'message': 'ID de tarea no encontrado o tarea expirada.',
        'progress_info': '',
        'final_download_count': 0 
    })
    
    status_info_clean = {k: v for k, v in status_info_full.items() if k != 'process'}
    
    return jsonify(status_info_clean)

@app.route('/stop_scrape/<task_id>', methods=['POST'])
def stop_scrape(task_id):
    task_info = scrape_tasks.get(task_id)
    if not task_info:
        return jsonify({"status": "error", "message": "Tarea no encontrada."}), 404
    
    process_obj = task_info.get('process')
    if process_obj and process_obj.poll() is None: 
        try:
            process_obj.terminate() 
            return jsonify({"status": "success", "message": "Solicitud para detener el scraping enviada."})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error al intentar detener el scraping: {e}"}), 500
    else:
        return jsonify({"status": "info", "message": "El scraping no está activo o ya ha terminado."}), 200

# =========================================================
# NUEVO: Rutas API para la lista de Creadores (del buscador)
# =========================================================
@app.route('/api/creators')
def get_creators():
    """
    Devuelve la lista cacheadada de creadores.
    Si la caché está caducada o vacía, inicia una actualización en segundo plano.
    """
    # Intenta adquirir el bloqueo, si no lo consigue en 5 segundos, devuelve un error 503
    if not cache_lock.acquire(timeout=5): 
        logging.warning("El bloqueo de caché está en uso, no se pudo obtener la lista de creadores a tiempo.")
        return jsonify({"message": "La caché de creadores se está actualizando. Por favor, intente de nuevo en unos segundos."}), 503

    try:
        if creators_cache:
            current_time = datetime.now()
            # Si la caché ha caducado, inicia una actualización silenciosa en segundo plano
            if cache_last_updated and (current_time - cache_last_updated) >= timedelta(hours=CACHE_LIFESPAN_HOURS):
                logging.info("Caché caducada. Iniciando actualización silenciosa en segundo plano.")
                threading.Thread(target=update_creators_cache_in_background).start()
                
            # Devuelve los datos de la caché
            return jsonify({
                'creators': creators_cache,
                'last_updated': cache_last_updated.isoformat() if cache_last_updated else None,
                'status': cache_status_message
            })
        else:
            # Si la caché está vacía, fuerza una actualización y notifica al cliente
            logging.warning("Caché de creadores vacía. Forzando una actualización en segundo plano.")
            threading.Thread(target=update_creators_cache_in_background).start()
            return jsonify({"message": "La caché está vacía. Iniciando descarga. Por favor, recargue en unos segundos."}), 503
    finally:
        cache_lock.release() # Asegura que el bloqueo se libere siempre

@app.route('/api/update_creators', methods=['POST'])
def trigger_update_creators(): # Nombre cambiado para evitar conflicto si ambos app.py existieran en el mismo scope
    """Endpoint para forzar una actualización manual de la caché de creadores."""
    logging.info("Solicitud de actualización forzada recibida para la caché de creadores.")
    threading.Thread(target=update_creators_cache_in_background, args=(True,)).start()
    return jsonify({"message": "Actualización de creadores iniciada en segundo plano."}), 202
# =========================================================
# FIN: Rutas API para la lista de Creadores
# =========================================================


if __name__ == '__main__':
    # --- MODIFICACIÓN: Llamar a la función de inicialización de la caché ---
    initialize_app_on_startup() 
    # --- FIN MODIFICACIÓN ---
    app.run(debug=True, threaded=True) # `threaded=True` es importante para manejar hilos de scraping
