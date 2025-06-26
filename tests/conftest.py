import pytest
import os
from app import app
from cache_manager import (
    clear_cache,
    CacheConfig
)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Fixture que se ejecuta antes de cada test para limpiar el entorno"""
    clear_cache()
    # Guardar el archivo de cache original
    original_cache_file = CacheConfig.CACHE_FILE
    # Usar el archivo de cache de tests
    CacheConfig.CACHE_FILE = 'tests/test_cache.json'
    yield
    # Restaurar el archivo de cache original
    CacheConfig.CACHE_FILE = original_cache_file
    # Limpiar el cache
    clear_cache()
    # Eliminar el archivo de cache de tests si existe
    if os.path.exists('tests/test_cache.json'):
        os.remove('tests/test_cache.json')

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
