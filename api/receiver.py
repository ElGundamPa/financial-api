import os
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# Crear aplicación FastAPI minimalista para receiver
app = FastAPI(
    title="Financial Data Receiver API",
    description="API para recibir y procesar datos desde bots externos",
    version="1.0.0",
    docs_url="/api/receiver/docs",
    redoc_url="/api/receiver/redoc",
    root_path="/api/receiver",
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
    """Endpoint raíz del receiver"""
    return {
        "message": "Financial Data Receiver API",
        "version": "1.0.0",
        "runtime": "vercel",
        "description": "API para recibir datos desde bots externos",
        "endpoints": {
            "/health": "Verificar estado de la API",
            "/receive": "Recibir datos (POST)",
            "/status": "Estado del receiver",
        },
        "auth_mode": AUTH_MODE,
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "ok": True,
        "time": time.time(),
        "version": "1.0.0",
        "runtime": "vercel",
        "auth_mode": AUTH_MODE,
        "service": "receiver",
    }

@app.get("/status")
async def get_status():
    """Obtener estado del receiver"""
    return {
        "status": "operational",
        "uptime": time.time(),
        "version": "1.0.0",
        "runtime": "vercel",
        "auth_mode": AUTH_MODE,
        "last_data_received": None,
        "total_requests": 0,
    }

@app.post("/receive")
async def receive_data(request: Request):
    """Recibir datos desde bots externos"""
    try:
        # Intentar leer el body como JSON
        body = await request.json()
    except:
        body = {"error": "Invalid JSON"}

    return {
        "status": "received",
        "timestamp": time.time(),
        "data_size": len(str(body)),
        "message": "Datos recibidos correctamente",
        "received_data": body,
    }

@app.get("/debug/echo")
async def debug_echo(request: Request):
    """Endpoint de debug para verificar la configuración"""
    return {
        "message": "Debug echo endpoint",
        "timestamp": time.time(),
        "headers": dict(request.headers),
        "method": request.method,
        "url": str(request.url),
        "auth_mode": AUTH_MODE,
        "api_keys_configured": len(API_KEYS) > 0,
    }
