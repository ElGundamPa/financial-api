#!/usr/bin/env python3
"""
Diagnóstico completo del scraping financiero
Identifica problemas en todas las fuentes y propone soluciones
"""

import json
import random
import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from config import FINVIZ_URLS, REQUEST_TIMEOUT, TRADINGVIEW_URLS, USER_AGENTS, YAHOO_URLS


def test_url(url: str, source: str, section: str) -> Dict[str, Any]:
    """Test a specific URL and return detailed diagnostics"""
    print(f"\n🔍 Probando: {source} - {section}")
    print(f"   URL: {url}")

    result = {
        "url": url,
        "source": source,
        "section": section,
        "status_code": None,
        "content_length": 0,
        "content_type": "",
        "is_html": False,
        "tables_found": 0,
        "rows_found": 0,
        "data_extracted": 0,
        "error": None,
        "suggestions": [],
    }

    try:
        # Headers optimizados
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

        # Request con timeout
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        result["status_code"] = response.status_code
        result["content_length"] = len(response.content)
        result["content_type"] = response.headers.get("content-type", "")

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            result["suggestions"].append(f"URL puede estar mal o requerir autenticación")
            return result

        # Verificar si es HTML
        if "text/html" in result["content_type"]:
            result["is_html"] = True
        else:
            result["error"] = "No es HTML"
            result["suggestions"].append("La URL puede devolver JSON o estar mal configurada")
            return result

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Buscar tablas
        tables = soup.find_all("table")
        result["tables_found"] = len(tables)

        # Buscar filas en tablas
        all_rows = []
        for table in tables:
            rows = table.find_all("tr")
            all_rows.extend(rows)

        result["rows_found"] = len(all_rows)

        # Intentar extraer datos
        if all_rows:
            extracted_data = []
            for row in all_rows[:10]:  # Solo primeros 10 para diagnóstico
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    row_data = {}
                    for i, cell in enumerate(cells[:6]):
                        row_data[f"col_{i+1}"] = cell.get_text(strip=True)
                    extracted_data.append(row_data)

            result["data_extracted"] = len(extracted_data)

            if extracted_data:
                result["sample_data"] = extracted_data[0]  # Primer elemento como muestra

        # Análisis específico por fuente
        if source == "TradingView":
            analyze_tradingview(soup, result)
        elif source == "Finviz":
            analyze_finviz(soup, result)
        elif source == "Yahoo":
            analyze_yahoo(soup, result)

        # Sugerencias generales
        if result["tables_found"] == 0:
            result["suggestions"].append("No se encontraron tablas - revisar selectors")
        if result["rows_found"] == 0:
            result["suggestions"].append("No se encontraron filas - la página puede estar vacía")
        if result["data_extracted"] == 0:
            result["suggestions"].append("No se pudieron extraer datos - revisar estructura HTML")

    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
        result["suggestions"].append("Aumentar timeout o verificar conectividad")
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)}"
        result["suggestions"].append("Verificar URL y conectividad")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        result["suggestions"].append("Revisar logs para más detalles")

    return result


def analyze_tradingview(soup: BeautifulSoup, result: Dict[str, Any]):
    """Análisis específico para TradingView"""
    # Buscar elementos específicos de TradingView
    tv_elements = soup.find_all("div", class_=lambda x: x and "tv-data-table" in x)
    if tv_elements:
        result["tradingview_specific"] = f"Encontrados {len(tv_elements)} elementos tv-data-table"

    # Buscar botones de "Load More"
    load_more = soup.find_all("button", string=lambda x: x and "load" in x.lower())
    if load_more:
        result["suggestions"].append("Página tiene botón 'Load More' - considerar Playwright")


def analyze_finviz(soup: BeautifulSoup, result: Dict[str, Any]):
    """Análisis específico para Finviz"""
    # Buscar elementos específicos de Finviz
    finviz_elements = soup.find_all("table", class_=lambda x: x and "screener" in x)
    if finviz_elements:
        result["finviz_specific"] = f"Encontradas {len(finviz_elements)} tablas screener"

    # Verificar si hay redirección
    if "screener" not in soup.get_text().lower():
        result["suggestions"].append("Página puede estar redirigiendo - verificar URL")


def analyze_yahoo(soup: BeautifulSoup, result: Dict[str, Any]):
    """Análisis específico para Yahoo Finance"""
    # Buscar elementos específicos de Yahoo
    yahoo_elements = soup.find_all("div", {"data-test": "fin-table"})
    if yahoo_elements:
        result["yahoo_specific"] = f"Encontrados {len(yahoo_elements)} elementos fin-table"

    # Verificar si es página de error
    if "error" in soup.get_text().lower() or "not found" in soup.get_text().lower():
        result["suggestions"].append("Página muestra error - URL puede estar mal")


def run_comprehensive_diagnostic():
    """Ejecutar diagnóstico completo de todas las fuentes"""
    print("🚀 DIAGNÓSTICO COMPLETO DEL SCRAPING FINANCIERO")
    print("=" * 60)

    all_results = {}

    # Test TradingView
    print("\n📊 TESTEANDO TRADINGVIEW")
    print("-" * 30)
    all_results["tradingview"] = {}
    for section, url in TRADINGVIEW_URLS.items():
        result = test_url(url, "TradingView", section)
        all_results["tradingview"][section] = result
        time.sleep(2)  # Delay entre requests

    # Test Finviz
    print("\n📊 TESTEANDO FINVIZ")
    print("-" * 30)
    all_results["finviz"] = {}
    for section, url in FINVIZ_URLS.items():
        result = test_url(url, "Finviz", section)
        all_results["finviz"][section] = result
        time.sleep(2)

    # Test Yahoo
    print("\n📊 TESTEANDO YAHOO FINANCE")
    print("-" * 30)
    all_results["yahoo"] = {}
    for section, url in YAHOO_URLS.items():
        result = test_url(url, "Yahoo", section)
        all_results["yahoo"][section] = result
        time.sleep(2)

    # Generar reporte
    print("\n📋 REPORTE COMPLETO")
    print("=" * 60)

    for source, sections in all_results.items():
        print(f"\n🔍 {source.upper()}:")
        for section, result in sections.items():
            status = "✅" if result["data_extracted"] > 0 else "❌"
            print(f"  {status} {section}: {result['data_extracted']} datos extraídos")
            if result["error"]:
                print(f"     Error: {result['error']}")
            if result["suggestions"]:
                print(f"     Sugerencias: {', '.join(result['suggestions'])}")

    # Guardar resultados
    with open("scraping_diagnostic_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: scraping_diagnostic_results.json")

    return all_results


if __name__ == "__main__":
    run_comprehensive_diagnostic()
