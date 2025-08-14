import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTTPYahooScraper:
    """Scraper HTTP-only para Yahoo Finance"""

    def __init__(self):
        self.base_urls = {
            "forex": "https://finance.yahoo.com/currencies",
            "gainers": "https://finance.yahoo.com/markets/stocks/gainers/",
            "losers": "https://finance.yahoo.com/markets/stocks/losers/",
            "most_active_stocks": "https://finance.yahoo.com/markets/stocks/most-active/",
            "most_active_etfs": "https://finance.yahoo.com/markets/etfs/most-active/",
            "materias_primas": "https://finance.yahoo.com/commodities",
            "indices": "https://finance.yahoo.com/quote/%5EGSPC",
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
        """Scrapear todos los datos de Yahoo Finance"""
        logger.info("🚀 Iniciando scraping HTTP de Yahoo Finance")

        if categories:
            urls_to_scrape = {k: v for k, v in self.base_urls.items() if k in categories}
        else:
            urls_to_scrape = self.base_urls

        results = {}

        for data_type, url in urls_to_scrape.items():
            try:
                data = await self.scrape_section(http_client, url, data_type)
                results[data_type] = data
                logger.info(f"✅ Yahoo {data_type}: {len(data)} elementos")
            except Exception as e:
                logger.error(f"❌ Error en Yahoo {data_type}: {e}")
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
            elif data_type in ["gainers", "losers", "most_active_stocks"]:
                return self.parse_stocks_page(soup, data_type)
            elif data_type == "most_active_etfs":
                return self.parse_etfs_page(soup)
            elif data_type == "materias_primas":
                return self.parse_commodities_page(soup)
            elif data_type == "indices":
                return self.parse_indices_page(soup)
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Error scrapeando {data_type} de Yahoo: {e}")
            return []

    def parse_forex_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de forex"""
        results = []

        # Buscar tabla de forex
        table = soup.find("table", {"data-test": "quote-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "W(100%)"})

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

    def parse_stocks_page(self, soup: BeautifulSoup, data_type: str) -> List[Dict[str, str]]:
        """Parsear página de acciones"""
        results = []

        # Buscar tabla de acciones
        table = soup.find("table", {"data-test": "quote-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "W(100%)"})

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

    def parse_etfs_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de ETFs"""
        results = []

        # Buscar tabla de ETFs
        table = soup.find("table", {"data-test": "quote-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "W(100%)"})

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
                    logger.debug(f"Error parseando fila ETFs: {e}")
                    continue

        return results

    def parse_commodities_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de materias primas"""
        results = []

        # Buscar tabla de materias primas
        table = soup.find("table", {"data-test": "quote-table"})
        if not table:
            # Intentar otros selectores
            table = soup.find("table", {"class": "W(100%)"})

        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:20]:  # Limitar a 20 elementos
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
                    logger.debug(f"Error parseando fila materias primas: {e}")
                    continue

        return results

    def parse_indices_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear página de índices (S&P 500)"""
        results = []

        try:
            # Buscar datos del S&P 500
            price_element = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})
            change_element = soup.find("fin-streamer", {"data-field": "regularMarketChange"})
            change_percent_element = soup.find("fin-streamer", {"data-field": "regularMarketChangePercent"})

            if price_element and change_element and change_percent_element:
                result = {
                    "nombre": "S&P 500",
                    "precio": price_element.get_text(strip=True),
                    "cambio": change_element.get_text(strip=True),
                    "cambio_porcentual": change_percent_element.get_text(strip=True),
                    "simbolo": "^GSPC",
                }
                results.append(result)

            # Buscar otros índices en la página
            index_elements = soup.find_all("fin-streamer", {"data-symbol": re.compile(r"\^")})

            for element in index_elements[:10]:  # Limitar a 10 índices
                try:
                    symbol = element.get("data-symbol", "")
                    price = element.get_text(strip=True)

                    if symbol and price:
                        result = {"nombre": symbol, "precio": price, "simbolo": symbol}
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando índice: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parseando página de índices: {e}")

        return results


# Función de conveniencia para importar desde app_core
async def scrape_yahoo(http_client: httpx.AsyncClient, scrape_req: Optional[Any] = None) -> Dict[str, List[Dict[str, str]]]:
    """Función de conveniencia para scrapear Yahoo Finance"""
    scraper = HTTPYahooScraper()
    categories = scrape_req.categories if scrape_req and scrape_req.categories else None
    return await scraper.scrape_all(http_client, categories)
