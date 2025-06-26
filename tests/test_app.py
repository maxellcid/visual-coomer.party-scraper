import pytest
import json
import os
from datetime import datetime
from app import app
from cache_manager import (
    load_cache_from_file,
    save_cache_to_file,
    clear_cache,
    CacheConfig
)

@pytest.mark.parametrize('url, expected_status', [
    ('/', 200),
    ('/scrape', 405),  # Debe ser POST
    ('/health', 200)
])
def test_routes(client, url, expected_status):
    """Testea las rutas principales de la aplicación"""
    response = client.get(url)
    assert response.status_code == expected_status

def test_cache_operations():
    """Testea las operaciones de cache"""
    try:
        # Importar las variables globales
        from cache_manager import (
            creators_cache,
            cache_last_updated,
            cache_status_message,
            CacheConfig
        )
        
        # Crear datos de prueba
        test_data = {
            'coomer': [{'id': '1', 'name': 'test'}]
        }
        
        # Inicializar variables globales
        creators_cache.clear()
        cache_last_updated.clear()
        cache_status_message.clear()
        
        # Guardar datos en el cache usando la función de guardado
        creators_cache.update({
            'coomer': test_data['coomer']
        })
        cache_last_updated.update({
            'coomer': datetime.now().isoformat()
        })
        
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(CacheConfig.CACHE_FILE), exist_ok=True)
        
        # Guardar el cache
        result = save_cache_to_file()
        assert result is True
        
        # Limpiar el cache antes de cargar
        clear_cache()
        
        # Testear cargar cache
        result = load_cache_from_file()
        assert result is True
        
        # Verificar contenido
        assert len(creators_cache['coomer']) == 1
        assert cache_last_updated['coomer'] is not None
        
        # Verificar mensaje de estado
        assert cache_status_message['coomer'].startswith('Loaded')

    finally:
        # Limpiar el cache
        clear_cache()

def test_scrape_endpoint(client):
    """Testea el endpoint de scrape con datos válidos"""
    test_data = {
        'username': 'test_user',
        'domain': 'coomer.party',
        'service': 'user'
    }
    
    response = client.post('/scrape', data=test_data)
    assert response.status_code == 200
    
    # Verificar que la respuesta es JSON
    assert response.is_json
    
    # Verificar estructura básica de la respuesta
    data = response.json
    assert 'status' in data
    assert 'message' in data

def test_scrape_endpoint_invalid_data(client):
    """Testea el endpoint de scrape con datos inválidos"""
    # Sin username
    response = client.post('/scrape', data={'domain': 'coomer.party'})
    assert response.status_code == 400
    
    # Sin dominio
    response = client.post('/scrape', data={'username': 'test_user'})
    assert response.status_code == 400
