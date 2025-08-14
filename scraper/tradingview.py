from typing import Any, Dict, List

from bs4 import BeautifulSoup

from config import TRADINGVIEW_URLS
from logger import logger

from .base_scraper import BaseScraper


class TradingViewScraper(BaseScraper):
    def __init__(self):
        super().__init__("TradingView")

    def get_urls(self) -> Dict[str, str]:
        return TRADINGVIEW_URLS

    def get_selectors(self) -> Dict[str, List[str]]:
        return {
            "forex": ["tbody tr", "table tbody tr", "tr[class*='row']", "table tr"],
            "acciones": ["table:nth-of-type(2) tbody tr", "table:nth-of-type(2) tr", "tbody tr", "table tbody tr"],
            "indices": ["table tbody tr", "div[class*='row']", "tr[class*='row']", "table tr", "tbody tr", "tr"],
            "cripto": [
                "table.tv-data-table > tbody > tr",
                "table[class*='table'] > tbody > tr",
                "div[class*='table'] table > tbody > tr",
                "table > tbody > tr",
                "div[class*='row']",
                "div[class*='item']",
                "tr[class*='row']",
                "tbody > tr",
                "table tr",
                "[data-role='symbol']",
                ".tv-data-table__row",
                ".tv-screener__content-row",
                "[data-symbol-full]",
                "tr",
                "div[class*='symbol']",
                "div[class*='price']",
            ],
        }

    def parse_row(self, row, data_type: str) -> Dict[str, str]:
        """Parse a single row of TradingView data"""
        try:
            # Get all text elements
            cells = row.find_all(["td", "th", "div"])
            if not cells:
                return {}

            # Extract text from cells
            texts = [cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)]

            if len(texts) < 2:
                return {}

            # Common fields for all types
            result = {
                "nombre": texts[0] if texts else "",
                "precio": texts[1] if len(texts) > 1 else "",
                "cambio": texts[2] if len(texts) > 2 else "",
            }

            # Add specific fields based on data type
            if data_type == "indices":
                if len(texts) > 3:
                    result["maximo"] = texts[3]
                if len(texts) > 4:
                    result["minimo"] = texts[4]
                if len(texts) > 5:
                    result["calificacion"] = texts[5]

            elif data_type == "acciones":
                if len(texts) > 3:
                    result["volumen"] = texts[3]
                if len(texts) > 4:
                    result["capitalizacion"] = texts[4]

            elif data_type == "forex":
                if len(texts) > 3:
                    result["spread"] = texts[3]
                if len(texts) > 4:
                    result["volumen"] = texts[4]

            elif data_type == "cripto":
                if len(texts) > 3:
                    result["volumen_24h"] = texts[3]
                if len(texts) > 4:
                    result["capitalizacion"] = texts[4]
                if len(texts) > 5:
                    result["dominancia"] = texts[5]

            return result

        except Exception as e:
            logger.debug(f"⚠️ Error parseando fila de TradingView: {e}")
            return {}


# Convenience functions for backward compatibility
def scrape_tradingview() -> Dict[str, List[Dict[str, str]]]:
    """Scrape all TradingView data"""
    scraper = TradingViewScraper()
    return scraper.scrape_all()


async def scrape_tradingview_async() -> Dict[str, List[Dict[str, str]]]:
    """Async version of scrape_tradingview"""
    scraper = TradingViewScraper()
    return await scraper.scrape_all_async()
