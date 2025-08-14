import asyncio
import threading
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from scraper_manager import scraper_manager
from data_store import get_data, get_data_summary
from endpoint_generator import endpoint_generator
from cache_manager import cache_manager
from database import init_db
from config import (
    SCRAPING_INTERVAL_MINUTES, 
    CORS_ORIGINS, 
    CORS_ALLOW_CREDENTIALS, 
    CORS_ALLOW_METHODS, 
    CORS_ALLOW_HEADERS,
    CORS_MAX_AGE
)
from logger import logger, log_api_request

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Financial Data API",
    description="API para obtener datos financieros de múltiples fuentes",
    version="2.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Add CORS middleware - Muy Seguro
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
    max_age=CORS_MAX_AGE,
)

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global scheduler
scheduler = None

async def scraping_job():
    """Main scraping job that runs all scrapers asynchronously"""
    logger.info("🚀 Iniciando job de scraping programado...")
    
    try:
        # Use the new scraper manager for async scraping
        await scraper_manager.scrape_all_async()
        logger.info("✅ Job de scraping completado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error crítico en job de scraping: {e}")

def run_scraping_job():
    """Wrapper to run async scraping job in sync context"""
    asyncio.run(scraping_job())

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global scheduler
    
    logger.info("🚀 Iniciando Financial Data API v2.0...")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.warning(f"⚠️ Error inicializando base de datos: {e}")
    
    # Start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scraping_job,
        trigger=IntervalTrigger(minutes=SCRAPING_INTERVAL_MINUTES),
        id="scraping_job",
        name="Scraping Job",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"⏰ Scheduler iniciado - intervalo: {SCRAPING_INTERVAL_MINUTES} minutos")
    
    # Run initial scraping job
    threading.Thread(target=run_scraping_job, daemon=True).start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("🛑 Scheduler detenido")

@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    """Root endpoint with API information"""
    log_api_request("GET", "/")
    return {
        "message": "Financial Data API",
        "version": "2.0.0",
        "description": "API optimizada para datos financieros de múltiples fuentes",
        "features": [
            "Scraping asíncrono mejorado",
            "Sistema de cache inteligente",
            "Base de datos SQLite",
            "Rate limiting",
            "Endpoints dinámicos",
            "Tests automatizados"
        ],
        "endpoints": {
            "general": {
                "/datos": "Obtener todos los datos financieros",
                "/datos/resume": "Obtener resumen de datos",
                "/health": "Verificar estado de la API",
                "/scrape": "Ejecutar scraping manualmente",
                "/sources": "Información de fuentes disponibles"
            },
            "por_tipo": {
                "/datos/indices": "Índices bursátiles de todas las fuentes",
                "/datos/acciones": "Acciones de todas las fuentes",
                "/datos/cripto": "Criptomonedas",
                "/datos/forex": "Forex de todas las fuentes",
                "/datos/etfs": "ETFs",
                "/datos/materias-primas": "Materias primas"
            },
            "por_fuente": {
                "/datos/tradingview": "Todos los datos de TradingView",
                "/datos/finviz": "Todos los datos de Finviz",
                "/datos/yahoo": "Todos los datos de Yahoo Finance"
            },
            "especifico": {
                "/datos/{fuente}/{tipo}": "Datos específicos por fuente y tipo"
            }
        },
        "cache_info": {
            "enabled": True,
            "ttl": "5 minutos",
            "strategy": "Redis con fallback a memoria"
        }
    }

@app.get("/datos")
@limiter.limit("30/minute")
async def get_datos(request: Request):
    """Get all financial data"""
    log_api_request("GET", "/datos")
    try:
        data = get_data()
        return JSONResponse(content=data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/resume")
@limiter.limit("60/minute")
async def get_datos_resume(request: Request):
    """Get data resume"""
    log_api_request("GET", "/datos/resume")
    try:
        summary = get_data_summary()
        return JSONResponse(content=summary, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/scrape")
@limiter.limit("5/minute")
async def manual_scrape(request: Request):
    """Manually trigger scraping"""
    log_api_request("POST", "/scrape")
    try:
        # Run scraping in background
        threading.Thread(target=run_scraping_job, daemon=True).start()
        return {"message": "Scraping iniciado manualmente", "status": "running"}
    except Exception as e:
        logger.error(f"❌ Error iniciando scraping manual: {e}")
        raise HTTPException(status_code=500, detail="Error iniciando scraping")

@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    log_api_request("GET", "/health")
    try:
        summary = get_data_summary()
        return {
            "status": "healthy",
            "version": "2.0.0",
            "last_updated": summary.get("last_updated"),
            "sources_available": len([s for s in summary.get("sources", {}).values() if s.get("has_data")]),
            "cache_status": "active" if cache_manager.redis_client else "memory_only"
        }
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/sources")
@limiter.limit("30/minute")
async def get_sources_info(request: Request):
    """Get information about available sources"""
    log_api_request("GET", "/sources")
    try:
        sources_info = {}
        for source_name in scraper_manager.get_available_sources():
            sources_info[source_name] = scraper_manager.get_source_info(source_name)
        
        return {
            "sources": sources_info,
            "total_sources": len(sources_info)
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo información de fuentes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Include dynamic endpoints from endpoint generator
app.include_router(endpoint_generator.router, prefix="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
