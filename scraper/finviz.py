import requests
from bs4 import BeautifulSoup
import random
import time
import asyncio
from typing import Dict, List, Any
from config import USER_AGENTS, FINVIZ_URLS, REQUEST_TIMEOUT
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

async def scrape_finviz_section(session: requests.Session, url: str, key: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from Finviz with improved selectors"""
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        
        logger.debug(f"🌐 Solicitando {url}")
        r = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "lxml")
        section = []
        
        # Selectors mejorados para Finviz
        selectors = {
            "forex": [
                "table#screener-content-table tr",
                "table.table-light tr",
                "table tr",
                ".table-light tr",
                "tr[class*='table-light']",
                "tbody tr"
            ],
            "acciones": [
                "table#screener-content-table tr",
                "table.table-light tr", 
                "table tr",
                ".table-light tr",
                "tr[class*='table-light']",
                "tbody tr"
            ],
            "indices": [
                "table#screener-content-table tr",
                "table.table-light tr",
                "table tr",
                ".table-light tr",
                "tr[class*='table-light']",
                "tbody tr"
            ]
        }
        
        rows = []
        selector_list = selectors.get(key, ["table tr"])
        
        # Intentar diferentes selectores con mejor lógica
        for selector in selector_list:
            try:
                found_rows = soup.select(selector)
                if found_rows and len(found_rows) > 2:  # Más de 2 para excluir headers
                    rows = found_rows
                    logger.debug(f"✅ Selector encontrado para {key}: {selector} - {len(rows)} filas")
                    break
            except Exception as e:
                logger.debug(f"⚠️ Error con selector {selector}: {e}")
                continue
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas en {key}")
            return []
        
        # Skip header rows and process all data rows (máximo 100)
        data_rows = rows[1:101] if len(rows) > 1 else []
        
        for i, row in enumerate(data_rows):
            try:
                cols = row.find_all("td")
                
                if key == "forex" and len(cols) >= 3:
                    par = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if par and precio and par != "Symbol":  # Validate data and skip headers
                        section.append({
                            "par": par,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Forex: {par} - {precio} - {cambio}")
                        
                elif key == "acciones" and len(cols) >= 4:
                    ticker = cols[1].text.strip() if len(cols) > 1 else ""
                    nombre = cols[2].text.strip() if len(cols) > 2 else ""
                    precio = cols[3].text.strip() if len(cols) > 3 else ""
                    cambio = cols[4].text.strip() if len(cols) > 4 else ""
                    
                    if ticker and ticker != "No.":  # Validate data and skip headers
                        section.append({
                            "ticker": ticker,
                            "nombre": nombre,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Acción: {ticker} - {nombre} - {precio}")
                        
                elif key == "indices" and len(cols) >= 3:
                    indice = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if indice and precio and indice != "Index":  # Validate data and skip headers
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
    """Main Finviz scraping function with improved error handling"""
    log_scraping_start("Finviz")
    
    data = {}
    session = requests.Session()
    
    try:
        # Configure session with better headers
        session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        for key, url in FINVIZ_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {key}")
                section_data = await scrape_finviz_section(session, url, key)
                data[key] = section_data
                
                # Add delay between requests to avoid rate limiting
                await asyncio.sleep(random.uniform(3, 6))
                
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
