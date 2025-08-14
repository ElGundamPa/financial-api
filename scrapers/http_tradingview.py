import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTTPTradingViewScraper:
    """Scraper HTTP-only para TradingView (deshabilitado en Vercel)"""

    def __init__(self):
        self.base_urls = {
            "indices": "https://es.tradingview.com/markets/indices/quotes-all/",
            "acciones": "https://es.tradingview.com/markets/stocks-usa/market-movers-large-cap/",
            "cripto": "https://es.tradingview.com/markets/cryptocurrencies/",
            "forex": "https://es.tradingview.com/markets/currencies/rates-all/",
        }

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def scrape_all(
        self, http_client: httpx.AsyncClient, categories: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """Scrapear todos los datos de TradingView (solo local)"""
        logger.info("🚀 Iniciando scraping HTTP de TradingView")

        if categories:
            urls_to_scrape = {k: v for k, v in self.base_urls.items() if k in categories}
        else:
            urls_to_scrape = self.base_urls

        results = {}

        for data_type, url in urls_to_scrape.items():
            try:
                data = await self.scrape_section(http_client, url, data_type)
                results[data_type] = data
                logger.info(f"✅ TradingView {data_type}: {len(data)} elementos")
            except Exception as e:
                logger.error(f"❌ Error en TradingView {data_type}: {e}")
                results[data_type] = []

        return results

    async def scrape_section(self, http_client: httpx.AsyncClient, url: str, data_type: str) -> List[Dict[str, str]]:
        """Scrapear una sección específica"""
        try:
            response = await http_client.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            if data_type == "forex":
                return self.parse_forex_page(soup)
            elif data_type == "acciones":
                return self.parse_stocks_page(soup)
            elif data_type == "indices":
                return self.parse_indices_page(soup)
            elif data_type == "cripto":
                return self.parse_crypto_page(soup)
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Error scrapeando {data_type} de TradingView: {e}")
            return []

    def parse_forex_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de forex"""
        results = []

        # Buscar tabla de forex
        table = soup.find("table", {"class": "tv-data-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "table"})

        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:30]:  # Limitar a 30 elementos
            cells = row.find_all("td")
            if len(cells) >= 4:
                try:
                    result = {
                        "nombre": cells[0].get_text(strip=True),
                        "precio": cells[1].get_text(strip=True),
                        "cambio": cells[2].get_text(strip=True),
                        "cambio_porcentual": cells[3].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila forex: {e}")
                    continue

        return results

    def parse_stocks_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de acciones"""
        results = []

        # Buscar tabla de acciones
        table = soup.find("table", {"class": "tv-data-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "table"})

        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:50]:  # Limitar a 50 elementos
            cells = row.find_all("td")
            if len(cells) >= 6:
                try:
                    result = {
                        "nombre": cells[0].get_text(strip=True),
                        "precio": cells[1].get_text(strip=True),
                        "cambio": cells[2].get_text(strip=True),
                        "cambio_porcentual": cells[3].get_text(strip=True),
                        "volumen": cells[4].get_text(strip=True),
                        "capitalizacion": cells[5].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila acciones: {e}")
                    continue

        return results

    def parse_indices_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de índices"""
        results = []

        # Buscar tabla de índices
        table = soup.find("table", {"class": "tv-data-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "table"})

        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:30]:  # Limitar a 30 elementos
            cells = row.find_all("td")
            if len(cells) >= 5:
                try:
                    result = {
                        "nombre": cells[0].get_text(strip=True),
                        "precio": cells[1].get_text(strip=True),
                        "cambio": cells[2].get_text(strip=True),
                        "cambio_porcentual": cells[3].get_text(strip=True),
                        "volumen": cells[4].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila índices: {e}")
                    continue

        return results

    def parse_crypto_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de criptomonedas"""
        results = []

        # Buscar tabla de criptomonedas
        table = soup.find("table", {"class": "tv-data-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "table"})

        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:50]:  # Limitar a 50 elementos
            cells = row.find_all("td")
            if len(cells) >= 6:
                try:
                    result = {
                        "nombre": cells[0].get_text(strip=True),
                        "precio": cells[1].get_text(strip=True),
                        "cambio": cells[2].get_text(strip=True),
                        "cambio_porcentual": cells[3].get_text(strip=True),
                        "volumen_24h": cells[4].get_text(strip=True),
                        "capitalizacion": cells[5].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila cripto: {e}")
                    continue

        return results


# Función de conveniencia para importar desde app_core
async def scrape_tradingview(
    http_client: httpx.AsyncClient, scrape_req: Optional[Any] = None
) -> Dict[str, List[Dict[str, str]]]:
    """Función de conveniencia para scrapear TradingView (solo local)"""
    scraper = HTTPTradingViewScraper()
    categories = scrape_req.categories if scrape_req and scrape_req.categories else None
    return await scraper.scrape_all(http_client, categories)
