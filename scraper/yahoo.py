import requests
from bs4 import BeautifulSoup
import random
import asyncio
from typing import Dict, List, Any
from config import USER_AGENTS, YAHOO_URLS, REQUEST_TIMEOUT
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

async def scrape_yahoo_section(session: requests.Session, url: str, key: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from Yahoo Finance"""
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        
        logger.debug(f"🌐 Solicitando {url}")
        r = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "lxml")
        section = []
        
        # Multiple selectors to try for Yahoo Finance tables
        selectors = [
            "table tbody tr",
            "div[data-test='fin-table'] tbody tr",
            "table[class*='table'] tbody tr",
            "div[class*='table'] tbody tr"
        ]
        
        rows = []
        for selector in selectors:
            rows = soup.select(selector)
            if rows:
                logger.debug(f"✅ Selector encontrado para {key}: {selector}")
                break
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas en {key}")
            return []
        
        # Take first 5 rows
        data_rows = rows[:5]
        
        for i, row in enumerate(data_rows):
            try:
                cols = row.find_all("td")
                
                # Different column structures for different sections
                if key == "forex" and len(cols) >= 3:
                    nombre = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if nombre and precio:  # Validate data
                        section.append({
                            "nombre": nombre,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Forex: {nombre} - {precio} - {cambio}")
                        
                elif key == "acciones" and len(cols) >= 3:
                    nombre = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if nombre and precio:  # Validate data
                        section.append({
                            "nombre": nombre,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Acción: {nombre} - {precio} - {cambio}")
                        
                elif key == "materias_primas" and len(cols) >= 3:
                    nombre = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if nombre and precio:  # Validate data
                        section.append({
                            "nombre": nombre,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Materia prima: {nombre} - {precio} - {cambio}")
                        
                elif key == "indices" and len(cols) >= 3:
                    nombre = cols[0].text.strip()
                    precio = cols[1].text.strip()
                    cambio = cols[2].text.strip()
                    
                    if nombre and precio:  # Validate data
                        section.append({
                            "nombre": nombre,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Índice: {nombre} - {precio} - {cambio}")
                        
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

async def scrape_yahoo():
    """Main Yahoo Finance scraping function"""
    log_scraping_start("Yahoo Finance")
    
    data = {}
    session = requests.Session()
    
    try:
        # Configure session
        session.headers.update({
            "User-Agent": random.choice(USER_AGENTS)
        })
        
        for key, url in YAHOO_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {key}")
                section_data = await scrape_yahoo_section(session, url, key)
                data[key] = section_data
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                log_scraping_error(key, e)
                data[key] = []
                
    except Exception as e:
        log_scraping_error("Yahoo Finance", e)
        return {}
    finally:
        session.close()
    
    # Log success
    total_items = sum(len(section) for section in data.values())
    log_scraping_success("Yahoo Finance", total_items)
    
    return data
