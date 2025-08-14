#!/usr/bin/env python3
"""
Tests de integración simples para CI/CD
"""

import json
import os
import sys


def test_project_structure():
    """Verificar estructura básica del proyecto"""
    # Verificar archivos esenciales
    essential_files = ["requirements.txt", "README.md", "vercel.json", "api/index.py"]

    for file_path in essential_files:
        assert os.path.exists(file_path), f"Archivo esencial no encontrado: {file_path}"

    # Verificar directorios
    essential_dirs = ["tests", "api", "scrapers"]

    for dir_path in essential_dirs:
        assert os.path.isdir(dir_path), f"Directorio esencial no encontrado: {dir_path}"


def test_requirements_file():
    """Verificar archivo requirements.txt"""
    with open("requirements.txt", "r") as f:
        content = f.read()

    # Verificar que contiene dependencias básicas
    assert "fastapi" in content, "fastapi no encontrado en requirements.txt"
    assert "pytest" in content, "pytest no encontrado en requirements.txt"
    assert "cachetools" in content, "cachetools no encontrado en requirements.txt"


def test_vercel_config():
    """Verificar configuración de Vercel"""
    with open("vercel.json", "r") as f:
        config = json.load(f)

    # Verificar estructura básica
    assert "functions" in config, "functions no encontrado en vercel.json"
    assert "routes" in config, "routes no encontrado en vercel.json"


def test_api_entry_point():
    """Verificar punto de entrada de la API"""
    api_file = "api/index.py"
    assert os.path.exists(api_file), "api/index.py no encontrado"

    with open(api_file, "r") as f:
        content = f.read()

    # Verificar que importa create_app
    assert "create_app" in content, "create_app no encontrado en api/index.py"


def test_environment_variables():
    """Verificar variables de entorno"""
    # Verificar que podemos acceder a variables de entorno
    test_var = os.getenv("TEST_VAR", "default_value")
    assert test_var == "default_value", f"Variable de entorno inesperada: {test_var}"


def test_python_environment():
    """Verificar entorno de Python"""
    # Verificar versión de Python
    version = sys.version_info
    assert version.major == 3, f"Se requiere Python 3, encontrado: {version.major}"
    assert version.minor >= 8, f"Se requiere Python 3.8+, encontrado: {version.major}.{version.minor}"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
