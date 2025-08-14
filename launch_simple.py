#!/usr/bin/env python3
"""
Lanzador simplificado de la API para evitar problemas de compatibilidad Python 3.13
Este script simula el comportamiento de la API sin depender de FastAPI directamente
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading

class FinancialAPIHandler(BaseHTTPRequestHandler):
    """Handler simplificado para simular la API financiera"""
    
    def do_GET(self):
        """Manejar requests GET"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/':
            self.send_root_response()
        elif path == '/health':
            self.send_health_response()
        elif path == '/sources':
            self.send_sources_response()
        elif path == '/datos':
            self.send_datos_response(query)
        elif path == '/datos/resume':
            self.send_datos_resume_response(query)
        else:
            self.send_404_response()
    
    def do_POST(self):
        """Manejar requests POST"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/scrape':
            self.send_scrape_response()
        else:
            self.send_404_response()
    
    def send_root_response(self):
        """Respuesta del endpoint raíz"""
        response_data = {
            "message": "Financial Data API - Serverless Ready",
            "version": "2.1.0",
            "runtime": "local",
            "description": "API optimizada para datos financieros de múltiples fuentes",
            "features": [
                "Scraping HTTP-only (sin navegador)",
                "Cache en memoria efímero",
                "Rate limiting",
                "CORS configurado",
                "Compresión GZip",
                "Timeouts estrictos"
            ],
            "endpoints": {
                "general": {
                    "/datos": "Obtener todos los datos financieros",
                    "/datos/resume": "Obtener resumen de datos",
                    "/health": "Verificar estado de la API",
                    "/scrape": "Ejecutar scraping manualmente",
                    "/sources": "Información de fuentes disponibles"
                }
            },
            "sources_status": {
                "finviz": {
                    "name": "Finviz",
                    "status": "ok",
                    "data_types": ["indices", "acciones", "forex"],
                    "requires_browser": False
                },
                "yahoo": {
                    "name": "Yahoo Finance", 
                    "status": "ok",
                    "data_types": ["indices", "acciones", "forex", "materias_primas", "etfs"],
                    "requires_browser": False
                },
                "tradingview": {
                    "name": "TradingView",
                    "status": "browser_required_disabled_in_prod",
                    "data_types": ["indices", "acciones", "forex", "cripto"],
                    "requires_browser": True
                }
            },
            "cache_info": {
                "enabled": True,
                "ttl": "90 segundos",
                "strategy": "In-memory TTL (serverless)"
            }
        }
        self.send_json_response(200, response_data)
    
    def send_health_response(self):
        """Respuesta del health check"""
        response_data = {
            "ok": True,
            "time": time.time(),
            "version": "2.1.0",
            "runtime": "local",
            "cache_items": 0,
            "sources_available": 2
        }
        self.send_json_response(200, response_data)
    
    def send_sources_response(self):
        """Respuesta de fuentes disponibles"""
        response_data = {
            "sources": {
                "finviz": {
                    "name": "Finviz",
                    "status": "ok",
                    "data_types": ["indices", "acciones", "forex"],
                    "requires_browser": False
                },
                "yahoo": {
                    "name": "Yahoo Finance",
                    "status": "ok", 
                    "data_types": ["indices", "acciones", "forex", "materias_primas", "etfs"],
                    "requires_browser": False
                },
                "tradingview": {
                    "name": "TradingView",
                    "status": "browser_required_disabled_in_prod",
                    "data_types": ["indices", "acciones", "forex", "cripto"],
                    "requires_browser": True
                }
            },
            "total_sources": 3,
            "runtime": "local"
        }
        self.send_json_response(200, response_data)
    
    def send_datos_response(self, query):
        """Respuesta de datos financieros (simulada)"""
        nocache = query.get('nocache', ['0'])[0] == '1'
        
        response_data = {
            "data": {
                "finviz": {
                    "indices": [
                        {"symbol": "SPY", "price": "450.25", "change": "+1.25%"},
                        {"symbol": "QQQ", "price": "380.50", "change": "+0.85%"}
                    ],
                    "acciones": [
                        {"symbol": "AAPL", "price": "175.30", "change": "+2.10%"},
                        {"symbol": "MSFT", "price": "420.80", "change": "+1.45%"}
                    ]
                },
                "yahoo": {
                    "forex": [
                        {"pair": "EUR/USD", "rate": "1.0950", "change": "+0.25%"},
                        {"pair": "GBP/USD", "rate": "1.2750", "change": "-0.15%"}
                    ],
                    "materias_primas": [
                        {"symbol": "GC=F", "name": "Gold", "price": "2050.30", "change": "+0.75%"},
                        {"symbol": "CL=F", "name": "Crude Oil", "price": "78.45", "change": "-1.20%"}
                    ]
                }
            },
            "errors": [],
            "timestamp": time.time(),
            "sources_scraped": ["finviz", "yahoo"],
            "total_sources": 2,
            "cache_used": not nocache
        }
        self.send_json_response(200, response_data)
    
    def send_datos_resume_response(self, query):
        """Respuesta de resumen de datos"""
        response_data = {
            "indices": [
                {"symbol": "SPY", "price": "450.25", "change": "+1.25%"},
                {"symbol": "QQQ", "price": "380.50", "change": "+0.85%"}
            ],
            "acciones": [
                {"symbol": "AAPL", "price": "175.30", "change": "+2.10%"},
                {"symbol": "MSFT", "price": "420.80", "change": "+1.45%"}
            ],
            "forex": [
                {"pair": "EUR/USD", "rate": "1.0950", "change": "+0.25%"}
            ],
            "materias_primas": [
                {"symbol": "GC=F", "name": "Gold", "price": "2050.30", "change": "+0.75%"}
            ],
            "etfs": [],
            "cripto": [],
            "last_updated": time.time(),
            "sources": {
                "finviz": {"has_data": True, "data_types": {"indices": 2, "acciones": 2}},
                "yahoo": {"has_data": True, "data_types": {"forex": 2, "materias_primas": 2}}
            }
        }
        self.send_json_response(200, response_data)
    
    def send_scrape_response(self):
        """Respuesta del endpoint de scraping manual"""
        response_data = {
            "data": {
                "finviz": {"indices": [], "acciones": []},
                "yahoo": {"forex": [], "materias_primas": []}
            },
            "errors": [],
            "timestamp": time.time(),
            "sources_scraped": ["finviz", "yahoo"],
            "total_sources": 2,
            "manual_scrape": True
        }
        self.send_json_response(200, response_data)
    
    def send_404_response(self):
        """Respuesta 404 para rutas no encontradas"""
        response_data = {
            "detail": "Not Found",
            "status_code": 404,
            "message": f"Endpoint {self.path} no encontrado"
        }
        self.send_json_response(404, response_data)
    
    def send_json_response(self, status_code, data):
        """Enviar respuesta JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept, User-Agent')
        self.send_header('Cache-Control', 'public, max-age=60')
        self.send_header('Vary', 'Accept-Encoding')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Personalizar logging"""
        print(f"🌐 {self.address_string()} - {format % args}")

def start_api_server(port=8000):
    """Iniciar servidor de la API"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, FinancialAPIHandler)
    
    print(f"🚀 FINANCIAL API LANZADA EXITOSAMENTE")
    print("=" * 50)
    print(f"🌐 Servidor corriendo en: http://localhost:{port}")
    print(f"📖 Endpoints disponibles:")
    print(f"   • GET  /              - Información general")
    print(f"   • GET  /health        - Health check")
    print(f"   • GET  /sources       - Fuentes disponibles")
    print(f"   • GET  /datos         - Datos financieros")
    print(f"   • GET  /datos/resume  - Resumen de datos")
    print(f"   • POST /scrape        - Scraping manual")
    print()
    print("🎯 Estado: FUNCIONANDO CORRECTAMENTE")
    print("✅ Sin errores de compatibilidad")
    print("🔧 Versión simplificada para desarrollo")
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        httpd.shutdown()

if __name__ == "__main__":
    start_api_server()
