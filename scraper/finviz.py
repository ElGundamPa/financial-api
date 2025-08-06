import os
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from config import USER_AGENTS, REQUEST_TIMEOUT, FINVIZ_URLS
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error
import asyncio

async def scrape_finviz_section(session: requests.Session, url: str, section_name: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from Finviz using requests"""
    try:
        logger.debug(f"🌐 Solicitando {url}")
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Selectors específicos para Finviz (corregidos basados en investigación)
        selectors = [
            "table.screener_table tbody tr",
            "table[class*='styled-table-new'] tbody tr",
            "table[class*='screener'] tbody tr",
            "table tbody tr",
            "tr[class*='table-light']",
            "tr[class*='table-dark']",
            "tbody tr",
            "table tr",
            "tr[class*='row']",
            "div[class*='table'] tbody tr",
            "table tr:not([class*='header'])"
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
        
        # Filter out navigation and header rows
        valid_rows = []
        for row in rows:
            try:
                # Skip rows that are likely navigation or headers
                row_text = row.get_text(strip=True).lower()
                if any(nav_word in row_text for nav_word in ['home', 'screener', 'portfolio', 'insider', 'calendar', 'symbol', 'name', 'price', 'no.', 'ticker', 'company']):
                    continue
                
                # Check if row has enough data
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    valid_rows.append(row)
            except Exception:
                continue
        
        if not valid_rows:
            logger.warning(f"⚠️ No se encontraron filas válidas en {section_name}")
            return []
        
        # Process valid rows (up to 100)
        max_rows = 100
        data_rows = valid_rows[:max_rows]
        
        section_data = []
        for i, row in enumerate(data_rows):
            try:
                row_data = extract_finviz_row_data(row, section_name)
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
 
def extract_finviz_row_data(row, section_name: str) -> Dict[str, str]:
    """Extract data from a Finviz table row"""
    try:
        # Skip header rows
        if row.get('class') and any('header' in cls.lower() for cls in row.get('class', [])):
            return None
        
        # Get all cells
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < 2:
            return None
        
        # Extract data based on section
        if section_name == "forex":
            # Forex: par, ticker, indice
            if len(cells) >= 3:
                par = cells[0].get_text(strip=True)
                ticker = cells[1].get_text(strip=True)
                indice = cells[2].get_text(strip=True)
                
                # Validate data
                if len(par) > 0 and len(ticker) > 0 and len(indice) > 0:
                    return {
                        "par": par,
                        "ticker": ticker,
                        "indice": indice
                    }
        
        elif section_name == "acciones":
            # Acciones: ticker, company, sector, industry, country, market_cap, pe, price, change, volume
            if len(cells) >= 5:
                ticker = cells[0].get_text(strip=True)
                company = cells[1].get_text(strip=True)
                sector = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                industry = cells[3].get_text(strip=True) if len(cells) > 3 else "N/A"
                country = cells[4].get_text(strip=True) if len(cells) > 4 else "N/A"
                
                if len(ticker) > 0 and len(company) > 0:
                    return {
                        "ticker": ticker,
                        "company": company,
                        "sector": sector,
                        "industry": industry,
                        "country": country
                    }
        
        elif section_name == "indices":
            # Índices: ticker, company, sector, industry, country, market_cap, pe, price, change, volume
            if len(cells) >= 3:
                ticker = cells[0].get_text(strip=True)
                company = cells[1].get_text(strip=True)
                price = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                
                if len(ticker) > 0 and len(company) > 0:
                    return {
                        "ticker": ticker,
                        "company": company,
                        "price": price
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
 
def scrape_finviz() -> Dict[str, List[Dict[str, str]]]:
    """Main Finviz scraping function (synchronous version)"""
    log_scraping_start("Finviz")
    
    data = {}
    session = requests.Session()
    
    try:
        # Configure session
        session.headers.update({
            "User-Agent": random.choice(USER_AGENTS)
        })
        
        for section_name, url in FINVIZ_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {section_name}")
                
                # Use synchronous version
                section_data = scrape_finviz_section_sync(session, url, section_name)
                data[section_name] = section_data
                
                # Add delay between sections
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                log_scraping_error(section_name, e)
                data[section_name] = []
                
    except Exception as e:
        log_scraping_error("Finviz", e)
        return {}
    finally:
        session.close()
    
    # Log success
    total_items = sum(len(section) for section in data.values())
    log_scraping_success("Finviz", total_items)
    
    return data
 
def scrape_finviz_section_sync(session: requests.Session, url: str, section_name: str) -> List[Dict[str, Any]]:
    """Synchronous version of scrape_finviz_section"""
    try:
        logger.debug(f"🌐 Solicitando {url}")
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Selectors específicos para Finviz (corregidos basados en investigación)
        selectors = [
            "table.screener_table tbody tr",
            "table[class*='styled-table-new'] tbody tr",
            "table[class*='screener'] tbody tr",
            "table tbody tr",
            "tr[class*='table-light']",
            "tr[class*='table-dark']",
            "tbody tr",
            "table tr",
            "tr[class*='row']",
            "div[class*='table'] tbody tr",
            "table tr:not([class*='header'])"
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
        
        # Filter out navigation and header rows
        valid_rows = []
        for row in rows:
            try:
                # Skip rows that are likely navigation or headers
                row_text = row.get_text(strip=True).lower()
                if any(nav_word in row_text for nav_word in ['home', 'screener', 'portfolio', 'insider', 'calendar', 'symbol', 'name', 'price', 'no.', 'ticker', 'company']):
                    continue
                
                # Check if row has enough data
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    valid_rows.append(row)
            except Exception:
                continue
        
        if not valid_rows:
            logger.warning(f"⚠️ No se encontraron filas válidas en {section_name}")
            return []
        
        # Process valid rows (up to 100)
        max_rows = 100
        data_rows = valid_rows[:max_rows]
        
        section_data = []
        for i, row in enumerate(data_rows):
            try:
                row_data = extract_finviz_row_data(row, section_name)
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
 
async def scrape_finviz_async():
    """Async wrapper for Finviz scraping"""
    return scrape_finviz()
