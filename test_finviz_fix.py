#!/usr/bin/env python3
"""
Test script para verificar que el scraper de Finviz funciona correctamente
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import random

import requests

from config import REQUEST_TIMEOUT, USER_AGENTS
from scraper.finviz import scrape_finviz_section_sync


def test_finviz_scraper():
    """Test del scraper de Finviz"""
    print("🧪 TESTEANDO SCRAPER DE FINVIZ")
    print("=" * 40)
    
    # URLs de prueba
    test_urls = {
        "acciones": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=cap_large",
        "indices": "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=idx_sp500"
    }
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS)
    })
    
    for section, url in test_urls.items():
        print(f"\n🔍 Probando: {section}")
        print(f"URL: {url}")
        
        try:
            # Usar el scraper corregido
            data = scrape_finviz_section_sync(session, url, section)
            
            print(f"✅ Datos extraídos: {len(data)} elementos")
            
            if data:
                print("📊 Primeros 3 elementos:")
                for i, item in enumerate(data[:3]):
                    print(f"  {i+1}. {item}")
            else:
                print("❌ No se extrajeron datos")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_finviz_scraper()
