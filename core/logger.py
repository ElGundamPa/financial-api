import logging
import os
from datetime import datetime

from config import LOG_FILE, LOG_LEVEL


def setup_logger(name: str = "financial_api") -> logging.Logger:
    """
    Setup a logger with file and console handlers
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

    # Create formatters
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s")
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Create main logger instance
logger = setup_logger()


def log_scraping_start(source: str):
    """Log the start of a scraping operation"""
    logger.info(f"🚀 Iniciando scraping de {source}")


def log_scraping_success(source: str, data_count: int):
    """Log successful scraping operation"""
    logger.info(f"✅ Scraping de {source} completado - {data_count} elementos obtenidos")


def log_scraping_error(source: str, error: Exception):
    """Log scraping error"""
    logger.error(f"❌ Error en scraping de {source}: {str(error)}")


def log_api_request(method: str, endpoint: str, status_code: int = None):
    """Log API requests"""
    if status_code:
        logger.info(f"🌐 {method} {endpoint} - Status: {status_code}")
    else:
        logger.info(f"🌐 {method} {endpoint}")


def log_data_update(sources: list):
    """Log data update operation"""
    logger.info(f"💾 Datos actualizados desde: {', '.join(sources)}")
