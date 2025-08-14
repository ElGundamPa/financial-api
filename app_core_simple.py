import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from cachetools import TTLCache

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache global en memoria (efímero por instancia)
cache = TTLCache(maxsize=128, ttl=90)  # 90 segundos TTL


class Settings:
    """Configuración de la aplicación"""

    def __init__(self, runtime: str = "local"):
        self.runtime = runtime
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        self.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))
        self.http_timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "12"))
        self.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "90"))
        self.max_body_kb = int(os.getenv("MAX_BODY_KB", "128"))

        # Configuración específica para Vercel
        if runtime == "vercel":
            self.disable_browser_sources = True
            self.enable_compression = True
        else:
            self.disable_browser_sources = False
            self.enable_compression = True


def get_sources_status(settings: Settings) -> Dict[str, Dict[str, Any]]:
    """Obtener estado de las fuentes disponibles"""
    sources = {
        "finviz": {
            "name": "Finviz",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex"],
            "requires_browser": False,
        },
        "yahoo": {
            "name": "Yahoo Finance",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex", "materias_primas", "etfs"],
            "requires_browser": False,
        },
    }

    # En Vercel, deshabilitar fuentes que requieren navegador
    if settings.runtime == "vercel":
        sources["tradingview"] = {
            "name": "TradingView",
            "status": "browser_required_disabled_in_prod",
            "data_types": ["indices", "acciones", "forex", "cripto"],
            "requires_browser": True,
        }
    else:
        sources["tradingview"] = {
            "name": "TradingView",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex", "cripto"],
            "requires_browser": True,
        }

    return sources


async def scrape_all_data(settings: Settings) -> Dict[str, Any]:
    """Scrapear todos los datos de las fuentes habilitadas"""
    logger.info("🚀 Iniciando scraping de todas las fuentes")

    # Determinar fuentes a scrapear
    sources_status = get_sources_status(settings)
    enabled_sources = [name for name, info in sources_status.items() if info["status"] == "ok"]

    # Crear tareas para scraping asíncrono
    tasks = []
    for source in enabled_sources:
        task = scrape_source(source, settings)
        tasks.append(task)

    # Ejecutar scraping en paralelo
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Procesar resultados
    scraped_data = {}
    errors = []

    for i, source in enumerate(enabled_sources):
        result = results[i]
        if isinstance(result, Exception):
            logger.error(f"❌ Error en {source}: {result}")
            errors.append({"source": source, "error": str(result)})
            scraped_data[source] = {}
        else:
            scraped_data[source] = result

    return {
        "data": scraped_data,
        "errors": errors,
        "last_updated": time.time(),
        "timestamp": time.time(),
        "sources_scraped": enabled_sources,
        "total_sources": len(enabled_sources),
    }


async def scrape_source(source: str, settings: Settings) -> Dict[str, List[Dict[str, str]]]:
    """Scrapear una fuente específica"""
    logger.info(f"🔄 Iniciando scraping de {source}")

    if source == "finviz":
        return await scrape_finviz()
    elif source == "yahoo":
        return await scrape_yahoo()
    elif source == "tradingview":
        if settings.runtime == "vercel":
            return {"error": "browser_required_disabled_in_prod"}
        else:
            return await scrape_tradingview()
    else:
        return {}


def create_data_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crear resumen de datos por categorías"""
    summary = {
        "indices": [],
        "acciones": [],
        "forex": [],
        "materias_primas": [],
        "etfs": [],
        "cripto": [],
        "last_updated": time.time(),
        "sources": {},
    }

    # Mapeo de tipos de datos específicos a categorías generales
    data_type_mapping = {
        "indices": "indices",
        "acciones": "acciones",
        "forex": "forex",
        "materias_primas": "materias_primas",
        "etfs": "etfs",
        "cripto": "cripto",
        "gainers": "acciones",  # gainers y losers van a acciones
        "losers": "acciones",
        "most_active_stocks": "acciones",
        "most_active_etfs": "etfs",
    }

    for source, source_data in data.get("data", {}).items():
        source_summary = {"has_data": False, "data_types": {}}

        for data_type, items in source_data.items():
            if items and len(items) > 0:
                # Mapear tipo específico a categoría general
                category = data_type_mapping.get(data_type, data_type)
                if category in summary:
                    summary[category].extend(items[:10])  # Top 10 por categoría
                    source_summary["data_types"][data_type] = len(items)
                    source_summary["has_data"] = True

        summary["sources"][source] = source_summary

    # Limitar resumen a top 20 por categoría
    for category in summary:
        if isinstance(summary[category], list):
            summary[category] = summary[category][:20]

    return summary


# Funciones mock para los scrapers (por ahora)
async def scrape_finviz() -> Dict[str, List[Dict[str, str]]]:
    """Mock scraper para Finviz"""
    return {
        "indices": [
            {"nombre": "S&P 500", "precio": "4,500.00", "cambio": "+0.5%"},
            {"nombre": "NASDAQ", "precio": "14,200.00", "cambio": "+0.3%"},
        ],
        "acciones": [
            {"nombre": "AAPL", "precio": "150.00", "cambio": "+1.2%"},
            {"nombre": "GOOGL", "precio": "2,800.00", "cambio": "+0.8%"},
        ],
        "forex": [
            {"nombre": "EUR/USD", "precio": "1.0850", "cambio": "-0.1%"},
            {"nombre": "USD/JPY", "precio": "150.50", "cambio": "+0.2%"},
        ],
    }


async def scrape_yahoo() -> Dict[str, List[Dict[str, str]]]:
    """Mock scraper para Yahoo Finance"""
    return {
        "indices": [
            {"nombre": "Dow Jones", "precio": "35,000.00", "cambio": "+0.4%"},
            {"nombre": "Russell 2000", "precio": "1,800.00", "cambio": "+0.6%"},
        ],
        "acciones": [
            {"nombre": "MSFT", "precio": "380.00", "cambio": "+1.5%"},
            {"nombre": "TSLA", "precio": "250.00", "cambio": "+2.1%"},
        ],
        "forex": [
            {"nombre": "GBP/USD", "precio": "1.2650", "cambio": "+0.3%"},
            {"nombre": "USD/CHF", "precio": "0.8900", "cambio": "-0.1%"},
        ],
        "materias_primas": [
            {"nombre": "Oro", "precio": "2,000.00", "cambio": "+0.7%"},
            {"nombre": "Petróleo", "precio": "75.00", "cambio": "-1.2%"},
        ],
    }


async def scrape_tradingview() -> Dict[str, List[Dict[str, str]]]:
    """Mock scraper para TradingView"""
    return {
        "indices": [{"nombre": "IBEX 35", "precio": "9,500.00", "cambio": "+0.2%"}],
        "cripto": [
            {"nombre": "Bitcoin", "precio": "45,000.00", "cambio": "+3.5%"},
            {"nombre": "Ethereum", "precio": "2,800.00", "cambio": "+2.8%"},
        ],
    }


def create_app(runtime: str = "local"):
    """Factory para crear la aplicación (versión simplificada)"""
    settings = Settings(runtime)

    # Por ahora, solo retornamos un diccionario con la configuración
    return {
        "runtime": runtime,
        "settings": {
            "cors_origins": settings.cors_origins,
            "rate_limit_rpm": settings.rate_limit_rpm,
            "http_timeout": settings.http_timeout,
            "cache_ttl": settings.cache_ttl,
            "max_body_kb": settings.max_body_kb,
        },
        "sources_status": get_sources_status(settings),
        "version": "2.1.0",
    }
