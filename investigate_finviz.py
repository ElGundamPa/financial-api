#!/usr/bin/env python3
"""
Investigación específica de Finviz para entender por qué no funciona
"""

import random

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT, USER_AGENTS


def investigate_finviz_url(url: str, section: str):
    """Investigar una URL específica de Finviz"""
    print(f"\n🔍 Investigando Finviz - {section}")
    print(f"URL: {url}")

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)}")
        print(f"Content Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")

            # Guardar HTML para inspección
            with open(f"finviz_{section}_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"HTML guardado en: finviz_{section}_debug.html")

            # Buscar elementos específicos
            tables = soup.find_all("table")
            print(f"Tablas encontradas: {len(tables)}")

            for i, table in enumerate(tables):
                print(f"  Tabla {i+1}: class='{table.get('class', 'N/A')}'")
                rows = table.find_all("tr")
                print(f"    Filas: {len(rows)}")
                if rows:
                    print(f"    Primera fila: {rows[0].get_text(strip=True)[:100]}...")

            # Buscar elementos con clase screener
            screener_elements = soup.find_all(class_=lambda x: x and "screener" in str(x).lower())
            print(f"Elementos screener: {len(screener_elements)}")

            # Buscar cualquier tabla
            all_tables = soup.find_all("table")
            print(f"Total de tablas: {len(all_tables)}")

            # Buscar divs que puedan contener datos
            data_divs = soup.find_all(
                "div", class_=lambda x: x and any(word in str(x).lower() for word in ["table", "data", "row"])
            )
            print(f"Divs con datos potenciales: {len(data_divs)}")

            # Verificar si hay redirección
            if "screener" not in soup.get_text().lower():
                print("⚠️ No se encontró 'screener' en el contenido - posible redirección")

            # Buscar enlaces que puedan ser útiles
            links = soup.find_all("a", href=True)
            screener_links = [link for link in links if "screener" in link["href"]]
            print(f"Enlaces screener encontrados: {len(screener_links)}")
            for link in screener_links[:5]:
                print(f"  - {link['href']}")

        else:
            print(f"❌ Error HTTP: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Investigar todas las URLs de Finviz"""
    print("🚀 INVESTIGACIÓN ESPECÍFICA DE FINVIZ")
    print("=" * 50)

    # URLs de Finviz para investigar
    finviz_urls = {
        "forex": "https://finviz.com/forex.ashx",
        "acciones": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=cap_large",
        "indices": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=idx_sp500",
    }

    # También probar URLs alternativas
    alternative_urls = {
        "forex_alt": "https://finviz.com/forex.ashx?v=111",
        "acciones_alt": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers",
        "indices_alt": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers",
    }

    for section, url in finviz_urls.items():
        investigate_finviz_url(url, section)

    print("\n🔄 PROBANDO URLs ALTERNATIVAS")
    print("-" * 30)

    for section, url in alternative_urls.items():
        investigate_finviz_url(url, section)


if __name__ == "__main__":
    main()
