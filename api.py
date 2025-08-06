from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
from data_store import update_data, get_data, get_data_summary
from config import (
    CORS_ORIGINS, 
    CORS_ALLOW_CREDENTIALS, 
    CORS_ALLOW_METHODS, 
    CORS_ALLOW_HEADERS
)
from logger import logger, log_api_request

app = FastAPI(
    title="Financial Data Receiver API",
    description="API para recibir datos de scraping desde el bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    log_api_request("GET", "/")
    return {
        "message": "Financial Data Receiver API",
        "version": "1.0.0",
        "endpoints": {
            "/update_data": "POST - Recibir datos de scraping",
            "/datos": "GET - Obtener datos almacenados",
            "/datos/resume": "GET - Obtener resumen de datos"
        }
    }

@app.post("/update_data")
async def receive_data(request: Request):
    """Receive scraped data from bot"""
    log_api_request("POST", "/update_data")
    
    try:
        data = await request.json()
        
        # Validate data structure
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Datos deben ser un objeto JSON")
        
        # Extract data with defaults
        tv_data = data.get("tradingview", {})
        fz_data = data.get("finviz", {})
        yh_data = data.get("yahoo", {})
        
        # Validate that at least one source has data
        if not any([tv_data, fz_data, yh_data]):
            logger.warning("⚠️ Datos recibidos sin contenido válido")
            return JSONResponse(
                content={"status": "warning", "message": "Datos recibidos sin contenido válido"},
                status_code=200
            )
        
        # Update data store
        update_data(tv_data, fz_data, yh_data)
        
        # Log success
        sources_received = []
        if tv_data: sources_received.append("TradingView")
        if fz_data: sources_received.append("Finviz")
        if yh_data: sources_received.append("Yahoo")
        
        logger.info(f"✅ Datos recibidos de: {', '.join(sources_received)}")
        
        return JSONResponse(
            content={
                "status": "ok",
                "message": "Datos actualizados correctamente",
                "sources_received": sources_received
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando datos recibidos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos")
async def get_datos():
    """Get all stored data"""
    log_api_request("GET", "/datos")
    try:
        data = get_data()
        return JSONResponse(content=data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/resume")
async def get_datos_resume():
    """Get data resume"""
    log_api_request("GET", "/datos/resume")
    try:
        summary = get_data_summary()
        return JSONResponse(content=summary, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    log_api_request("GET", "/health")
    try:
        summary = get_data_summary()
        return {
            "status": "healthy",
            "last_updated": summary.get("last_updated"),
            "sources_available": len([s for s in summary.get("sources", {}).values() if s.get("has_data")])
        }
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        return {"status": "unhealthy", "error": str(e)}
