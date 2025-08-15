import asyncio
import base64
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
import jwt
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from ..scrapers.http_finviz import scrape_finviz
from ..scrapers.http_tradingview import scrape_tradingview
from ..scrapers.http_yahoo import scrape_yahoo

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache global en memoria (efímero por instancia)
cache = TTLCache(maxsize=128, ttl=90)  # 90 segundos TTL


# Rate limiter (la clave se ajustará dinámicamente según el modo de auth)
def _default_rate_key(request: Request) -> str:
    return get_remote_address(request)


limiter = Limiter(key_func=_default_rate_key)


class ScrapeRequest(BaseModel):
    sources: Optional[List[str]] = Field(default=None, description="Fuentes específicas a scrapear")
    categories: Optional[List[str]] = Field(default=None, description="Categorías específicas a scrapear")
    force_refresh: bool = Field(default=False, description="Forzar refresh ignorando cache")


class Settings:
    """Configuración de la aplicación"""

    def __init__(self, runtime: str = "local"):
        self.runtime = runtime
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        self.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))
        self.http_timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "12"))
        self.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "90"))
        self.max_body_kb = int(os.getenv("MAX_BODY_KB", "128"))

        # Autenticación (configurable por entorno)
        # Modo por defecto: "apikey" en vercel, "none" en local
        # Modos soportados: none | apikey | basic | jwt
        default_auth_mode = "apikey" if runtime == "vercel" else "none"
        self.auth_mode = os.getenv("AUTH_MODE", default_auth_mode).lower()
        # API Keys permitidas, separadas por coma
        raw_keys = os.getenv("API_KEYS", "")
        self.api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        # Credenciales Basic Auth (si se habilita modo "basic")
        self.basic_user = os.getenv("BASIC_USER", "")
        self.basic_password = os.getenv("BASIC_PASSWORD", "")
        # JWT configuración (modo "jwt")
        # Para serverless, se recomienda RS256 con clave pública inyectada por env
        self.jwt_public_key = os.getenv("JWT_PUBLIC_KEY", "")
        self.jwt_issuer = os.getenv("JWT_ISSUER", "")
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "")
        self.jwt_required_scope = os.getenv("JWT_REQUIRED_SCOPE", "")
        # Rutas excluidas de autenticación (por defecto permitir preflight y docs/health)
        raw_excludes = os.getenv("AUTH_EXCLUDE_PATHS", "/health,/docs,/openapi.json")
        self.auth_exclude_paths = [p.strip() for p in raw_excludes.split(",") if p.strip()]

        # Configuración específica para Vercel
        if runtime == "vercel":
            self.disable_browser_sources = True
            self.enable_compression = True
        else:
            self.disable_browser_sources = False
            self.enable_compression = True


def create_app(runtime: str = "local") -> FastAPI:
    """Factory para crear la aplicación FastAPI"""
    settings = Settings(runtime)

    app = FastAPI(
        title="Financial Data API",
        description="API para obtener datos financieros de múltiples fuentes - Serverless Ready",
        version="2.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configurar rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "User-Agent"],
        max_age=3600,
    )

    # Configurar compresión
    if settings.enable_compression:
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Helper: decodificar y validar JWT RS256
    def _decode_jwt(token: str) -> Dict[str, Any]:
        if not settings.jwt_public_key:
            raise HTTPException(status_code=500, detail="JWT_PUBLIC_KEY no configurado")

        try:
            decoded = jwt.decode(
                token,
                settings.jwt_public_key,
                algorithms=["RS256"],
                issuer=settings.jwt_issuer if settings.jwt_issuer else None,
                audience=settings.jwt_audience if settings.jwt_audience else None,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": bool(settings.jwt_issuer),
                    "verify_aud": bool(settings.jwt_audience),
                },
            )
            return decoded
        except InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # Middleware de Autenticación (API Key, Basic o JWT)
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Permitir preflight CORS sin auth
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path in settings.auth_exclude_paths:
            return await call_next(request)

        mode = settings.auth_mode
        # Si la autenticación está deshabilitada
        if mode in ("none", "disabled", "off"):
            return await call_next(request)

        # Verificar API Key
        if mode == "apikey":
            api_key_header = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
            # También soportar esquema Authorization: ApiKey <key>
            auth_header = request.headers.get("authorization") or ""
            token = None
            if api_key_header:
                token = api_key_header.strip()
            elif auth_header.lower().startswith("apikey "):
                token = auth_header.split(" ", 1)[1].strip()

            if token and token in settings.api_keys:
                return await call_next(request)

            response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            response.headers["WWW-Authenticate"] = "ApiKey"
            return response

        # Verificar Basic Auth
        if mode == "basic":
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            if not auth_header or not auth_header.lower().startswith("basic "):
                response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
                response.headers["WWW-Authenticate"] = "Basic realm=API"
                return response

            try:
                b64 = auth_header.split(" ", 1)[1]
                decoded = base64.b64decode(b64).decode("utf-8")
                if ":" not in decoded:
                    raise ValueError("invalid basic structure")
                user, pwd = decoded.split(":", 1)
            except Exception:
                response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
                response.headers["WWW-Authenticate"] = "Basic realm=API"
                return response

            if user == settings.basic_user and pwd == settings.basic_password and user and pwd:
                return await call_next(request)

            response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            response.headers["WWW-Authenticate"] = "Basic realm=API"
            return response

        # Verificar JWT RS256
        if mode == "jwt":
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            if not auth_header or not auth_header.lower().startswith("bearer "):
                return JSONResponse(status_code=401, content={"detail": "Missing Bearer token"})

            token = auth_header.split(" ", 1)[1].strip()
            try:
                claims = _decode_jwt(token)
                # Validar scope si se requiere
                if settings.jwt_required_scope:
                    scopes = []
                    # Common places: scope, scopes, permissions
                    if isinstance(claims.get("scope"), str):
                        scopes = claims.get("scope", "").split()
                    elif isinstance(claims.get("scopes"), list):
                        scopes = claims.get("scopes", [])
                    elif isinstance(claims.get("permissions"), list):
                        scopes = claims.get("permissions", [])

                    if settings.jwt_required_scope not in scopes:
                        return JSONResponse(status_code=403, content={"detail": "Insufficient scope"})

                # Ajustar clave de rate-limit por sujeto del token si está presente
                subject = claims.get("sub") or claims.get("client_id") or claims.get("uid")
                if subject:
                    request.state.rate_limit_key = f"jwt:{subject}"
                else:
                    request.state.rate_limit_key = f"jwt:anonymous"

                # Continuar
                return await call_next(request)
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
            except Exception:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # Modos no soportados
        logger.warning(f"Modo de autenticación desconocido: {settings.auth_mode}. Permitiendo acceso.")
        return await call_next(request)

    # Middleware para limitar tamaño de body
    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_body_kb * 1024:
                return JSONResponse(
                    status_code=413, content={"error": f"Body demasiado grande. Máximo {settings.max_body_kb}KB"}
                )
        response = await call_next(request)
        return response

    # Middleware para headers de cache
    @app.middleware("http")
    async def add_cache_headers(request: Request, call_next):
        response = await call_next(request)
        if request.method == "GET":
            response.headers["Cache-Control"] = "public, max-age=60"
            response.headers["Vary"] = "Accept-Encoding"
        return response

    # Reconfigurar función de key de rate-limit para usar el subject del JWT si está disponible
    def _rate_key_func(request: Request) -> str:
        key = getattr(request.state, "rate_limit_key", None)
        if key:
            return key
        return get_remote_address(request)

    app.state.limiter._key_func = _rate_key_func  # type: ignore[attr-defined]

    # Cliente HTTP global
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
    )

    # Endpoints
    @app.get("/")
    @limiter.limit(f"{settings.rate_limit_rpm}/minute")
    async def root(request: Request):
        """Endpoint raíz con información de la API"""
        sources_status = get_sources_status(settings)

        return {
            "message": "Financial Data API - Serverless Ready",
            "version": "2.1.0",
            "runtime": settings.runtime,
            "description": "API optimizada para datos financieros de múltiples fuentes",
            "features": [
                "Scraping HTTP-only (sin navegador)",
                "Cache en memoria efímero",
                "Rate limiting",
                "CORS configurado",
                "Compresión GZip",
                "Timeouts estrictos",
            ],
            "endpoints": {
                "general": {
                    "/datos": "Obtener todos los datos financieros",
                    "/datos/resume": "Obtener resumen de datos",
                    "/health": "Verificar estado de la API",
                    "/scrape": "Ejecutar scraping manualmente",
                    "/sources": "Información de fuentes disponibles",
                }
            },
            "sources_status": sources_status,
            "cache_info": {"enabled": True, "ttl": f"{settings.cache_ttl} segundos", "strategy": "In-memory TTL (serverless)"},
        }

    @app.get("/health")
    @limiter.limit("100/minute")
    async def health_check(request: Request):
        """Health check endpoint"""
        return {
            "ok": True,
            "time": time.time(),
            "version": "2.1.0",
            "runtime": settings.runtime,
            "cache_items": len(cache),
            "sources_available": len([s for s in get_sources_status(settings).values() if s.get("status") == "ok"]),
        }

    @app.get("/sources")
    @limiter.limit("30/minute")
    async def get_sources(request: Request):
        """Obtener información de fuentes disponibles"""
        sources_status = get_sources_status(settings)

        return {"sources": sources_status, "total_sources": len(sources_status), "runtime": settings.runtime}

    @app.get("/datos")
    @limiter.limit("30/minute")
    async def get_datos(request: Request):
        """Obtener todos los datos financieros"""
        nocache = request.query_params.get("nocache", "0") == "1"

        if not nocache:
            cached_data = cache.get("all_data")
            if cached_data:
                return JSONResponse(content=cached_data)

        try:
            data = await scrape_all_data(http_client, settings)
            cache["all_data"] = data
            return JSONResponse(content=data)
        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    @app.get("/datos/resume")
    @limiter.limit("60/minute")
    async def get_datos_resume(request: Request):
        """Obtener resumen de datos por categorías"""
        nocache = request.query_params.get("nocache", "0") == "1"

        if not nocache:
            cached_summary = cache.get("data_summary")
            if cached_summary:
                return JSONResponse(content=cached_summary)

        try:
            data = await scrape_all_data(http_client, settings)
            summary = create_data_summary(data)
            cache["data_summary"] = summary
            return JSONResponse(content=summary)
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    @app.post("/scrape")
    @limiter.limit("5/minute")
    async def manual_scrape(request: Request, scrape_req: ScrapeRequest):
        """Ejecutar scraping manualmente con filtros opcionales"""
        try:
            data = await scrape_all_data(http_client, settings, scrape_req)
            return JSONResponse(content=data)
        except Exception as e:
            logger.error(f"Error en scraping manual: {e}")
            raise HTTPException(status_code=500, detail="Error en scraping")

    # Cleanup
    @app.on_event("shutdown")
    async def shutdown_event():
        await http_client.aclose()

    return app


def get_sources_status(settings: Settings) -> Dict[str, Dict[str, Any]]:
    """Obtener estado de las fuentes disponibles"""
    sources = {
        "finviz": {
            "name": "Finviz",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex"],
            "requires_browser": False,
        },
        "yahoo": {
            "name": "Yahoo Finance",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex", "materias_primas", "etfs"],
            "requires_browser": False,
        },
    }

    # En Vercel, deshabilitar fuentes que requieren navegador
    if settings.runtime == "vercel":
        sources["tradingview"] = {
            "name": "TradingView",
            "status": "browser_required_disabled_in_prod",
            "data_types": ["indices", "acciones", "forex", "cripto"],
            "requires_browser": True,
        }
    else:
        sources["tradingview"] = {
            "name": "TradingView",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex", "cripto"],
            "requires_browser": True,
        }

    return sources


async def scrape_all_data(
    http_client: httpx.AsyncClient, settings: Settings, scrape_req: Optional[ScrapeRequest] = None
) -> Dict[str, Any]:
    """Scrapear todos los datos de las fuentes habilitadas"""
    logger.info("🚀 Iniciando scraping de todas las fuentes")

    # Determinar fuentes a scrapear
    sources_status = get_sources_status(settings)
    enabled_sources = [name for name, info in sources_status.items() if info["status"] == "ok"]

    if scrape_req and scrape_req.sources:
        enabled_sources = [s for s in enabled_sources if s in scrape_req.sources]

    # Crear tareas para scraping asíncrono
    tasks = []
    for source in enabled_sources:
        task = scrape_source(http_client, source, settings, scrape_req)
        tasks.append(task)

    # Ejecutar scraping en paralelo
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Procesar resultados
    scraped_data = {}
    errors = []

    for i, source in enumerate(enabled_sources):
        result = results[i]
        if isinstance(result, Exception):
            logger.error(f"❌ Error en {source}: {result}")
            errors.append({"source": source, "error": str(result)})
            scraped_data[source] = {}
        else:
            scraped_data[source] = result

    return {
        "data": scraped_data,
        "errors": errors,
        "timestamp": time.time(),
        "sources_scraped": enabled_sources,
        "total_sources": len(enabled_sources),
    }


async def scrape_source(
    http_client: httpx.AsyncClient, source: str, settings: Settings, scrape_req: Optional[ScrapeRequest] = None
) -> Dict[str, List[Dict[str, str]]]:
    """Scrapear una fuente específica"""
    logger.info(f"🔄 Iniciando scraping de {source}")

    if source == "finviz":
        return await scrape_finviz(http_client, scrape_req)
    elif source == "yahoo":
        return await scrape_yahoo(http_client, scrape_req)
    elif source == "tradingview":
        if settings.runtime == "vercel":
            return {"error": "browser_required_disabled_in_prod"}
        else:
            return await scrape_tradingview(http_client, scrape_req)
    else:
        return {}


def create_data_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crear resumen de datos por categorías"""
    summary = {
        "indices": [],
        "acciones": [],
        "forex": [],
        "materias_primas": [],
        "etfs": [],
        "cripto": [],
        "last_updated": time.time(),
        "sources": {},
    }

    for source, source_data in data.get("data", {}).items():
        source_summary = {"has_data": False, "data_types": {}}

        for data_type, items in source_data.items():
            if items and len(items) > 0:
                summary[data_type].extend(items[:10])  # Top 10 por categoría
                source_summary["data_types"][data_type] = len(items)
                source_summary["has_data"] = True

        summary["sources"][source] = source_summary

    # Limitar resumen a top 20 por categoría
    for category in summary:
        if isinstance(summary[category], list):
            summary[category] = summary[category][:20]

    return summary


# (fin imports)
