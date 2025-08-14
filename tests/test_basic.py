#!/usr/bin/env python3
"""
Tests básicos para verificar la funcionalidad core sin FastAPI
"""

import asyncio
import json

import pytest

from app_core_simple import Settings, create_app, create_data_summary, scrape_all_data


def test_create_app():
    """Test creación de aplicación"""
    app = create_app('vercel')
    assert app['runtime'] == 'vercel'
    assert 'settings' in app
    assert 'sources_status' in app
    assert 'version' in app

def test_settings():
    """Test configuración"""
    settings = Settings('vercel')
    assert settings.runtime == 'vercel'
    assert settings.rate_limit_rpm > 0
    assert settings.http_timeout > 0
    assert settings.cache_ttl > 0

@pytest.mark.asyncio
async def test_scrape_all_data():
    """Test scraping de datos"""
    settings = Settings('vercel')
    data = await scrape_all_data(settings)
    
    assert 'total_sources' in data
    assert 'last_updated' in data
    assert 'data' in data
    assert isinstance(data['data'], dict)

def test_create_data_summary():
    """Test creación de resumen de datos"""
    test_data = {
        'data': {
            'finviz': {
                'indices': [{'nombre': 'S&P 500', 'precio': '4500'}],
                'forex': [{'nombre': 'EUR/USD', 'precio': '1.0850'}]
            },
            'yahoo': {
                'indices': [{'nombre': 'NASDAQ', 'precio': '14200'}],
                'gainers': [{'nombre': 'AAPL', 'precio': '150'}]
            }
        }
    }
    
    summary = create_data_summary(test_data)
    
    assert 'last_updated' in summary
    assert 'indices' in summary
    assert 'forex' in summary
    assert 'acciones' in summary
    assert 'sources' in summary
    assert len(summary['indices']) > 0
    assert len(summary['forex']) > 0
    assert len(summary['acciones']) > 0

def test_settings_environment():
    """Test configuración por ambiente"""
    # Test local
    local_settings = Settings('local')
    assert local_settings.runtime == 'local'
    
    # Test vercel
    vercel_settings = Settings('vercel')
    assert vercel_settings.runtime == 'vercel'

def test_cache_functionality():
    """Test funcionalidad de cache"""
    from cachetools import TTLCache

    # Crear cache de prueba
    cache = TTLCache(maxsize=10, ttl=60)
    
    # Agregar datos
    cache['test_key'] = 'test_value'
    assert 'test_key' in cache
    assert cache['test_key'] == 'test_value'
    
    # Limpiar cache
    cache.clear()
    assert len(cache) == 0

if __name__ == "__main__":
    pytest.main([__file__])
