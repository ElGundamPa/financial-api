import os
from typing import Dict, List

# API Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = f"http://{API_HOST}:{API_PORT}/update_data"

# Scraping Configuration
SCRAPING_INTERVAL_MINUTES = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "50"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "60000"))

# Data Storage
DATA_FILE = os.getenv("DATA_FILE", "data.json")
BACKUP_FILE = os.getenv("BACKUP_FILE", "data_backup.json")

# User Agents for rotation
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
]

# URLs for scraping
TRADINGVIEW_URLS: Dict[str, str] = {
    "indices": "https://es.tradingview.com/markets/indices/quotes-all/",
    "acciones": "https://es.tradingview.com/markets/stocks-usa/",
    "cripto": "https://es.tradingview.com/markets/cryptocurrencies/",
    "forex": "https://es.tradingview.com/markets/currencies/"
}

FINVIZ_URLS: Dict[str, str] = {
    "forex": "https://finviz.com/forex.ashx",
    "acciones": "https://finviz.com/screener.ashx?v=111",
    "indices": "https://finviz.com/futures.ashx"
}

YAHOO_URLS: Dict[str, str] = {
    "forex": "https://finance.yahoo.com/currencies",
    "gainers": "https://finance.yahoo.com/markets/stocks/gainers/",
    "losers": "https://finance.yahoo.com/markets/stocks/losers/",
    "most_active_stocks": "https://finance.yahoo.com/markets/stocks/most-active/",
    "most_active_etfs": "https://finance.yahoo.com/markets/etfs/most-active/",
    "undervalued_growth": "https://finance.yahoo.com/research-hub/screener/undervalued_growth_stocks/",
    "materias_primas": "https://finance.yahoo.com/commodities",
    "indices": "https://finance.yahoo.com/world-indices"
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "financial_api.log")

# CORS Configuration - Muy Segura
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://tu-dominio.com").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"  # Más seguro deshabilitado
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,OPTIONS").split(",")  # Solo métodos necesarios
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Accept,User-Agent").split(",")  # Headers específicos
CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", "3600"))  # Cache por 1 hora

# Screenshots Configuration
SCREENSHOTS_DIR = os.getenv("SCREENSHOTS_DIR", "screenshots")
ENABLE_SCREENSHOTS = os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true" 