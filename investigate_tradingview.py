#!/usr/bin/env python3
"""
Script para investigar la estructura HTML de TradingView
"""

import asyncio
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def investigate_tradingview_forex():
    """Investigar la estructura HTML de TradingView Forex"""
    print("🔍 Investigando TradingView Forex...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible para debugging
        page = await browser.new_page()
        
        # Configurar viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Navegar a la página
        url = "https://es.tradingview.com/markets/currencies/rates-all/"
        print(f"🌐 Navegando a: {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)  # Esperar que cargue todo
        
        # Tomar screenshot
        await page.screenshot(path="investigation_forex.png")
        print("📸 Screenshot guardado: investigation_forex.png")
        
        # Obtener HTML
        content = await page.content()
        
        # Guardar HTML para análisis
        with open("investigation_forex.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("📄 HTML guardado: investigation_forex.html")
        
        # Analizar con BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        
        # Buscar diferentes tipos de selectors
        selectors_to_try = [
            "table tbody tr",
            "div[class*='row']",
            "tr[class*='row']",
            "table tr",
            "tbody tr",
            "tr",
            ".tv-data-table__row",
            ".tv-screener__content-row",
            "[data-role='symbol']",
            "div[class*='symbol']",
            "div[class*='price']",
            "div[class*='change']",
            "div[class*='table']",
            "div[class*='cell']",
            "div[class*='item']"
        ]
        
        print("\n🔍 Analizando selectors...")
        for selector in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                print(f"✅ {selector}: {len(elements)} elementos encontrados")
                if len(elements) > 0:
                    # Mostrar el primer elemento
                    first_element = elements[0]
                    text = first_element.get_text(strip=True)[:100]
                    print(f"   Primer elemento: {text}...")
            else:
                print(f"❌ {selector}: 0 elementos")
        
        # Buscar botones "Cargar más"
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
        
        print("\n🔍 Buscando botones 'Cargar más'...")
        for selector in load_more_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"✅ Botón encontrado: {selector}")
                for elem in elements:
                    text = elem.get_text(strip=True)
                    print(f"   Texto: '{text}'")
        
        await browser.close()

async def investigate_tradingview_stocks():
    """Investigar la estructura HTML de TradingView Acciones"""
    print("\n🔍 Investigando TradingView Acciones...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        url = "https://es.tradingview.com/markets/stocks-usa/market-movers-large-cap/"
        print(f"🌐 Navegando a: {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        
        await page.screenshot(path="investigation_stocks.png")
        print("📸 Screenshot guardado: investigation_stocks.png")
        
        content = await page.content()
        
        with open("investigation_stocks.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("📄 HTML guardado: investigation_stocks.html")
        
        soup = BeautifulSoup(content, "lxml")
        
        # Buscar la tabla de datos
        print("\n🔍 Analizando estructura de acciones...")
        
        # Buscar tablas específicas
        tables = soup.find_all("table")
        print(f"📊 Encontradas {len(tables)} tablas")
        
        for i, table in enumerate(tables):
            print(f"\n📋 Tabla {i+1}:")
            rows = table.find_all("tr")
            print(f"   Filas: {len(rows)}")
            
            if rows:
                # Mostrar primera fila
                first_row = rows[0]
                cells = first_row.find_all(["td", "th"])
                print(f"   Columnas: {len(cells)}")
                
                for j, cell in enumerate(cells[:5]):  # Solo primeras 5 columnas
                    text = cell.get_text(strip=True)[:50]
                    print(f"     Col {j+1}: {text}")
        
        await browser.close()

async def investigate_finviz():
    """Investigar la estructura HTML de Finviz"""
    print("\n🔍 Investigando Finviz...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        url = "https://finviz.com/forex.ashx?v=111"
        print(f"🌐 Navegando a: {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        
        await page.screenshot(path="investigation_finviz.png")
        print("📸 Screenshot guardado: investigation_finviz.png")
        
        content = await page.content()
        
        with open("investigation_finviz.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("📄 HTML guardado: investigation_finviz.html")
        
        soup = BeautifulSoup(content, "lxml")
        
        # Buscar tablas de datos
        print("\n🔍 Analizando estructura de Finviz...")
        
        tables = soup.find_all("table")
        print(f"📊 Encontradas {len(tables)} tablas")
        
        for i, table in enumerate(tables):
            print(f"\n📋 Tabla {i+1}:")
            rows = table.find_all("tr")
            print(f"   Filas: {len(rows)}")
            
            if rows:
                first_row = rows[0]
                cells = first_row.find_all(["td", "th"])
                print(f"   Columnas: {len(cells)}")
                
                for j, cell in enumerate(cells[:5]):
                    text = cell.get_text(strip=True)[:50]
                    print(f"     Col {j+1}: {text}")
        
        await browser.close()

async def main():
    """Función principal de investigación"""
    print("🔍 INICIO DE INVESTIGACIÓN DE SCRAPERS")
    print("=" * 50)
    
    try:
        await investigate_tradingview_forex()
        await investigate_tradingview_stocks()
        await investigate_finviz()
        
        print("\n✅ Investigación completada")
        print("📁 Archivos generados:")
        print("   - investigation_forex.png/html")
        print("   - investigation_stocks.png/html")
        print("   - investigation_finviz.png/html")
        
    except Exception as e:
        print(f"❌ Error durante la investigación: {e}")

if __name__ == "__main__":
    asyncio.run(main())
