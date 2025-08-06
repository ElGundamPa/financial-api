import asyncio
import random
import time
from typing import Dict, List, Any
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from config import USER_AGENTS, FINVIZ_URLS, REQUEST_TIMEOUT
from logger import logger, log_scraping_start, log_scraping_success, log_scraping_error

async def launch_browser():
    """Launch browser with proper configuration"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    )
    return browser

async def scrape_finviz_section(page, url: str, key: str) -> List[Dict[str, Any]]:
    """Scrape a specific section from Finviz using Playwright"""
    try:
        logger.debug(f"🌐 Navegando a {url}")
        
        # Set user agent
        await page.set_user_agent(random.choice(USER_AGENTS))
        
        # Navigate to page
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)  # Wait for content to load
        
        # Take screenshot for debugging
        screenshot_path = f"screenshots/finviz_{key}_{int(time.time())}.png"
        await page.screenshot(path=screenshot_path)
        logger.debug(f"📸 Screenshot guardado: {screenshot_path}")
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, "lxml")
        section = []
        
        # Selectors mejorados y específicos para Finviz
        selectors = {
            "forex": [
                "table#screener-content-table tr",
                "table.table-light tr",
                "table tr",
                ".table-light tr",
                "tr[class*='table-light']",
                "tbody tr",
                "table.screener_table tr",
                "tr[class*='screener']",
                "table tr:not([class*='header'])"
            ],
            "acciones": [
                "table#screener-content-table tr",
                "table.table-light tr", 
                "table tr",
                ".table-light tr",
                "tr[class*='table-light']",
                "tbody tr",
                "table.screener_table tr",
                "tr[class*='screener']",
                "table tr:not([class*='header'])"
            ],
            "indices": [
                "table#screener-content-table tr",
                "table.table-light tr",
                "table tr",
                ".table-light tr",
                "tr[class*='table-light']",
                "tbody tr",
                "table.screener_table tr",
                "tr[class*='screener']",
                "table tr:not([class*='header'])"
            ]
        }
        
        rows = []
        selector_list = selectors.get(key, ["table tr"])
        
        # Intentar diferentes selectors con mejor lógica
        for selector in selector_list:
            try:
                found_rows = soup.select(selector)
                if found_rows and len(found_rows) > 2:  # Más de 2 para excluir headers
                    # Filtrar filas que contengan datos reales
                    valid_rows = []
                    for row in found_rows:
                        text = row.get_text(strip=True)
                        # Verificar que la fila contenga datos financieros, no navegación
                        if (len(text) > 10 and 
                            not any(nav_word in text.lower() for nav_word in 
                                   ['home', 'news', 'screener', 'maps', 'groups', 'portfolio', 
                                    'insider', 'futures', 'forex', 'crypto', 'backtests', 
                                    'pricing', 'theme', 'help', 'login', 'register'])):
                            valid_rows.append(row)
                    
                    if valid_rows:
                        rows = valid_rows
                        logger.debug(f"✅ Selector encontrado para {key}: {selector} - {len(rows)} filas válidas")
                        break
            except Exception as e:
                logger.debug(f"⚠️ Error con selector {selector}: {e}")
                continue
        
        if not rows:
            logger.warning(f"⚠️ No se encontraron filas válidas en {key}")
            return []
        
        # Skip header rows and process all data rows (máximo 100)
        data_rows = rows[1:101] if len(rows) > 1 else []
        
        for i, row in enumerate(data_rows):
            try:
                cols = row.find_all("td")
                
                if key == "forex" and len(cols) >= 3:
                    par = cols[0].get_text(strip=True)
                    precio = cols[1].get_text(strip=True)
                    cambio = cols[2].get_text(strip=True)
                    
                    if par and precio and par != "Symbol" and len(par) < 20:  # Validate data and skip headers
                        section.append({
                            "par": par,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Forex: {par} - {precio} - {cambio}")
                        
                elif key == "acciones" and len(cols) >= 4:
                    ticker = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                    nombre = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                    precio = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                    cambio = cols[4].get_text(strip=True) if len(cols) > 4 else ""
                    
                    if ticker and ticker != "No." and len(ticker) < 10:  # Validate data and skip headers
                        section.append({
                            "ticker": ticker,
                            "nombre": nombre,
                            "precio": precio,
                            "cambio": cambio
                        })
                        logger.debug(f"📊 Acción: {ticker} - {nombre} - {precio}")
                        
                elif key == "indices" and len(cols) >= 3:
                    indice = cols[0].get_text(strip=True)
                    precio = cols[1].get_text(strip=True)
                    cambio = cols[2].get_text(strip=True)
                    
                    if indice and precio and indice != "Index" and len(indice) < 50:  # Validate data and skip headers
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
        
    except Exception as e:
        logger.error(f"❌ Error scraping {key}: {e}")
        return []

async def scrape_finviz():
    """Main Finviz scraping function using Playwright"""
    log_scraping_start("Finviz")
    
    data = {}
    
    try:
        # Launch browser
        browser = await launch_browser()
        page = await browser.new_page()
        
        # Set viewport for better rendering
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        for key, url in FINVIZ_URLS.items():
            try:
                logger.info(f"🔄 Procesando sección: {key}")
                section_data = await scrape_finviz_section(page, url, key)
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
        if 'browser' in locals():
            await browser.close()
    
    # Log success
    total_items = sum(len(section) for section in data.values())
    log_scraping_success("Finviz", total_items)
    
    return data
