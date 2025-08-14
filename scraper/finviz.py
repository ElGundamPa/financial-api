import asyncio
import os
import random
import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from config import FINVIZ_URLS, REQUEST_TIMEOUT, USER_AGENTS
from logger import log_scraping_error, log_scraping_start, log_scraping_success, logger

from .base_scraper import BaseScraper


class FinvizScraper(BaseScraper):
    def __init__(self):
        super().__init__("Finviz")

    def get_urls(self) -> Dict[str, str]:
        return FINVIZ_URLS

    def get_selectors(self) -> Dict[str, List[str]]:
        return {
            "forex": ["table.table-light tbody tr", "table tbody tr", "tr[class*='table']", "table tr"],
            "acciones": ["table.table-light tbody tr", "table tbody tr", "tr[class*='table']", "table tr"],
            "indices": ["table.table-light tbody tr", "table tbody tr", "tr[class*='table']", "table tr"],
        }

    def parse_row(self, row, data_type: str) -> Dict[str, str]:
        try:
            cells = row.find_all("td")
            if len(cells) < 6:
                return {}

            return {
                "symbol": cells[0].get_text(strip=True) if cells[0] else "",
                "name": cells[1].get_text(strip=True) if len(cells) > 1 and cells[1] else "",
                "price": cells[2].get_text(strip=True) if len(cells) > 2 and cells[2] else "",
                "change": cells[3].get_text(strip=True) if len(cells) > 3 and cells[3] else "",
                "change_percent": cells[4].get_text(strip=True) if len(cells) > 4 and cells[4] else "",
                "volume": cells[5].get_text(strip=True) if len(cells) > 5 and cells[5] else "",
            }
        except Exception as e:
            logger.error(f"Error parsing Finviz row: {e}")
            return {}


def scrape_finviz() -> Dict[str, List[Dict[str, str]]]:
    scraper = FinvizScraper()
    return scraper.scrape_all()


async def scrape_finviz_async() -> Dict[str, List[Dict[str, str]]]:
    scraper = FinvizScraper()
    return await scraper.scrape_all_async()
