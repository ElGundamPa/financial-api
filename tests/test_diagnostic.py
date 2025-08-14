#!/usr/bin/env python3
"""
Test de diagnóstico para identificar problemas de importación
"""

import sys
import os


def test_python_environment():
    """Verificar entorno de Python"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    assert True


def test_basic_imports():
    """Verificar importaciones básicas"""
    try:
        import pytest
        print("✅ pytest imported successfully")
    except ImportError as e:
        print(f"❌ pytest import failed: {e}")
        raise
    
    try:
        import asyncio
        print("✅ asyncio imported successfully")
    except ImportError as e:
        print(f"❌ asyncio import failed: {e}")
        raise
    
    try:
        import json
        print("✅ json imported successfully")
    except ImportError as e:
        print(f"❌ json import failed: {e}")
        raise


def test_project_imports():
    """Verificar importaciones del proyecto"""
    try:
        import app_core_simple
        print("✅ app_core_simple imported successfully")
    except ImportError as e:
        print(f"❌ app_core_simple import failed: {e}")
        print(f"Current directory contents: {os.listdir('.')}")
        raise
    
    try:
        from app_core_simple import Settings
        print("✅ Settings imported successfully")
    except ImportError as e:
        print(f"❌ Settings import failed: {e}")
        raise
    
    try:
        from app_core_simple import create_app
        print("✅ create_app imported successfully")
    except ImportError as e:
        print(f"❌ create_app import failed: {e}")
        raise


def test_cachetools_import():
    """Verificar importación de cachetools"""
    try:
        from cachetools import TTLCache
        print("✅ TTLCache imported successfully")
    except ImportError as e:
        print(f"❌ TTLCache import failed: {e}")
        raise


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
