import os
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# Crear aplicación FastAPI minimalista
app = FastAPI(
    title="Financial Data API",
    description="API para obtener datos financieros - Serverless Ready",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path="/api/index",
)

# Configuración básica
AUTH_MODE = os.getenv("AUTH_MODE", "apikey").lower()
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "mF9zX2q7Lr4pK8yD1sBvWj").split(",") if k.strip()]

# Middleware de autenticación simple
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    if AUTH_MODE == "none":
        return await call_next(request)

    if AUTH_MODE == "apikey":
        api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
        auth_header = request.headers.get("authorization") or ""
        token = (
            api_key.strip()
            if api_key
            else (auth_header.split(" ", 1)[1].strip() if auth_header.lower().startswith("apikey ") else None)
        )
        if token and token in API_KEYS:
            return await call_next(request)
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)

# Endpoints básicos
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Financial Data API - Serverless Ready",
        "version": "2.1.0",
        "runtime": "vercel",
        "description": "API optimizada para datos financieros",
        "endpoints": {
            "general": {
                "/datos": "Obtener todos los datos financieros",
                "/datos/resume": "Obtener resumen de datos",
                "/health": "Verificar estado de la API",
                "/sources": "Información de fuentes disponibles",
            }
        },
        "auth_mode": AUTH_MODE,
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "ok": True,
        "time": time.time(),
        "version": "2.1.0",
        "runtime": "vercel",
        "auth_mode": AUTH_MODE,
    }

@app.get("/sources")
async def get_sources():
    """Obtener información de fuentes disponibles"""
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
        "tradingview": {
            "name": "TradingView",
            "status": "browser_required_disabled_in_prod",
            "data_types": ["indices", "acciones", "forex", "cripto"],
            "requires_browser": True,
        },
    }
    return {"sources": sources, "total_sources": len(sources), "runtime": "vercel"}

@app.get("/datos")
async def get_datos():
    """Obtener datos financieros básicos"""
    return {
        "data": {
            "finviz": {
                "indices": [
                    {"symbol": "SPY", "name": "S&P 500", "change": "+0.5%"},
                    {"symbol": "QQQ", "name": "NASDAQ", "change": "+0.3%"},
                ],
                "acciones": [
                    {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.2%"},
                    {"symbol": "MSFT", "name": "Microsoft", "change": "+0.8%"},
                ],
            },
            "yahoo": {
                "forex": [
                    {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.1%"},
                    {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.2%"},
                ],
            },
        },
        "timestamp": time.time(),
        "sources_scraped": ["finviz", "yahoo"],
        "total_sources": 2,
        "note": "Datos de ejemplo - scraping deshabilitado temporalmente",
    }

@app.get("/datos/resume")
async def get_datos_resume():
    """Obtener resumen de datos por categorías"""
    return {
        "indices": [
            {"symbol": "SPY", "name": "S&P 500", "change": "+0.5%"},
            {"symbol": "QQQ", "name": "NASDAQ", "change": "+0.3%"},
        ],
        "acciones": [
            {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.2%"},
            {"symbol": "MSFT", "name": "Microsoft", "change": "+0.8%"},
        ],
        "forex": [
            {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.1%"},
            {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.2%"},
        ],
        "last_updated": time.time(),
        "note": "Resumen de ejemplo - scraping deshabilitado temporalmente",
    }
