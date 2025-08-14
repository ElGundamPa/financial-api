import asyncio
import concurrent.futures
from typing import Any, Dict, List

from cache_manager import cache_manager
from data_store import update_data
from logger import logger
from scraper.finviz import FinvizScraper
from scraper.tradingview import TradingViewScraper
from scraper.yahoo import YahooScraper


class ScraperManager:
    """Manages all scrapers with async execution and better error handling"""

    def __init__(self):
        self.scrapers = {"tradingview": TradingViewScraper(), "finviz": FinvizScraper(), "yahoo": YahooScraper()}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    async def scrape_all_async(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Scrape all sources asynchronously"""
        logger.info("🚀 Iniciando scraping asíncrono de todas las fuentes")

        # Create tasks for all scrapers
        tasks = []
        for source_name, scraper in self.scrapers.items():
            task = self.scrape_source_async(source_name, scraper)
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        scraped_data = {}
        for i, (source_name, scraper) in enumerate(self.scrapers.items()):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"❌ Error en {source_name}: {result}")
                scraped_data[source_name] = {}
            else:
                scraped_data[source_name] = result

        # Update data store
        update_data(scraped_data.get("tradingview", {}), scraped_data.get("finviz", {}), scraped_data.get("yahoo", {}))

        # Clear cache to force refresh
        cache_manager.clear()

        logger.info("✅ Scraping asíncrono completado")
        return scraped_data

    async def scrape_source_async(self, source_name: str, scraper) -> Dict[str, List[Dict[str, str]]]:
        """Scrape a single source asynchronously"""
        try:
            logger.info(f"🔄 Iniciando scraping de {source_name}")

            # Run scraper in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, scraper.scrape_all)

            logger.info(f"✅ {source_name} completado - {sum(len(data) for data in result.values())} elementos")
            return result

        except Exception as e:
            logger.error(f"❌ Error en {source_name}: {e}")
            return {}

    def scrape_all_sync(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Synchronous version for backward compatibility"""
        logger.info("🚀 Iniciando scraping síncrono de todas las fuentes")

        scraped_data = {}

        for source_name, scraper in self.scrapers.items():
            try:
                logger.info(f"🔄 Iniciando scraping de {source_name}")
                result = scraper.scrape_all()
                scraped_data[source_name] = result
                logger.info(f"✅ {source_name} completado")
            except Exception as e:
                logger.error(f"❌ Error en {source_name}: {e}")
                scraped_data[source_name] = {}

        # Update data store
        update_data(scraped_data.get("tradingview", {}), scraped_data.get("finviz", {}), scraped_data.get("yahoo", {}))

        # Clear cache to force refresh
        cache_manager.clear()

        logger.info("✅ Scraping síncrono completado")
        return scraped_data

    def scrape_single_source(self, source_name: str) -> Dict[str, List[Dict[str, str]]]:
        """Scrape a single source"""
        if source_name not in self.scrapers:
            raise ValueError(f"Fuente no válida: {source_name}")

        logger.info(f"🔄 Iniciando scraping de {source_name}")

        try:
            scraper = self.scrapers[source_name]
            result = scraper.scrape_all()
            logger.info(f"✅ {source_name} completado")
            return result
        except Exception as e:
            logger.error(f"❌ Error en {source_name}: {e}")
            return {}

    def get_available_sources(self) -> List[str]:
        """Get list of available sources"""
        return list(self.scrapers.keys())

    def get_source_info(self, source_name: str) -> Dict[str, Any]:
        """Get information about a source"""
        if source_name not in self.scrapers:
            return {}

        scraper = self.scrapers[source_name]
        urls = scraper.get_urls()
        selectors = scraper.get_selectors()

        return {
            "name": source_name,
            "available_data_types": list(urls.keys()),
            "urls": urls,
            "selectors_count": {k: len(v) for k, v in selectors.items()},
        }


# Global scraper manager instance
scraper_manager = ScraperManager()
