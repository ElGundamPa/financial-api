#!/usr/bin/env python3
"""
Script de inicio para Financial Data API
Facilita el lanzamiento de la aplicación con configuración automática
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")

    try:
        import bs4
        import fastapi
        import playwright
        import requests
        import uvicorn

        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return False


def install_playwright_browsers():
    """Instalar navegadores de Playwright si no están instalados"""
    print("🌐 Verificando navegadores de Playwright...")

    try:
        # Verificar si chromium está instalado
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
                browser.close()
                print("✅ Navegadores de Playwright ya están instalados")
                return True
            except Exception:
                pass
    except Exception:
        pass

    print("📥 Instalando navegadores de Playwright...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, capture_output=True)
        print("✅ Navegadores instalados correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando navegadores: {e}")
        return False


def create_directories():
    """Crear directorios necesarios"""
    print("📁 Creando directorios...")

    directories = ["screenshots", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directorio {directory} creado/verificado")


def setup_environment():
    """Configurar variables de entorno por defecto"""
    print("⚙️ Configurando entorno...")

    # Variables de entorno por defecto
    env_vars = {
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "SCRAPING_INTERVAL_MINUTES": "50",
        "LOG_LEVEL": "INFO",
        "ENABLE_SCREENSHOTS": "true",
    }

    # Establecer variables si no están definidas
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"✅ {key} = {value}")


def start_api(mode="main", host="0.0.0.0", port=8000, reload=True):
    """Iniciar la API"""
    print(f"🚀 Iniciando API en modo: {mode}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"📊 Endpoints disponibles:")
    print(f"   - GET  http://{host}:{port}/")
    print(f"   - GET  http://{host}:{port}/datos")
    print(f"   - GET  http://{host}:{port}/datos/resume")
    print(f"   - POST http://{host}:{port}/scrape")
    print(f"   - GET  http://{host}:{port}/health")
    print(f"")
    print(f"📈 Por tipo de dato:")
    print(f"   - GET  http://{host}:{port}/datos/indices")
    print(f"   - GET  http://{host}:{port}/datos/acciones")
    print(f"   - GET  http://{host}:{port}/datos/cripto")
    print(f"   - GET  http://{host}:{port}/datos/forex")
    print(f"   - GET  http://{host}:{port}/datos/etfs")
    print(f"   - GET  http://{host}:{port}/datos/materias-primas")
    print(f"")
    print(f"🌐 Por fuente:")
    print(f"   - GET  http://{host}:{port}/datos/tradingview")
    print(f"   - GET  http://{host}:{port}/datos/finviz")
    print(f"   - GET  http://{host}:{port}/datos/yahoo")
    print(f"")
    print(f"📊 TradingView específico:")
    print(f"   - GET  http://{host}:{port}/datos/tradingview/indices")
    print(f"   - GET  http://{host}:{port}/datos/tradingview/acciones")
    print(f"   - GET  http://{host}:{port}/datos/tradingview/cripto")
    print(f"   - GET  http://{host}:{port}/datos/tradingview/forex")
    print(f"")
    print(f"📊 Finviz específico:")
    print(f"   - GET  http://{host}:{port}/datos/finviz/indices")
    print(f"   - GET  http://{host}:{port}/datos/finviz/acciones")
    print(f"   - GET  http://{host}:{port}/datos/finviz/forex")
    print(f"")
    print(f"📊 Yahoo específico:")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/indices")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/acciones")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/forex")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/etfs")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/materias-primas")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/gainers")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/losers")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/most-active")
    print(f"   - GET  http://{host}:{port}/datos/yahoo/undervalued")
    print("=" * 50)

    try:
        # Construir comando uvicorn
        cmd = [sys.executable, "-m", "uvicorn", f"{mode}:app", "--host", host, "--port", str(port)]

        if reload:
            cmd.append("--reload")

        # Ejecutar uvicorn
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n⏹️ API detenida por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando API: {e}")


def run_bot():
    """Ejecutar el bot de scraping"""
    print("🤖 Ejecutando bot de scraping...")

    try:
        subprocess.run([sys.executable, "bot_scraper.py"])
    except KeyboardInterrupt:
        print("\n⏹️ Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando bot: {e}")


def main():
    parser = argparse.ArgumentParser(description="Financial Data API - Script de inicio")
    parser.add_argument(
        "--mode", choices=["main", "api"], default="main", help="Modo de ejecución: main (con scheduler) o api (solo API)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host para la API")
    parser.add_argument("--port", type=int, default=8000, help="Puerto para la API")
    parser.add_argument("--no-reload", action="store_true", help="Deshabilitar auto-reload")
    parser.add_argument("--bot-only", action="store_true", help="Solo ejecutar el bot de scraping")
    parser.add_argument("--skip-checks", action="store_true", help="Saltar verificaciones iniciales")

    args = parser.parse_args()

    print("🎯 Financial Data API - Script de inicio")
    print("=" * 50)

    if not args.skip_checks:
        # Verificaciones iniciales
        if not check_dependencies():
            sys.exit(1)

        if not install_playwright_browsers():
            print("⚠️ Continuando sin navegadores de Playwright...")

        create_directories()
        setup_environment()

    if args.bot_only:
        run_bot()
    else:
        start_api(mode=args.mode, host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()
