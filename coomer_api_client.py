import requests
import json
import time
from datetime import datetime

class CoomerApiClient:
    """
    Cliente para interactuar con la API de Coomer para obtener la lista de creadores.
    Incluye lógica de reintentos y manejo de errores.
    """
    
    COOMER_API_URL = 'https://coomer.party/api/v1/creators'
    # Fallback si coomer.party falla, aunque no siempre está disponible
    # COOMER_API_URL_FALLBACK = 'https://coomer.su/api/v1/creators' 
    
    MAX_RETRIES = 5 # Número máximo de intentos si falla la petición
    RETRY_DELAY = 10 # Segundos de espera entre reintentos
    TIMEOUT = 60     # Segundos de tiempo de espera para la petición HTTP

    def __init__(self):
        pass

    def get_all_creators(self):
        """
        Intenta obtener la lista completa de creadores de la API de Coomer.
        
        Returns:
            list: Una lista de objetos creadores si la petición fue exitosa.
            None: Si la petición falla después de todos los reintentos.
        """
        for attempt in range(self.MAX_RETRIES):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Intento {attempt + 1}/{self.MAX_RETRIES}: Descargando lista de creadores de {self.COOMER_API_URL}")
            try:
                # Intenta con la URL principal
                response = requests.get(self.COOMER_API_URL, headers={'accept': 'application/json'}, timeout=self.TIMEOUT)
                response.raise_for_status() # Lanza una excepción si el estado HTTP es un error (4xx o 5xx)

                creators_data = response.json()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Descarga exitosa. Creadores encontrados: {len(creators_data)}")
                return creators_data
                
            except requests.exceptions.Timeout:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error de tiempo de espera (timeout) al conectar con {self.COOMER_API_URL}.")
            except requests.exceptions.ConnectionError as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error de conexión con {self.COOMER_API_URL}: {e}.")
                # Aquí podrías intentar con COOMER_API_URL_FALLBACK si lo habilitas.
            except requests.exceptions.HTTPError as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error HTTP: {e}. Código de estado: {response.status_code}.")
            except json.JSONDecodeError:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error al decodificar la respuesta JSON. El contenido no es un JSON válido.")
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ocurrió un error inesperado durante la descarga: {e}.")
            
            if attempt < self.MAX_RETRIES - 1:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reintentando en {self.RETRY_DELAY} segundos...")
                time.sleep(self.RETRY_DELAY)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FALLO: No se pudo obtener la lista de creadores después de {self.MAX_RETRIES} intentos.")
        return None

# Ejemplo de uso (solo para probar el módulo directamente)
if __name__ == '__main__':
    client = CoomerApiClient()
    creators = client.get_all_creators()
    if creators:
        print(f"\nObtenidos {len(creators)} creadores.")
        # Puedes guardar esto en un archivo si quieres:
        # with open('creators_downloaded.json', 'w', encoding='utf-8') as f:
        #     json.dump(creators, f, ensure_ascii=False, indent=2)
    else:
        print("No se pudo obtener la lista de creadores.")