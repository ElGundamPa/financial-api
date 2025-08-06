import os
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from config import USER_AGENTS, REQUEST_TIMEOUT, TRADINGVIEW_URLS
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error
import asyncio

async def scrape_tradingview_section(page, url: str, section_name: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from TradingView with improved data extraction"""
    try:
        logger.debug(f"🌐 Navegando a {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait for content to load
        await asyncio.sleep(3)
        
        # Handle "Load More" button for forex and other sections
        if section_name in ["forex", "acciones"]:
            await handle_load_more_button(page, section_name)
        
        # Take screenshot for debugging
        screenshot_path = f"screenshots/tradingview_{section_name}_{int(time.time())}.png"
        await page.screenshot(path=screenshot_path)
        logger.debug(f"📸 HTML guardado: {screenshot_path}")
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, "lxml")
        
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
        
        section = []
        for i, row in enumerate(data_rows):
            try:
                row_data = extract_row_data_improved(row, section_name)
                if row_data:
                    section.append(row_data)
                    logger.debug(f"📊 {section_name}: {row_data.get('nombre', 'N/A')} - {row_data.get('precio', 'N/A')}")
            except Exception as e:
                logger.debug(f"⚠️ Error procesando fila {i} en {section_name}: {e}")
                continue
        
        logger.debug(f"✅ Sección {section_name} procesada: {len(section)} elementos")
        return section
        
    except Exception as e:
        logger.error(f"❌ Error scraping {section_name}: {e}")
        return []

async def handle_load_more_button(page, section_name: str):
    """Handle 'Load More' button to get all available data"""
    try:
        max_clicks = 10  # Maximum number of "Load More" clicks
        clicks = 0
        
        while clicks < max_clicks:
            # Look for "Load More" button with different possible selectors
            load_more_selectors = [
                "button[class*='load-more']",
                "button[class*='LoadMore']",
                "button:contains('Cargar más')",
                "button:contains('Load more')",
                "button:contains('Show more')",
                "button:contains('Mostrar más')",
                "[data-role='load-more']",
                ".tv-load-more__btn",
                ".tv-screener__load-more",
                "button[class*='tv-button']"
            ]
            
            button_found = False
            for selector in load_more_selectors:
                try:
                    # Check if button exists and is visible
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        if is_visible:
                            # Click the button
                            await button.click()
                            await asyncio.sleep(2)  # Wait for content to load
                            clicks += 1
                            button_found = True
                            logger.debug(f"🔄 Clic {clicks} en 'Cargar más' para {section_name}")
                            break
                except Exception as e:
                    logger.debug(f"⚠️ Error con selector de botón {selector}: {e}")
                    continue
            
            if not button_found:
                logger.debug(f"✅ No se encontraron más botones 'Cargar más' para {section_name}")
                break
                
    except Exception as e:
        logger.debug(f"⚠️ Error manejando botón 'Cargar más' para {section_name}: {e}")

def extract_row_data_improved(row, section_name: str) -> Dict[str, str]:
    """
    Extract data from a table row with improved logic based on investigation
    """
    try:
        # Skip header rows
        row_text = row.get_text(strip=True)
        if any(header_word in row_text.lower() for header_word in 
               ['símbolo', 'symbol', 'precio', 'price', 'cambio', 'change', 'capitalización']):
            return None
        
        # Try to extract from table cells first
        cells = row.find_all("td")
        if len(cells) >= 3:
            if section_name == "forex":
                # Forex: Símbolo, Precio, Cambio %, Cambio, Bid, Ask, Máximo, Mínimo, Calificación
                nombre = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                precio = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                cambio_porcentaje = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                cambio = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                maximo = cells[6].get_text(strip=True) if len(cells) > 6 else ""
                minimo = cells[7].get_text(strip=True) if len(cells) > 7 else ""
                calificacion = cells[8].get_text(strip=True) if len(cells) > 8 else ""
                
                return {
                    "nombre": nombre,
                    "precio": precio,
                    "cambio": cambio_porcentaje,
                    "cambio_valor": cambio,
                    "maximo": maximo,
                    "minimo": minimo,
                    "calificacion": calificacion
                }
                
            elif section_name == "acciones":
                # Acciones: Símbolo, Capitalización, Precio, Cambio %, Volumen, etc.
                nombre = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                capitalizacion = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                precio = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                cambio = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                volumen = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                
                return {
                    "nombre": nombre,
                    "capitalizacion": capitalizacion,
                    "precio": precio,
                    "cambio": cambio,
                    "volumen": volumen
                }
                
            else:
                # Default extraction for other sections
                nombre = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                precio = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                cambio = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                maximo = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                minimo = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                calificacion = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                
                return {
                    "nombre": nombre,
                    "precio": precio,
                    "cambio": cambio,
                    "maximo": maximo,
                    "minimo": minimo,
                    "calificacion": calificacion
                }
        
        # Fallback: try to extract from div elements
        divs = row.find_all("div")
        if len(divs) >= 2:
            nombre = divs[0].get_text(strip=True)
            precio = divs[1].get_text(strip=True)
            cambio = divs[2].get_text(strip=True) if len(divs) > 2 else "N/A"
            
            return {
                "nombre": nombre,
                "precio": precio,
                "cambio": cambio,
                "maximo": "N/A",
                "minimo": "N/A",
                "calificacion": "N/A"
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

# Función async que usa Playwright para mejor rendimiento
async def scrape_tradingview_async():
    """
    Main TradingView scraping function using Playwright with improved error handling
    """
    log_scraping_start("TradingView")
    
    data = {}
    
    try:
        # Launch browser
        browser = await launch_browser()
        page = await browser.new_page()
        
        # Set user agent
        await page.set_user_agent(random.choice(USER_AGENTS))
        
        # Set viewport for better rendering
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        for key, url in TRADINGVIEW_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {key}")
                section_data = await scrape_tradingview_section(page, url, key)
                data[key] = section_data
                
                # Add delay between requests to avoid rate limiting
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception as e:
                log_scraping_error(key, e)
                data[key] = []
                
    except Exception as e:
        log_scraping_error("TradingView", e)
        return {}
    finally:
        if 'browser' in locals():
            await browser.close()
    
    # Log success
    total_items = sum(len(section) for section in data.values())
    log_scraping_success("TradingView", total_items)
    
    return data
