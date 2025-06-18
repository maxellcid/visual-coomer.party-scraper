from flask import Flask, render_template, request, jsonify
import subprocess
import os
import threading
import uuid
import re 
import signal
import time 

app = Flask(__name__)

# Diccionario para almacenar el estado de las tareas de scraping
scrape_tasks = {}

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

if __name__ == '__main__':
    app.run(debug=True)
