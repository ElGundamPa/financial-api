import json
import random

import requests
from bs4 import BeautifulSoup
from config import FINVIZ_URLS, REQUEST_TIMEOUT, USER_AGENTS, YAHOO_URLS


def test_url(url, name):
    """Test a URL and return basic info about the response"""
    try:
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
        }

        print(f"\n🔍 Probando {name}: {url}")
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        print(f"   Status Code: {response.status_code}")
        print(f"   Content Length: {len(response.text)}")
        print(f"   Content Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")

            # Buscar tablas
            tables = soup.find_all("table")
            print(f"   Tablas encontradas: {len(tables)}")

            # Buscar filas de tabla
            rows = soup.find_all("tr")
            print(f"   Filas encontradas: {len(rows)}")

            # Buscar elementos específicos
            selectors_to_test = [
                "table.screener_table tbody tr",
                "table[class*='screener'] tbody tr",
                "table tbody tr",
                "tr[class*='table-light']",
                "tr[class*='table-dark']",
                "tbody tr",
                "table tr",
                "div[data-test='fin-table'] tbody tr",
                "tr[class*='simpTblRow']",
            ]

            for selector in selectors_to_test:
                found = soup.select(selector)
                if found:
                    print(f"   ✅ Selector '{selector}': {len(found)} elementos")
                    if len(found) > 0:
                        # Mostrar primera fila como ejemplo
                        first_row = found[0]
                        cells = first_row.find_all(["td", "th"])
                        print(f"      Primera fila tiene {len(cells)} celdas")
                        if len(cells) > 0:
                            print(f"      Contenido: {cells[0].get_text(strip=True)[:50]}...")
                        break
            else:
                print(f"   ❌ Ningún selector funcionó")

            # Guardar HTML para inspección
            with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"   📄 HTML guardado en debug_{name}.html")

        else:
            print(f"   ❌ Error HTTP: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error: {e}")


def main():
    print("🔧 DIAGNÓSTICO DE SCRAPERS")
    print("=" * 50)

    print("\n📊 PROBANDO FINVIZ:")
    for key, url in FINVIZ_URLS.items():
        test_url(url, f"finviz_{key}")

    print("\n📊 PROBANDO YAHOO:")
    for key, url in YAHOO_URLS.items():
        test_url(url, f"yahoo_{key}")


if __name__ == "__main__":
    main()
