import os
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from config import USER_AGENTS, REQUEST_TIMEOUT
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

# URLs específicas para cada sección (actualizadas)
TRADINGVIEW_URLS = {
    "indices": "https://www.tradingview.com/markets/stocks-usa/sectorandindustry-sector/",
    "acciones": "https://www.tradingview.com/markets/stocks-usa/",
    "cripto": "https://www.tradingview.com/markets/cryptocurrencies/",
    "forex": "https://www.tradingview.com/markets/currencies/rates-major/"
}

def scrape_tradingview_section(session, url: str, section_name: str) -> List[Dict[str, str]]:
    """
    Scrape a specific section from TradingView using requests and BeautifulSoup
    """
    try:
        logger.info(f"🔄 Procesando sección: {section_name}")
        logger.debug(f"🌐 Navegando a {url}")
        
        # Prepare headers for the request
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        # Make the request with increased timeout for TradingView
        response = session.get(url, headers=headers, timeout=30)  # 30 seconds timeout
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Take screenshot for debugging if enabled
        if os.getenv("ENABLE_SCREENSHOTS", "false").lower() == "true":
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = os.path.join("screenshots", f"tradingview_{section_name}.html")
            with open(screenshot_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.debug(f"📸 HTML guardado: {screenshot_path}")

        # Multiple selector strategies for different page layouts
        selectors = [
            # Primary selectors for data tables
            "table.tv-data-table > tbody > tr",
            "table[class*='table'] > tbody > tr",
            "div[class*='table'] table > tbody > tr",
            "table > tbody > tr",
            # Alternative selectors for different layouts
            "div[class*='row']",
            "div[class*='item']",
            "tr[class*='row']",
            # Generic selectors as fallback
            "tbody > tr",
            "table tr",
            # Additional selectors for TradingView
            "[data-role='symbol']",
            ".tv-data-table__row",
            ".tv-screener__content-row",
            # More specific TradingView selectors
            ".tv-screener__content-row",
            ".tv-data-table__row",
            "[data-symbol-full]",
            ".tv-screener__content-row",
            # Fallback for any table-like structure
            "tr",
            "div[class*='symbol']",
            "div[class*='price']"
        ]
        
        rows = []
        used_selector = None
        
        # Try different selectors until we find data
        for selector in selectors:
            try:
                elements = soup.select(selector)
                
                if elements and len(elements) > 0:
                    used_selector = selector
                    rows = elements
                    logger.debug(f"✅ Selector encontrado: {selector} - {len(rows)} filas")
                    break
                    
            except Exception as e:
                logger.debug(f"⚠️ Error con selector {selector}: {e}")
                continue
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas de datos en {section_name}")
            return []

        data = []
        processed_count = 0
        
        # Process first 5 rows
        for i, row in enumerate(rows[:5]):
            try:
                # Try different cell extraction strategies
                cells = row.find_all("td")
                
                if len(cells) >= 3:
                    # Standard table format
                    nombre = cells[0].get_text(strip=True)
                    precio = cells[1].get_text(strip=True)
                    cambio = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                    
                elif len(cells) == 2:
                    # Two-column format
                    nombre = cells[0].get_text(strip=True)
                    precio = cells[1].get_text(strip=True)
                    cambio = "N/A"
                    
                else:
                    # Try to extract from div elements
                    divs = row.find_all("div")
                    if len(divs) >= 2:
                        nombre = divs[0].get_text(strip=True)
                        precio = divs[1].get_text(strip=True)
                        cambio = divs[2].get_text(strip=True) if len(divs) > 2 else "N/A"
                    else:
                        # Fallback: extract all text
                        text = row.get_text(strip=True)
                        parts = text.split()
                        if len(parts) >= 2:
                            nombre = parts[0]
                            precio = parts[1]
                            cambio = parts[2] if len(parts) > 2 else "N/A"
                        else:
                            continue
                
                # Validate and clean data
                if nombre and precio and len(nombre) > 0:
                    # Clean up the data
                    nombre = nombre.replace('\n', ' ').replace('\t', ' ').strip()
                    precio = precio.replace('\n', ' ').replace('\t', ' ').strip()
                    cambio = cambio.replace('\n', ' ').replace('\t', ' ').strip()
                    
                    # Limit string lengths
                    nombre = nombre[:50] if len(nombre) > 50 else nombre
                    precio = precio[:20] if len(precio) > 20 else precio
                    cambio = cambio[:20] if len(cambio) > 20 else cambio
                    
                    data.append({
                        "nombre": nombre,
                        "precio": precio,
                        "cambio": cambio
                    })
                    processed_count += 1
                    logger.debug(f"📊 Datos extraídos: {nombre} - {precio} - {cambio}")
                    
            except Exception as e:
                logger.debug(f"⚠️ Error procesando fila {i}: {e}")
                continue
        
        logger.info(f"✅ Sección {section_name} procesada: {processed_count} elementos")
        return data
        
    except requests.exceptions.Timeout as e:
        logger.error(f"⏰ Timeout en {section_name}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de red en {section_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error inesperado en {section_name}: {e}")
        return []

def scrape_tradingview() -> Dict[str, List[Dict[str, str]]]:
    """
    Main TradingView scraping function using requests and BeautifulSoup
    Returns: {
        "indices": [...],
        "acciones": [...],
        "cripto": [...],
        "forex": [...]
    }
    """
    log_scraping_start("TradingView")
    
    result = {
        "indices": [],
        "acciones": [],
        "cripto": [],
        "forex": []
    }
    
    try:
        # Create a session for better performance
        session = requests.Session()
        
        # Set default headers for the session
        session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        # Process each section with retry mechanism
        for section_name, url in TRADINGVIEW_URLS.items():
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    data = scrape_tradingview_section(session, url, section_name)
                    result[section_name] = data
                    
                    # Add random delay between requests to avoid detection
                    delay = random.uniform(2, 4)
                    logger.debug(f"⏳ Esperando {delay:.1f} segundos...")
                    time.sleep(delay)
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Intento {attempt + 1} falló para {section_name}: {e}")
                        time.sleep(random.uniform(3, 6))  # Wait before retry
                    else:
                        log_scraping_error(section_name, e)
                        result[section_name] = []
        
        # Close session
        session.close()
            
    except Exception as e:
        log_scraping_error("TradingView", e)
        return result
    
    # Log success
    total_items = sum(len(section) for section in result.values())
    log_scraping_success("TradingView", total_items)
    
    return result

# Función de compatibilidad para mantener la interfaz async
async def scrape_tradingview_async():
    """
    Async wrapper for the synchronous scraping function
    """
    return scrape_tradingview()
