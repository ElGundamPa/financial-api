import asyncio
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT, USER_AGENTS
from logger import logger


class BaseScraper(ABC):
    """Base class for all scrapers to eliminate code duplication"""

    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "DNT": "1",
            }
        )

    @abstractmethod
    def get_urls(self) -> Dict[str, str]:
        """Return URLs for different data types"""
        pass

    @abstractmethod
    def get_selectors(self) -> Dict[str, List[str]]:
        """Return CSS selectors for different data types"""
        pass

    @abstractmethod
    def parse_row(self, row, data_type: str) -> Dict[str, str]:
        """Parse a single row of data"""
        pass

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.debug(f"🌐 {self.name}: Solicitando {url} (intento {attempt + 1})")

                # Rotate User-Agent
                self.session.headers["User-Agent"] = random.choice(USER_AGENTS)

                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                logger.debug(f"✅ {self.name}: Página obtenida exitosamente")
                return soup

            except Exception as e:
                logger.warning(f"⚠️ {self.name}: Error en intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ {self.name}: Falló después de {max_retries} intentos")
                    return None

    def find_rows(self, soup: BeautifulSoup, data_type: str) -> List:
        """Find data rows using multiple selectors"""
        selectors = self.get_selectors().get(data_type, [])

        for selector in selectors:
            try:
                rows = soup.select(selector)
                if rows and len(rows) > 0:
                    logger.debug(f"✅ {self.name}: Selector encontrado para {data_type}: {selector} - {len(rows)} filas")
                    return rows
            except Exception as e:
                logger.debug(f"⚠️ {self.name}: Error con selector {selector}: {e}")
                continue

        logger.warning(f"⚠️ {self.name}: No se encontraron filas para {data_type}")
        return []

    def scrape_section(self, url: str, data_type: str, max_rows: int = 200) -> List[Dict[str, str]]:
        """Scrape a specific section"""
        logger.info(f"🚀 {self.name}: Iniciando scraping de {data_type}")

        soup = self.get_page_content(url)
        if not soup:
            return []

        rows = self.find_rows(soup, data_type)
        if not rows:
            return []

        # Limit rows
        data_rows = rows[:max_rows]
        results = []

        for row in data_rows:
            try:
                parsed_data = self.parse_row(row, data_type)
                if parsed_data:
                    results.append(parsed_data)
            except Exception as e:
                logger.debug(f"⚠️ {self.name}: Error parseando fila: {e}")
                continue

        logger.info(f"✅ {self.name}: {data_type} completado - {len(results)} elementos")
        return results

    def scrape_all(self) -> Dict[str, List[Dict[str, str]]]:
        """Scrape all data types"""
        logger.info(f"🚀 {self.name}: Iniciando scraping completo")

        urls = self.get_urls()
        results = {}

        for data_type, url in urls.items():
            try:
                data = self.scrape_section(url, data_type)
                results[data_type] = data
            except Exception as e:
                logger.error(f"❌ {self.name}: Error en {data_type}: {e}")
                results[data_type] = []

        logger.info(f"✅ {self.name}: Scraping completo finalizado")
        return results

    async def scrape_all_async(self) -> Dict[str, List[Dict[str, str]]]:
        """Async version of scrape_all"""
        # For now, run sync version in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scrape_all)
