import os
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from config import USER_AGENTS, REQUEST_TIMEOUT, TRADINGVIEW_URLS
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

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

        # Selectors mejorados para TradingView
        if section_name == "indices":
            # Selectors específicos para índices
            selectors = [
                "table tbody tr",
                "div[class*='row']",
                "tr[class*='row']",
                "table tr",
                "tbody tr",
                "tr"
            ]
        elif section_name == "forex":
            # Selectors específicos para forex
            selectors = [
                "table tbody tr",
                "div[class*='row']",
                "tr[class*='row']",
                "table tr",
                "tbody tr",
                "tr",
                ".tv-data-table__row",
                ".tv-screener__content-row"
            ]
        else:
            # Selectors para otras secciones
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
            
            rows = []
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    if elements and len(elements) > 0:
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
        
        # Procesar TODAS las filas para índices, máximo 50 para otras secciones
        max_rows = len(rows) if section_name == "indices" else min(50, len(rows))
        
        for i, row in enumerate(rows[:max_rows]):
            try:
                # Extraer datos de la fila
                row_data = extract_row_data(row, section_name)
                
                if row_data:
                    data.append(row_data)
                    processed_count += 1
                    
                    # Log cada 10 elementos procesados
                    if processed_count % 10 == 0:
                        logger.debug(f"📊 Procesados {processed_count} elementos de {section_name}")
                    
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

def extract_row_data(row, section_name: str) -> Dict[str, str]:
    """
    Extract data from a table row
    """
    try:
        # Try different cell extraction strategies
        cells = row.find_all("td")
        
        if len(cells) >= 3:
            # Standard table format
            nombre = cells[0].get_text(strip=True)
            precio = cells[1].get_text(strip=True)
            cambio = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
            maximo = cells[3].get_text(strip=True) if len(cells) > 3 else "N/A"
            minimo = cells[4].get_text(strip=True) if len(cells) > 4 else "N/A"
            calificacion = cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"
            
        elif len(cells) == 2:
            # Two-column format
            nombre = cells[0].get_text(strip=True)
            precio = cells[1].get_text(strip=True)
            cambio = "N/A"
            maximo = "N/A"
            minimo = "N/A"
            calificacion = "N/A"
            
        else:
            # Try to extract from div elements
            divs = row.find_all("div")
            if len(divs) >= 2:
                nombre = divs[0].get_text(strip=True)
                precio = divs[1].get_text(strip=True)
                cambio = divs[2].get_text(strip=True) if len(divs) > 2 else "N/A"
                maximo = divs[3].get_text(strip=True) if len(divs) > 3 else "N/A"
                minimo = divs[4].get_text(strip=True) if len(divs) > 4 else "N/A"
                calificacion = divs[5].get_text(strip=True) if len(divs) > 5 else "N/A"
            else:
                # Fallback: extract all text
                text = row.get_text(strip=True)
                parts = text.split()
                if len(parts) >= 2:
                    nombre = parts[0]
                    precio = parts[1]
                    cambio = parts[2] if len(parts) > 2 else "N/A"
                    maximo = parts[3] if len(parts) > 3 else "N/A"
                    minimo = parts[4] if len(parts) > 4 else "N/A"
                    calificacion = parts[5] if len(parts) > 5 else "N/A"
                else:
                    return None
        
        # Validate and clean data
        if nombre and precio and len(nombre) > 0:
            # Clean up the data
            nombre = nombre.replace('\n', ' ').replace('\t', ' ').strip()
            precio = precio.replace('\n', ' ').replace('\t', ' ').strip()
            cambio = cambio.replace('\n', ' ').replace('\t', ' ').strip()
            maximo = maximo.replace('\n', ' ').replace('\t', ' ').strip()
            minimo = minimo.replace('\n', ' ').replace('\t', ' ').strip()
            calificacion = calificacion.replace('\n', ' ').replace('\t', ' ').strip()
            
            # Limit string lengths
            nombre = nombre[:50] if len(nombre) > 50 else nombre
            precio = precio[:20] if len(precio) > 20 else precio
            cambio = cambio[:20] if len(cambio) > 20 else cambio
            maximo = maximo[:20] if len(maximo) > 20 else maximo
            minimo = minimo[:20] if len(minimo) > 20 else minimo
            calificacion = calificacion[:20] if len(calificacion) > 20 else calificacion
            
            return {
                "nombre": nombre,
                "precio": precio,
                "cambio": cambio,
                "maximo": maximo,
                "minimo": minimo,
                "calificacion": calificacion
            }
        
        return None
        
    except Exception as e:
        logger.debug(f"⚠️ Error extrayendo datos de fila: {e}")
        return None

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
