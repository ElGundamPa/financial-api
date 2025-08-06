import asyncio
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scraper.tradingview import scrape_tradingview
from scraper.finviz import scrape_finviz
from scraper.yahoo import scrape_yahoo
from data_store import update_data, get_data, get_data_summary
from config import (
    SCRAPING_INTERVAL_MINUTES, 
    CORS_ORIGINS, 
    CORS_ALLOW_CREDENTIALS, 
    CORS_ALLOW_METHODS, 
    CORS_ALLOW_HEADERS,
    CORS_MAX_AGE
)
from logger import logger, log_api_request

app = FastAPI(
    title="Financial Data API",
    description="API para obtener datos financieros de múltiples fuentes",
    version="1.0.0"
)

# Add CORS middleware - Muy Seguro
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
    max_age=CORS_MAX_AGE,
)

# Global scheduler
scheduler = None

async def scraping_job():
    """Main scraping job that runs all scrapers"""
    logger.info("🚀 Iniciando job de scraping programado...")
    
    try:
        # Run Finviz and Yahoo concurrently (they are async)
        async_tasks = [
            scrape_finviz(),
            scrape_yahoo()
        ]
        
        # Run TradingView synchronously in a thread to avoid blocking
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit TradingView scraping to thread pool
            tv_future = executor.submit(scrape_tradingview)
            
            # Run async scrapers
            async_results = await asyncio.gather(*async_tasks, return_exceptions=True)
            
            # Get TradingView result
            try:
                tv = tv_future.result(timeout=120)  # 2 minutes timeout
            except Exception as e:
                logger.error(f"❌ Error en TradingView: {e}")
                tv = {}
        
        # Extract results and handle exceptions
        fz, yh = {}, {}
        
        if not isinstance(async_results[0], Exception):
            fz = async_results[0]
        else:
            logger.error(f"❌ Error en Finviz: {async_results[0]}")
            
        if not isinstance(async_results[1], Exception):
            yh = async_results[1]
        else:
            logger.error(f"❌ Error en Yahoo: {async_results[1]}")
        
        # Update data store
        update_data(tv, fz, yh)
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
    
    logger.info("🚀 Iniciando Financial Data API...")
    
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
async def root():
    """Root endpoint with API information"""
    log_api_request("GET", "/")
    return {
        "message": "Financial Data API",
        "version": "1.1.0",
        "description": "API organizada para datos financieros de múltiples fuentes",
        "endpoints": {
            "general": {
                "/datos": "Obtener todos los datos financieros",
                "/datos/resume": "Obtener resumen de datos",
                "/health": "Verificar estado de la API",
                "/scrape": "Ejecutar scraping manualmente"
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
            "yahoo_especifico": {
                "/datos/yahoo/gainers": "Acciones con mayor ganancia",
                "/datos/yahoo/losers": "Acciones con mayor pérdida",
                "/datos/yahoo/most-active": "Acciones y ETFs más activos",
                "/datos/yahoo/undervalued": "Acciones de crecimiento infravaloradas"
            }
        }
    }

@app.get("/datos")
async def get_datos():
    """Get all financial data"""
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

@app.post("/scrape")
async def manual_scrape():
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

# ===== NUEVOS ENDPOINTS ORGANIZADOS =====

# === ENDPOINTS POR TIPO DE DATO ===

@app.get("/datos/indices")
async def get_indices():
    """Get all indices data from all sources"""
    log_api_request("GET", "/datos/indices")
    try:
        data = get_data()
        indices_data = {
            "tradingview": data.get("tradingview", {}).get("indices", []),
            "finviz": data.get("finviz", {}).get("indices", []),
            "yahoo": data.get("yahoo", {}).get("indices", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=indices_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo índices: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/acciones")
async def get_acciones():
    """Get all stocks data from all sources"""
    log_api_request("GET", "/datos/acciones")
    try:
        data = get_data()
        acciones_data = {
            "tradingview": data.get("tradingview", {}).get("acciones", []),
            "finviz": data.get("finviz", {}).get("acciones", []),
            "yahoo": {
                "gainers": data.get("yahoo", {}).get("gainers", []),
                "losers": data.get("yahoo", {}).get("losers", []),
                "most_active": data.get("yahoo", {}).get("most_active_stocks", [])
            },
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=acciones_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo acciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/cripto")
async def get_cripto():
    """Get all cryptocurrency data"""
    log_api_request("GET", "/datos/cripto")
    try:
        data = get_data()
        cripto_data = {
            "tradingview": data.get("tradingview", {}).get("cripto", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=cripto_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo cripto: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/forex")
async def get_forex():
    """Get all forex data from all sources"""
    log_api_request("GET", "/datos/forex")
    try:
        data = get_data()
        forex_data = {
            "tradingview": data.get("tradingview", {}).get("forex", []),
            "finviz": data.get("finviz", {}).get("forex", []),
            "yahoo": data.get("yahoo", {}).get("forex", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=forex_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo forex: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/etfs")
async def get_etfs():
    """Get all ETFs data"""
    log_api_request("GET", "/datos/etfs")
    try:
        data = get_data()
        etfs_data = {
            "yahoo": data.get("yahoo", {}).get("most_active_etfs", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=etfs_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo ETFs: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/materias-primas")
async def get_materias_primas():
    """Get all commodities data"""
    log_api_request("GET", "/datos/materias-primas")
    try:
        data = get_data()
        commodities_data = {
            "yahoo": data.get("yahoo", {}).get("materias_primas", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=commodities_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo materias primas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# === ENDPOINTS POR FUENTE ===

@app.get("/datos/tradingview")
async def get_tradingview_data():
    """Get all TradingView data"""
    log_api_request("GET", "/datos/tradingview")
    try:
        data = get_data()
        tv_data = {
            "indices": data.get("tradingview", {}).get("indices", []),
            "acciones": data.get("tradingview", {}).get("acciones", []),
            "cripto": data.get("tradingview", {}).get("cripto", []),
            "forex": data.get("tradingview", {}).get("forex", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=tv_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de TradingView: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/finviz")
async def get_finviz_data():
    """Get all Finviz data"""
    log_api_request("GET", "/datos/finviz")
    try:
        data = get_data()
        fv_data = {
            "forex": data.get("finviz", {}).get("forex", []),
            "acciones": data.get("finviz", {}).get("acciones", []),
            "indices": data.get("finviz", {}).get("indices", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=fv_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de Finviz: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/yahoo")
async def get_yahoo_data():
    """Get all Yahoo Finance data"""
    log_api_request("GET", "/datos/yahoo")
    try:
        data = get_data()
        yh_data = {
            "forex": data.get("yahoo", {}).get("forex", []),
            "gainers": data.get("yahoo", {}).get("gainers", []),
            "losers": data.get("yahoo", {}).get("losers", []),
            "most_active_stocks": data.get("yahoo", {}).get("most_active_stocks", []),
            "most_active_etfs": data.get("yahoo", {}).get("most_active_etfs", []),
            "undervalued_growth": data.get("yahoo", {}).get("undervalued_growth", []),
            "materias_primas": data.get("yahoo", {}).get("materias_primas", []),
            "indices": data.get("yahoo", {}).get("indices", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=yh_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de Yahoo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# === ENDPOINTS ESPECÍFICOS DE YAHOO ===

@app.get("/datos/yahoo/gainers")
async def get_yahoo_gainers():
    """Get Yahoo Finance gainers data"""
    log_api_request("GET", "/datos/yahoo/gainers")
    try:
        data = get_data()
        gainers_data = {
            "gainers": data.get("yahoo", {}).get("gainers", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=gainers_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo gainers: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/yahoo/losers")
async def get_yahoo_losers():
    """Get Yahoo Finance losers data"""
    log_api_request("GET", "/datos/yahoo/losers")
    try:
        data = get_data()
        losers_data = {
            "losers": data.get("yahoo", {}).get("losers", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=losers_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo losers: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/yahoo/most-active")
async def get_yahoo_most_active():
    """Get Yahoo Finance most active data"""
    log_api_request("GET", "/datos/yahoo/most-active")
    try:
        data = get_data()
        most_active_data = {
            "stocks": data.get("yahoo", {}).get("most_active_stocks", []),
            "etfs": data.get("yahoo", {}).get("most_active_etfs", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=most_active_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo most active: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/datos/yahoo/undervalued")
async def get_yahoo_undervalued():
    """Get Yahoo Finance undervalued growth stocks data"""
    log_api_request("GET", "/datos/yahoo/undervalued")
    try:
        data = get_data()
        undervalued_data = {
            "undervalued_growth": data.get("yahoo", {}).get("undervalued_growth", []),
            "last_updated": data.get("last_updated")
        }
        return JSONResponse(content=undervalued_data, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error obteniendo undervalued: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
