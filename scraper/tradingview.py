import os
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from config import USER_AGENTS, REQUEST_TIMEOUT, TRADINGVIEW_URLS
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error
import asyncio

async def scrape_tradingview_section(session: requests.Session, url: str, section_name: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from TradingView using requests"""
    try:
        logger.debug(f"🌐 Solicitando {url}")
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1"
        }
        
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Selectors específicos basados en la investigación real
        if section_name == "forex":
            # Para forex: usar tbody tr que funciona perfectamente
            selectors = [
                "tbody tr",
                "table tbody tr",
                "tr[class*='row']",
                "table tr"
            ]
        elif section_name == "acciones":
            # Para acciones: usar la segunda tabla que contiene los datos
            selectors = [
                "table:nth-of-type(2) tbody tr",
                "table:nth-of-type(2) tr",
                "tbody tr",
                "table tbody tr"
            ]
        elif section_name == "indices":
            # Para índices: mantener los selectors que funcionan
            selectors = [
                "table tbody tr",
                "div[class*='row']",
                "tr[class*='row']",
                "table tr",
                "tbody tr",
                "tr"
            ]
        else:
            # Para otras secciones
            selectors = [
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
                "div[class*='price']"
            ]
        
        rows = []
        for selector in selectors:
            try:
                found_rows = soup.select(selector)
                if found_rows and len(found_rows) > 0:
                    rows = found_rows
                    logger.debug(f"✅ Selector encontrado para {section_name}: {selector} - {len(rows)} filas")
                    break
            except Exception as e:
                logger.debug(f"⚠️ Error con selector {selector}: {e}")
                continue
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas en {section_name}")
            return []
        
        # Process all rows (no limit for indices, up to 200 for others)
        max_rows = 1000 if section_name == "indices" else 200
        data_rows = rows[:max_rows]
        
        section_data = []
        for i, row in enumerate(data_rows):
            try:
                row_data = extract_row_data_improved(row, section_name)
                if row_data:
                    section_data.append(row_data)
            except Exception as e:
                logger.debug(f"⚠️ Error procesando fila {i} en {section_name}: {e}")
                continue
        
        logger.debug(f"✅ Sección {section_name} procesada: {len(section_data)} elementos")
        return section_data
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout en {section_name}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Error de red en {section_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error inesperado en {section_name}: {e}")
        return []

def extract_row_data_improved(row, section_name: str) -> Dict[str, str]:
    """Extract data from a TradingView table row with improved logic"""
    try:
        # Skip header rows
        if row.get('class') and any('header' in cls.lower() for cls in row.get('class', [])):
            return None
        
        # Get all cells (td or th)
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < 2:
            return None
        
        # Extract data based on section
        if section_name == "forex":
            # Forex: nombre, precio, cambio_porcentaje, cambio, maximo, minimo, calificacion
            if len(cells) >= 7:
                return {
                    "nombre": cells[0].get_text(strip=True),
                    "precio": cells[1].get_text(strip=True),
                    "cambio_porcentaje": cells[2].get_text(strip=True),
                    "cambio": cells[3].get_text(strip=True),
                    "maximo": cells[4].get_text(strip=True),
                    "minimo": cells[5].get_text(strip=True),
                    "calificacion": cells[6].get_text(strip=True)
                }
            elif len(cells) >= 4:
                return {
                    "nombre": cells[0].get_text(strip=True),
                    "precio": cells[1].get_text(strip=True),
                    "cambio_porcentaje": cells[2].get_text(strip=True),
                    "cambio": cells[3].get_text(strip=True),
                    "maximo": "N/A",
                    "minimo": "N/A",
                    "calificacion": "N/A"
                }
        
        elif section_name == "acciones":
            # Acciones: nombre, capitalizacion, precio, cambio, volumen
            if len(cells) >= 5:
                return {
                    "nombre": cells[0].get_text(strip=True),
                    "capitalizacion": cells[1].get_text(strip=True),
                    "precio": cells[2].get_text(strip=True),
                    "cambio": cells[3].get_text(strip=True),
                    "volumen": cells[4].get_text(strip=True)
                }
            elif len(cells) >= 3:
                return {
                    "nombre": cells[0].get_text(strip=True),
                    "precio": cells[1].get_text(strip=True),
                    "cambio": cells[2].get_text(strip=True),
                    "capitalizacion": "N/A",
                    "volumen": "N/A"
                }
        
        elif section_name == "indices":
            # Índices: nombre, precio, cambio, maximo, minimo, calificacion
            if len(cells) >= 6:
                return {
                    "nombre": cells[0].get_text(strip=True),
                    "precio": cells[1].get_text(strip=True),
                    "cambio": cells[2].get_text(strip=True),
                    "maximo": cells[3].get_text(strip=True),
                    "minimo": cells[4].get_text(strip=True),
                    "calificacion": cells[5].get_text(strip=True)
                }
            elif len(cells) >= 3:
                return {
                    "nombre": cells[0].get_text(strip=True),
                    "precio": cells[1].get_text(strip=True),
                    "cambio": cells[2].get_text(strip=True),
                    "maximo": "N/A",
                    "minimo": "N/A",
                    "calificacion": "N/A"
                }
        
        else:
            # Generic extraction for other sections
            data = {}
            for i, cell in enumerate(cells[:6]):  # Max 6 columns
                data[f"col_{i+1}"] = cell.get_text(strip=True)
            return data
        
    except Exception as e:
        logger.debug(f"⚠️ Error extrayendo datos de fila: {e}")
        return None

def scrape_tradingview() -> Dict[str, List[Dict[str, str]]]:
    """Main TradingView scraping function (synchronous version)"""
    log_scraping_start("TradingView")
    
    data = {}
    session = requests.Session()
    
    try:
        # Configure session
        session.headers.update({
            "User-Agent": random.choice(USER_AGENTS)
        })
        
        for section_name, url in TRADINGVIEW_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {section_name}")
                
                # Use synchronous version
                section_data = scrape_tradingview_section_sync(session, url, section_name)
                data[section_name] = section_data
                
                # Add delay between sections
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                log_scraping_error(section_name, e)
                data[section_name] = []
                
    except Exception as e:
        log_scraping_error("TradingView", e)
        return {}
    finally:
        session.close()
    
    # Log success
    total_items = sum(len(section) for section in data.values())
    log_scraping_success("TradingView", total_items)
    
    return data

def scrape_tradingview_section_sync(session: requests.Session, url: str, section_name: str) -> List[Dict[str, Any]]:
    """Synchronous version of scrape_tradingview_section"""
    try:
        logger.debug(f"🌐 Solicitando {url}")
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1"
        }
        
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Selectors específicos basados en la investigación real
        if section_name == "forex":
            selectors = ["tbody tr", "table tbody tr", "tr[class*='row']", "table tr"]
        elif section_name == "acciones":
            selectors = ["table:nth-of-type(2) tbody tr", "table:nth-of-type(2) tr", "tbody tr", "table tbody tr"]
        elif section_name == "indices":
            selectors = ["table tbody tr", "div[class*='row']", "tr[class*='row']", "table tr", "tbody tr", "tr"]
        else:
            selectors = ["table tbody tr", "div[class*='row']", "tr[class*='row']", "tbody tr", "table tr"]
        
        rows = []
        for selector in selectors:
            try:
                found_rows = soup.select(selector)
                if found_rows and len(found_rows) > 0:
                    rows = found_rows
                    logger.debug(f"✅ Selector encontrado para {section_name}: {selector} - {len(rows)} filas")
                    break
            except Exception as e:
                logger.debug(f"⚠️ Error con selector {selector}: {e}")
                continue
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas en {section_name}")
            return []
        
        # Process all rows
        max_rows = 1000 if section_name == "indices" else 200
        data_rows = rows[:max_rows]
        
        section_data = []
        for i, row in enumerate(data_rows):
            try:
                row_data = extract_row_data_improved(row, section_name)
                if row_data:
                    section_data.append(row_data)
            except Exception as e:
                logger.debug(f"⚠️ Error procesando fila {i} en {section_name}: {e}")
                continue
        
        logger.debug(f"✅ Sección {section_name} procesada: {len(section_data)} elementos")
        return section_data
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout en {section_name}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Error de red en {section_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error inesperado en {section_name}: {e}")
        return []

async def scrape_tradingview_async():
    """Async wrapper for TradingView scraping"""
    return scrape_tradingview()
