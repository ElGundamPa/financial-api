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
import os
import base64
import jwt
from jwt import InvalidTokenError

class FinancialAPIHandler(BaseHTTPRequestHandler):
    """Handler simplificado para simular la API financiera"""
    
    def _unauthorized(self, scheme: str = "ApiKey", detail: str = "Unauthorized"):
        payload = {"detail": detail}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("WWW-Authenticate", scheme)
        self.end_headers()
        self.wfile.write(data)

    def _read_auth_mode(self):
        return (os.getenv("AUTH_MODE", "none") or "none").lower()

    def _require_auth(self) -> bool:
        """Devuelve True si la request está autenticada, False si no (y ya envió 401)."""
        mode = self._read_auth_mode()

        # Deshabilitado
        if mode in ("none", "off", "disabled"):
            return True

        # API Key
        if mode == "apikey":
            api_keys = [k.strip() for k in (os.getenv("API_KEYS", "") or "").split(",") if k.strip()]
            x_api_key = self.headers.get("x-api-key") or self.headers.get("X-API-Key")
            auth = self.headers.get("authorization") or self.headers.get("Authorization") or ""
            token = None
            if x_api_key:
                token = x_api_key.strip()
            elif auth.lower().startswith("apikey "):
                token = auth.split(" ", 1)[1].strip()
            if token and token in api_keys:
                return True
            self._unauthorized("ApiKey", "API key requerida")
            return False

        # Basic
        if mode == "basic":
            auth = self.headers.get("authorization") or self.headers.get("Authorization")
            if not auth or not auth.lower().startswith("basic "):
                self._unauthorized("Basic realm=API", "Credenciales básicas requeridas")
                return False
            try:
                b64 = auth.split(" ", 1)[1]
                user_pwd = base64.b64decode(b64).decode("utf-8")
                user, pwd = user_pwd.split(":", 1)
            except Exception:
                self._unauthorized("Basic realm=API", "Basic inválido")
                return False
            if user == os.getenv("BASIC_USER", "") and pwd == os.getenv("BASIC_PASSWORD", "") and user and pwd:
                return True
            self._unauthorized("Basic realm=API", "Credenciales inválidas")
            return False

        # JWT RS256
        if mode == "jwt":
            auth = self.headers.get("authorization") or self.headers.get("Authorization")
            if not auth or not auth.lower().startswith("bearer "):
                self._unauthorized("Bearer", "Token Bearer requerido")
                return False
            token = auth.split(" ", 1)[1].strip()
            public_key = os.getenv("JWT_PUBLIC_KEY", "")
            issuer = os.getenv("JWT_ISSUER", "")
            audience = os.getenv("JWT_AUDIENCE", "")
            required_scope = os.getenv("JWT_REQUIRED_SCOPE", "")
            if not public_key:
                # Config incorrecta
                self._unauthorized("Bearer", "Configuración JWT incompleta")
                return False
            try:
                claims = jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    issuer=issuer or None,
                    audience=audience or None,
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_iss": bool(issuer),
                        "verify_aud": bool(audience),
                    },
                )
                if required_scope:
                    scopes = []
                    if isinstance(claims.get("scope"), str):
                        scopes = claims.get("scope", "").split()
                    elif isinstance(claims.get("scopes"), list):
                        scopes = claims.get("scopes", [])
                    elif isinstance(claims.get("permissions"), list):
                        scopes = claims.get("permissions", [])
                    if required_scope not in scopes:
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"detail": "Insufficient scope"}).encode("utf-8"))
                        return False
                return True
            except InvalidTokenError:
                self._unauthorized("Bearer", "Token inválido")
                return False

        # Modo desconocido: denegar por seguridad
        self._unauthorized("ApiKey", "Autenticación requerida")
        return False

    def do_GET(self):
        """Manejar requests GET"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        # Proteger todos los endpoints (incluye /health)
        if not self._require_auth():
            return

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
        
        if not self._require_auth():
            return

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
