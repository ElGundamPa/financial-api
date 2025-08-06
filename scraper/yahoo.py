import requests
from bs4 import BeautifulSoup
import random
import asyncio
from typing import Dict, List, Any
from config import USER_AGENTS, YAHOO_URLS, REQUEST_TIMEOUT
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

async def scrape_yahoo_paginated_section(session: requests.Session, base_url: str, key: str, max_pages: int = 10) -> List[Dict[str, Any]]:
    """Scrape a paginated section from Yahoo Finance"""
    all_data = []
    
    try:
        for page in range(1, max_pages + 1):
            try:
                # Construir URL con parámetros de página
                if "?" in base_url:
                    page_url = f"{base_url}&offset={(page-1)*100}"
                else:
                    page_url = f"{base_url}?offset={(page-1)*100}"
                
                logger.debug(f"🌐 Procesando página {page} de {key}: {page_url}")
                
                headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
                
                r = session.get(page_url, headers=headers, timeout=REQUEST_TIMEOUT)
                r.raise_for_status()
                
                soup = BeautifulSoup(r.text, "lxml")
                
                # Selectors específicos para Yahoo Finance
                selectors = [
                    "table tbody tr",
                    "div[data-test='fin-table'] tbody tr",
                    "table[class*='table'] tbody tr",
                    "div[class*='table'] tbody tr",
                    "tr[class*='simpTblRow']",
                    "tbody tr"
                ]
                
                rows = []
                for selector in selectors:
                    rows = soup.select(selector)
                    if rows and len(rows) > 0:
                        logger.debug(f"✅ Selector encontrado para {key} página {page}: {selector} - {len(rows)} filas")
                        break
                
                if not rows:
                    logger.warning(f"⚠️ No se encontraron filas en {key} página {page}")
                    break  # Si no hay datos, probablemente llegamos al final
                
                page_data = []
                for i, row in enumerate(rows):
                    try:
                        row_data = extract_yahoo_row_data(row, key)
                        if row_data:
                            page_data.append(row_data)
                    except Exception as e:
                        logger.debug(f"⚠️ Error procesando fila {i} en {key} página {page}: {e}")
                        continue
                
                if not page_data:
                    logger.warning(f"⚠️ No se extrajeron datos de {key} página {page}")
                    break  # Si no hay datos válidos, terminar
                
                all_data.extend(page_data)
                logger.debug(f"📊 Página {page} de {key}: {len(page_data)} elementos")
                
                # Delay entre páginas
                await asyncio.sleep(random.uniform(1, 3))
                
            except requests.exceptions.Timeout:
                logger.error(f"⏰ Timeout en {key} página {page}")
                break
            except requests.exceptions.RequestException as e:
                logger.error(f"🌐 Error de red en {key} página {page}: {e}")
                break
            except Exception as e:
                logger.error(f"❌ Error inesperado en {key} página {page}: {e}")
                break
        
        logger.info(f"✅ Sección {key} completada: {len(all_data)} elementos totales")
        return all_data
        
    except Exception as e:
        logger.error(f"❌ Error procesando sección {key}: {e}")
        return all_data

def extract_yahoo_row_data(row, key: str) -> Dict[str, Any]:
    """Extract data from a Yahoo Finance table row"""
    try:
        cols = row.find_all("td")
        
        if len(cols) < 2:
            return None
        
        # Extraer datos según el tipo de sección
        if key == "gainers":
            return extract_gainers_data(cols)
        elif key == "losers":
            return extract_losers_data(cols)
        elif key == "most_active_stocks":
            return extract_most_active_data(cols)
        elif key == "most_active_etfs":
            return extract_etf_data(cols)
        elif key == "undervalued_growth":
            return extract_undervalued_data(cols)
        elif key == "forex":
            return extract_forex_data(cols)
        elif key == "materias_primas":
            return extract_commodities_data(cols)
        elif key == "indices":
            return extract_indices_data(cols)
        else:
            return extract_generic_data(cols)
            
    except Exception as e:
        logger.debug(f"⚠️ Error extrayendo datos de fila: {e}")
        return None

def extract_gainers_data(cols) -> Dict[str, Any]:
    """Extract data from gainers table"""
    try:
        if len(cols) >= 6:
            return {
                "symbol": cols[0].text.strip(),
                "name": cols[1].text.strip(),
                "price": cols[2].text.strip(),
                "change": cols[3].text.strip(),
                "change_percent": cols[4].text.strip(),
                "volume": cols[5].text.strip() if len(cols) > 5 else "N/A"
            }
        elif len(cols) >= 4:
            return {
                "symbol": cols[0].text.strip(),
                "price": cols[1].text.strip(),
                "change": cols[2].text.strip(),
                "change_percent": cols[3].text.strip()
            }
    except Exception:
        pass
    return None

def extract_losers_data(cols) -> Dict[str, Any]:
    """Extract data from losers table"""
    return extract_gainers_data(cols)  # Misma estructura

def extract_most_active_data(cols) -> Dict[str, Any]:
    """Extract data from most active stocks table"""
    try:
        if len(cols) >= 6:
            return {
                "symbol": cols[0].text.strip(),
                "name": cols[1].text.strip(),
                "price": cols[2].text.strip(),
                "change": cols[3].text.strip(),
                "change_percent": cols[4].text.strip(),
                "volume": cols[5].text.strip()
            }
        elif len(cols) >= 4:
            return {
                "symbol": cols[0].text.strip(),
                "price": cols[1].text.strip(),
                "change": cols[2].text.strip(),
                "change_percent": cols[3].text.strip()
            }
    except Exception:
        pass
    return None

def extract_etf_data(cols) -> Dict[str, Any]:
    """Extract data from ETF table"""
    return extract_most_active_data(cols)  # Misma estructura

def extract_undervalued_data(cols) -> Dict[str, Any]:
    """Extract data from undervalued growth stocks table"""
    try:
        if len(cols) >= 5:
            return {
                "symbol": cols[0].text.strip(),
                "name": cols[1].text.strip(),
                "price": cols[2].text.strip(),
                "pe_ratio": cols[3].text.strip(),
                "market_cap": cols[4].text.strip()
            }
        elif len(cols) >= 3:
            return {
                "symbol": cols[0].text.strip(),
                "price": cols[1].text.strip(),
                "pe_ratio": cols[2].text.strip()
            }
    except Exception:
        pass
    return None

def extract_forex_data(cols) -> Dict[str, Any]:
    """Extract data from forex table"""
    try:
        if len(cols) >= 3:
            return {
                "pair": cols[0].text.strip(),
                "price": cols[1].text.strip(),
                "change": cols[2].text.strip()
            }
    except Exception:
        pass
    return None

def extract_commodities_data(cols) -> Dict[str, Any]:
    """Extract data from commodities table"""
    return extract_forex_data(cols)  # Misma estructura

def extract_indices_data(cols) -> Dict[str, Any]:
    """Extract data from indices table"""
    return extract_forex_data(cols)  # Misma estructura

def extract_generic_data(cols) -> Dict[str, Any]:
    """Extract generic data from any table"""
    try:
        data = {}
        for i, col in enumerate(cols[:6]):  # Máximo 6 columnas
            data[f"col_{i+1}"] = col.text.strip()
        return data
    except Exception:
        return None

async def scrape_yahoo_section(session: requests.Session, url: str, key: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from Yahoo Finance (non-paginated)"""
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        logger.debug(f"🌐 Solicitando {url}")
        r = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "lxml")
        
        # Selectors para páginas no paginadas
        selectors = [
            "table tbody tr",
            "div[data-test='fin-table'] tbody tr",
            "table[class*='table'] tbody tr",
            "div[class*='table'] tbody tr",
            "tr[class*='simpTblRow']",
            "tbody tr"
        ]
        
        rows = []
        for selector in selectors:
            rows = soup.select(selector)
            if rows and len(rows) > 0:
                logger.debug(f"✅ Selector encontrado para {key}: {selector} - {len(rows)} filas")
                break
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas en {key}")
            return []
        
        # Procesar todas las filas (máximo 50)
        data_rows = rows[:50]
        section_data = []
        
        for i, row in enumerate(data_rows):
            try:
                row_data = extract_yahoo_row_data(row, key)
                if row_data:
                    section_data.append(row_data)
            except Exception as e:
                logger.debug(f"⚠️ Error procesando fila {i} en {key}: {e}")
                continue
        
        logger.debug(f"✅ Sección {key} procesada: {len(section_data)} elementos")
        return section_data
        
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
        
        # Configurar páginas máximas para cada sección
        paginated_sections = {
            "gainers": 149,      # 149 páginas
            "losers": 148,       # 148 páginas
            "most_active_stocks": 50,  # Máximo 50 páginas
            "most_active_etfs": 50,    # Máximo 50 páginas
            "undervalued_growth": 20   # Máximo 20 páginas
        }
        
        for key, url in YAHOO_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {key}")
                
                if key in paginated_sections:
                    # Sección paginada
                    section_data = await scrape_yahoo_paginated_section(
                        session, url, key, paginated_sections[key]
                    )
                else:
                    # Sección no paginada
                    section_data = await scrape_yahoo_section(session, url, key)
                
                data[key] = section_data
                
                # Add delay between sections
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
