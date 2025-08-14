import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTTPFinvizScraper:
    """Scraper HTTP-only para Finviz"""

    def __init__(self):
        self.base_urls = {
            "forex": "https://finviz.com/forex.ashx",
            "acciones": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=cap_large",
            "indices": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=idx_sp500",
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
        """Scrapear todos los datos de Finviz"""
        logger.info("🚀 Iniciando scraping HTTP de Finviz")

        if categories:
            urls_to_scrape = {k: v for k, v in self.base_urls.items() if k in categories}
        else:
            urls_to_scrape = self.base_urls

        results = {}

        for data_type, url in urls_to_scrape.items():
            try:
                data = await self.scrape_section(http_client, url, data_type)
                results[data_type] = data
                logger.info(f"✅ Finviz {data_type}: {len(data)} elementos")
            except Exception as e:
                logger.error(f"❌ Error en Finviz {data_type}: {e}")
                results[data_type] = []

        return results

    async def scrape_section(self, http_client: httpx.AsyncClient, url: str, data_type: str) -> List[Dict[str, str]]:
        """Scrapear una sección específica"""
        try:
            response = await http_client.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            if data_type == "forex":
                return self.parse_forex_table(soup)
            elif data_type == "acciones":
                return self.parse_stocks_table(soup)
            elif data_type == "indices":
                return self.parse_indices_table(soup)
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Error scrapeando {data_type} de Finviz: {e}")
            return []

    def parse_forex_table(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear tabla de forex"""
        results = []

        # Buscar tabla de forex
        table = soup.find("table", {"class": "table-light"})
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
                        "maximo": cells[4].get_text(strip=True),
                        "minimo": cells[5].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila forex: {e}")
                    continue

        return results

    def parse_stocks_table(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear tabla de acciones"""
        results = []

        # Buscar tabla de acciones
        table = soup.find("table", {"class": "table-light"})
        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:50]:  # Limitar a 50 elementos
            cells = row.find_all("td")
            if len(cells) >= 8:
                try:
                    result = {
                        "nombre": cells[1].get_text(strip=True),
                        "precio": cells[2].get_text(strip=True),
                        "cambio": cells[3].get_text(strip=True),
                        "cambio_porcentual": cells[4].get_text(strip=True),
                        "volumen": cells[5].get_text(strip=True),
                        "capitalizacion": cells[6].get_text(strip=True),
                        "pe_ratio": cells[7].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila acciones: {e}")
                    continue

        return results

    def parse_indices_table(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parsear tabla de índices"""
        results = []

        # Buscar tabla de índices
        table = soup.find("table", {"class": "table-light"})
        if not table:
            return results

        rows = table.find_all("tr")[1:]  # Skip header

        for row in rows[:30]:  # Limitar a 30 elementos
            cells = row.find_all("td")
            if len(cells) >= 6:
                try:
                    result = {
                        "nombre": cells[1].get_text(strip=True),
                        "precio": cells[2].get_text(strip=True),
                        "cambio": cells[3].get_text(strip=True),
                        "cambio_porcentual": cells[4].get_text(strip=True),
                        "volumen": cells[5].get_text(strip=True),
                    }
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error parseando fila índices: {e}")
                    continue

        return results


# Función de conveniencia para importar desde app_core
async def scrape_finviz(http_client: httpx.AsyncClient, scrape_req: Optional[Any] = None) -> Dict[str, List[Dict[str, str]]]:
    """Función de conveniencia para scrapear Finviz"""
    scraper = HTTPFinvizScraper()
    categories = scrape_req.categories if scrape_req and scrape_req.categories else None
    return await scraper.scrape_all(http_client, categories)
