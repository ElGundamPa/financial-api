import asyncio
import requests
import json
import sys
from typing import Dict, Any
from scraper.tradingview import scrape_tradingview
from scraper.finviz import scrape_finviz
from scraper.yahoo import scrape_yahoo
from config import API_URL
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

async def scrape_all() -> Dict[str, Any]:
    """Scrape data from all sources concurrently"""
    log_scraping_start("Todas las fuentes")
    
    try:
        # Run Finviz and Yahoo concurrently (they are async)
        async_tasks = [
            scrape_finviz(),
            scrape_yahoo()
        ]
        
        # Run TradingView synchronously in a thread to avoid blocking
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit TradingView scraping to thread pool
            tv_future = executor.submit(scrape_tradingview)
            
            # Run async scrapers
            async_results = await asyncio.gather(*async_tasks, return_exceptions=True)
            
            # Get TradingView result
            try:
                tv = tv_future.result(timeout=120)  # 2 minutes timeout
                logger.info(f"✅ TradingView completado: {sum(len(section) for section in tv.values())} elementos")
            except Exception as e:
                logger.error(f"❌ Error en TradingView: {e}")
                tv = {}
        
        # Extract results and handle exceptions
        fz, yh = {}, {}
        
        if not isinstance(async_results[0], Exception):
            fz = async_results[0]
            logger.info(f"✅ Finviz completado: {sum(len(section) for section in fz.values())} elementos")
        else:
            logger.error(f"❌ Error en Finviz: {async_results[0]}")
            
        if not isinstance(async_results[1], Exception):
            yh = async_results[1]
            logger.info(f"✅ Yahoo completado: {sum(len(section) for section in yh.values())} elementos")
        else:
            logger.error(f"❌ Error en Yahoo: {async_results[1]}")
        
        data = {"tradingview": tv, "finviz": fz, "yahoo": yh}
        
        # Log total results
        total_items = sum(
            sum(len(section) for section in source.values()) 
            for source in data.values()
        )
        log_scraping_success("Todas las fuentes", total_items)
        
        return data
        
    except Exception as e:
        log_scraping_error("Todas las fuentes", e)
        return {"tradingview": {}, "finviz": {}, "yahoo": {}}

def send_data_to_api(data: Dict[str, Any]) -> bool:
    """Send scraped data to API"""
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Financial-Scraper-Bot/1.0"
        }
        
        logger.info(f"📤 Enviando datos a {API_URL}")
        response = requests.post(
            API_URL, 
            data=json.dumps(data, ensure_ascii=False), 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info("✅ Datos enviados correctamente a la API")
            return True
        else:
            logger.error(f"❌ Error enviando datos: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Timeout enviando datos a la API")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Error de conexión con la API")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado enviando datos: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Iniciando bot de scraping...")
    
    try:
        # Scrape all data
        data = await scrape_all()
        
        # Log data summary
        for source, source_data in data.items():
            if source_data:
                sections = list(source_data.keys())
                total_items = sum(len(section) for section in source_data.values())
                logger.info(f"📊 {source.capitalize()}: {total_items} elementos en {len(sections)} secciones")
        
        # Send to API
        success = send_data_to_api(data)
        
        if success:
            logger.info("🎉 Proceso completado exitosamente")
            sys.exit(0)
        else:
            logger.error("💥 Error enviando datos a la API")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
