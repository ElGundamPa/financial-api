# Despliegue en Vercel - Financial Data API

## 🚀 Resumen

Esta API ha sido optimizada para funcionar en Vercel como funciones serverless sin base de datos, usando cache en memoria efímero y scraping HTTP-only.

## 📋 Características Implementadas

### ✅ Completado
- [x] Estructura para Vercel (`api/index.py`)
- [x] Configuración `vercel.json`
- [x] Cache en memoria con TTL (90 segundos)
- [x] Rate limiting (60 RPM por defecto)
- [x] CORS configurado
- [x] Timeouts estrictos (12 segundos)
- [x] Scrapers HTTP-only (Finviz, Yahoo)
- [x] TradingView deshabilitado en producción
- [x] Headers de cache apropiados
- [x] Validación de tamaño de body
- [x] Logging estructurado
- [x] Variables de entorno configurables

### 🔧 Limitaciones Serverless
- **Cache efímero**: Los datos se pierden entre invocaciones
- **Sin TradingView**: Requiere navegador, deshabilitado en Vercel
- **Timeouts**: Máximo 10 segundos por función
- **Memoria**: Límite de 1024MB por función

## 🛠️ Estructura de Archivos

```
financial_api/
├── api/
│   └── index.py              # Punto de entrada para Vercel
├── scrapers/
│   ├── http_finviz.py        # Scraper HTTP para Finviz
│   ├── http_yahoo.py         # Scraper HTTP para Yahoo
│   └── http_tradingview.py   # Scraper HTTP para TradingView (solo local)
├── app_core.py               # Factory de aplicación FastAPI
├── app_core_simple.py        # Versión simplificada para testing
├── vercel.json               # Configuración de Vercel
├── requirements.txt          # Dependencias optimizadas
├── env.example               # Variables de entorno
└── Makefile                  # Comandos de desarrollo
```

## 🚀 Despliegue

### Opción 1: Despliegue Automático

1. **Conectar repositorio en Vercel**
   - Ve a [vercel.com](https://vercel.com)
   - Conecta tu repositorio de GitHub
   - Selecciona la rama `deploy/vercel`

2. **Configurar variables de entorno**
   ```bash
   CORS_ORIGINS=https://tu-frontend.com
   RATE_LIMIT_RPM=60
   HTTP_TIMEOUT_SECONDS=12
   CACHE_TTL_SECONDS=90
   MAX_BODY_KB=128
   ```

3. **Desplegar**
   - Vercel detectará automáticamente la configuración
   - La API estará disponible en `https://tu-proyecto.vercel.app`

### Opción 2: Despliegue Manual

1. **Instalar Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login en Vercel**
   ```bash
   vercel login
   ```

3. **Desplegar**
   ```bash
   vercel --prod
   ```

## 📡 Endpoints

### GET /
Información de la API y estado de fuentes

### GET /health
Health check con información del runtime

### GET /sources
Lista de fuentes disponibles y su estado

### GET /datos
Obtener todos los datos financieros
- Query param: `?nocache=1` para forzar refresh

### GET /datos/resume
Resumen de datos por categorías
- Query param: `?nocache=1` para forzar refresh

### POST /scrape
Ejecutar scraping manualmente
```json
{
  "sources": ["finviz", "yahoo"],
  "categories": ["indices", "acciones"],
  "force_refresh": false
}
```

## 🔧 Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
python test_vercel.py

# Usar Makefile
make dev

# O directamente
uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `http://localhost:3000` |
| `RATE_LIMIT_RPM` | Requests por minuto | `60` |
| `HTTP_TIMEOUT_SECONDS` | Timeout para requests HTTP | `12` |
| `CACHE_TTL_SECONDS` | TTL del cache en memoria | `90` |
| `MAX_BODY_KB` | Tamaño máximo de body en KB | `128` |

## 🧪 Testing

```bash
# Probar funcionalidad básica
python test_vercel.py

# Probar endpoints (si FastAPI funciona)
curl http://localhost:8000/health
curl http://localhost:8000/sources
curl http://localhost:8000/datos
```

## 🔍 Troubleshooting

### Error de compatibilidad FastAPI/Pydantic
- Usar `app_core_simple.py` para testing
- Las dependencias están optimizadas para Vercel

### Error de scraping
- Verificar conectividad a internet
- Los scrapers usan datos mock por ahora

### Error de cache
- El cache es efímero por instancia
- Usar `?nocache=1` para forzar refresh

## 📈 Próximos Pasos

1. **Implementar scrapers reales**: Reemplazar datos mock con scraping HTTP real
2. **Optimizar selectores**: Mejorar parsing de HTML para mayor robustez
3. **Añadir tests**: Tests unitarios y de integración
4. **Monitoreo**: Logs y métricas de rendimiento
5. **CDN**: Considerar cache en CDN para datos estáticos

## 🎯 Estado Actual

- ✅ **Estructura serverless**: Completada
- ✅ **Configuración Vercel**: Completada
- ✅ **Cache en memoria**: Completado
- ✅ **Rate limiting**: Completado
- ✅ **CORS**: Completado
- 🔄 **Scrapers reales**: En progreso (datos mock)
- ⏳ **Tests**: Pendiente
- ⏳ **Monitoreo**: Pendiente

La API está lista para desplegar en Vercel con funcionalidad básica operativa.
