import base64
import json
import os
import time
from typing import Any, Dict, List, Optional

import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Crear aplicación FastAPI específica para el receiver
app = FastAPI(
    title="Financial Data Receiver API",
    description="API para recibir y procesar datos desde bots externos",
    version="1.0.0",
    docs_url="/api/receiver/docs",
    redoc_url="/api/receiver/redoc",
)

# CORS deshabilitado por defecto. Para habilitar, exporta ENABLE_CORS=true y CORS_ORIGINS
ENABLE_CORS = (os.getenv("ENABLE_CORS", "false").lower() in ("1", "true", "yes"))
if ENABLE_CORS:
    ORIGINS = [o for o in (os.getenv("CORS_ORIGINS", "").split(",")) if o]
    if ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=ORIGINS,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Accept", "User-Agent", "Authorization", "x-api-key"],
            max_age=3600,
        )

# Configurar rate limiting
app.state.limiter = limiter
# Middleware de autenticación (soporta AUTH_MODE=none|apikey|basic|jwt)
AUTH_MODE = os.getenv("AUTH_MODE", "none").lower()
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
JWT_ISSUER = os.getenv("JWT_ISSUER", "")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "")


def decode_jwt(token: str):
    if not JWT_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="JWT_PUBLIC_KEY no configurado")
    try:
        return jwt.decode(
            token,
            JWT_PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": bool(JWT_ISSUER),
                "verify_aud": bool(JWT_AUDIENCE),
            },
        )
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Permitir preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in ("/health", "/docs", "/openapi.json"):
        return await call_next(request)

    mode = AUTH_MODE
    if mode in ("none", "off", "disabled"):
        return await call_next(request)

    if mode == "apikey":
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

    if mode == "basic":
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("basic "):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        try:
            b64 = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(b64).decode("utf-8")
            user, pwd = decoded.split(":", 1)
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        basic_user = os.getenv("BASIC_USER", "")
        basic_pwd = os.getenv("BASIC_PASSWORD", "")
        if user == basic_user and pwd == basic_pwd and user and pwd:
            return await call_next(request)
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    if mode == "jwt":
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing Bearer token"})
        token = auth_header.split(" ", 1)[1].strip()
        try:
            _ = decode_jwt(token)
            return await call_next(request)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


class DataPayload(BaseModel):
    """Modelo para recibir datos del bot"""

    source: str = Field(..., description="Fuente de los datos (ej: 'bot_telegram')")
    data_type: str = Field(..., description="Tipo de datos (ej: 'market_update')")
    payload: Dict[str, Any] = Field(..., description="Datos principales")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos adicionales")
    timestamp: Optional[float] = Field(default=None, description="Timestamp del evento")


class ProcessingResult(BaseModel):
    """Resultado del procesamiento"""

    success: bool
    message: str
    processed_at: float
    data_id: Optional[str] = None


@app.get("/")
@limiter.limit("60/minute")
async def receiver_root(request: Request):
    """Información del endpoint receiver"""
    return {
        "service": "Financial Data Receiver",
        "version": "1.0.0",
        "description": "Endpoint para recibir datos desde bots externos",
        "endpoints": {
            "/": "Información del servicio",
            "/health": "Health check",
            "/receive": "Recibir datos (POST)",
            "/status": "Estado del procesamiento",
        },
        "timestamp": time.time(),
    }


@app.get("/health")
@limiter.limit("100/minute")
async def receiver_health(request: Request):
    """Health check del receiver"""
    return {
        "ok": True,
        "service": "receiver",
        "timestamp": time.time(),
        "status": "operational",
    }


@app.post("/receive")
@limiter.limit("30/minute")
async def receive_data(request: Request, data: DataPayload) -> ProcessingResult:
    """
    Recibir y procesar datos desde bots externos

    Este endpoint puede ser usado por:
    - Bots de Telegram
    - Webhooks externos
    - Sistemas de monitoreo
    - Scripts automatizados
    """
    try:
        # Asignar timestamp si no se proporciona
        if data.timestamp is None:
            data.timestamp = time.time()

        # Validar datos básicos
        if not data.source or not data.data_type:
            raise HTTPException(status_code=400, detail="Los campos 'source' y 'data_type' son obligatorios")

        # Procesar los datos (aquí puedes agregar lógica específica)
        processed_data = await process_received_data(data)

        # Generar ID único para el procesamiento
        data_id = f"{data.source}_{data.data_type}_{int(data.timestamp)}"

        return ProcessingResult(
            success=True,
            message=f"Datos recibidos y procesados correctamente desde {data.source}",
            processed_at=time.time(),
            data_id=data_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando datos: {str(e)}")


@app.get("/status")
@limiter.limit("60/minute")
async def get_processing_status(request: Request):
    """Obtener estado del procesamiento de datos"""
    return {
        "status": "operational",
        "last_processed": time.time(),
        "total_processed": 0,  # En una implementación real, esto vendría de una base de datos
        "sources_active": ["bot_telegram", "webhook_external"],
        "timestamp": time.time(),
    }


async def process_received_data(data: DataPayload) -> Dict[str, Any]:
    """
    Procesar los datos recibidos según el tipo y fuente

    Aquí puedes implementar lógica específica para:
    - Validar datos
    - Transformar formato
    - Almacenar temporalmente
    - Enviar notificaciones
    - Integrar con otros sistemas
    """

    # Ejemplo de procesamiento básico
    processed = {
        "source": data.source,
        "data_type": data.data_type,
        "received_at": time.time(),
        "payload_size": len(str(data.payload)),
        "has_metadata": data.metadata is not None,
    }

    # Lógica específica por tipo de datos
    if data.data_type == "market_update":
        # Procesar actualización de mercado
        processed["market_data"] = True

    elif data.data_type == "alert":
        # Procesar alerta
        processed["alert_processed"] = True

    elif data.data_type == "status_update":
        # Procesar actualización de estado
        processed["status_updated"] = True

    # En una implementación real, aquí podrías:
    # - Guardar en base de datos
    # - Enviar a cola de mensajes
    # - Activar webhooks
    # - Generar notificaciones

    return processed


# Endpoint adicional para debugging (solo en desarrollo)
@app.post("/debug/echo")
@limiter.limit("10/minute")
async def debug_echo(request: Request, payload: Dict[str, Any]):
    """Endpoint de debug que devuelve lo que recibe"""
    return {
        "received": payload,
        "timestamp": time.time(),
        "headers": dict(request.headers),
        "method": request.method,
    }
