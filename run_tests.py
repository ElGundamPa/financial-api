#!/usr/bin/env python3
"""
Script para ejecutar tests de la Financial Data API
"""

import os
import subprocess
import sys


def run_tests():
    """Ejecutar todos los tests"""
    print("🧪 Ejecutando tests de Financial Data API...")
    print("=" * 50)

    # Verificar que pytest esté instalado
    try:
        import pytest
    except ImportError:
        print("❌ pytest no está instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "httpx"])

    # Crear directorio de tests si no existe
    if not os.path.exists("tests"):
        os.makedirs("tests")
        print("📁 Directorio tests creado")

    # Ejecutar tests
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"], capture_output=False
        )

        if result.returncode == 0:
            print("\n✅ Todos los tests pasaron exitosamente!")
        else:
            print("\n❌ Algunos tests fallaron")
            return False

    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False

    return True


def run_coverage():
    """Ejecutar tests con cobertura"""
    print("\n📊 Ejecutando tests con cobertura...")

    try:
        # Instalar coverage si no está instalado
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"])

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--cov=.", "--cov-report=html", "--cov-report=term-missing", "-v"],
            capture_output=False,
        )

        if result.returncode == 0:
            print("\n✅ Reporte de cobertura generado en htmlcov/")
        else:
            print("\n❌ Error generando reporte de cobertura")

    except Exception as e:
        print(f"❌ Error ejecutando coverage: {e}")


if __name__ == "__main__":
    print("🚀 Financial Data API - Test Runner")
    print("=" * 50)

    # Ejecutar tests básicos
    if run_tests():
        # Preguntar si ejecutar coverage
        response = input("\n¿Ejecutar tests con cobertura? (y/n): ").lower()
        if response in ["y", "yes", "sí", "si"]:
            run_coverage()
    else:
        print("\n❌ Los tests fallaron. Revisa los errores antes de continuar.")
        sys.exit(1)
