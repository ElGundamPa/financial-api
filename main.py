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
from config import SCRAPING_INTERVAL_MINUTES
from logger import logger, log_api_request

app = FastAPI(
    title="Financial Data API",
    description="API para obtener datos financieros de múltiples fuentes",
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
        "version": "1.0.0",
        "endpoints": {
            "/datos": "Obtener todos los datos financieros",
            "/datos/summary": "Obtener resumen de datos",
            "/scrape": "Ejecutar scraping manualmente"
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

@app.get("/datos/summary")
async def get_datos_summary():
    """Get data summary"""
    log_api_request("GET", "/datos/summary")
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
