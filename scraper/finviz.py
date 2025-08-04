import requests
from bs4 import BeautifulSoup
import random
import time
import asyncio
from typing import Dict, List, Any
from config import USER_AGENTS, FINVIZ_URLS, REQUEST_TIMEOUT
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

async def scrape_finviz_section(session: requests.Session, url: str, key: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from Finviz"""
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        logger.debug(f"🌐 Solicitando {url}")
        r = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "lxml")
        section = []
        
        # Different selectors for different sections
        selectors = {
            "forex": "table#screener-content-table tr",
            "acciones": "table#screener-content-table tr", 
            "indices": "table#screener-content-table tr"
        }
        
        selector = selectors.get(key, "table tr")
        rows = soup.select(selector)
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas en {key}")
            return []
        
        # Skip header row and take first 5 data rows
        data_rows = rows[1:6] if len(rows) > 1 else []
        
        for i, row in enumerate(data_rows):
            try:
                cols = row.find_all("td")
                
                if key == "forex" and len(cols) >= 3:
                    par = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if par and precio:  # Validate data
                        section.append({
                            "par": par,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Forex: {par} - {precio} - {cambio}")
                        
                elif key == "acciones" and len(cols) >= 3:
                    ticker = cols[1].text.strip()
                    nombre = cols[2].text.strip()
                    
                    if ticker:  # Validate data
                        section.append({
                            "ticker": ticker,
                            "nombre": nombre
                        })
                        logger.debug(f"📊 Acción: {ticker} - {nombre}")
                        
                elif key == "indices" and len(cols) >= 3:
                    indice = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if indice and precio:  # Validate data
                        section.append({
                            "indice": indice,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Índice: {indice} - {precio} - {cambio}")
                        
            except Exception as e:
                logger.debug(f"⚠️ Error procesando fila {i} en {key}: {e}")
                continue
        
        logger.debug(f"✅ Sección {key} procesada: {len(section)} elementos")
        return section
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout en {key}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Error de red en {key}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error inesperado en {key}: {e}")
        return []

async def scrape_finviz():
    """Main Finviz scraping function"""
    log_scraping_start("Finviz")
    
    data = {}
    session = requests.Session()
    
    try:
        # Configure session
        session.headers.update({
            "User-Agent": random.choice(USER_AGENTS)
        })
        
        for key, url in FINVIZ_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {key}")
                section_data = await scrape_finviz_section(session, url, key)
                data[key] = section_data
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                log_scraping_error(key, e)
                data[key] = []
                
    except Exception as e:
        log_scraping_error("Finviz", e)
        return {}
    finally:
        session.close()
    
    # Log success
    total_items = sum(len(section) for section in data.values())
    log_scraping_success("Finviz", total_items)
    
    return data
