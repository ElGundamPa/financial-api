# Financial Data API v2.1.0 - Serverless Ready

Una API optimizada para obtener datos financieros de múltiples fuentes (Finviz, Yahoo Finance) con scraping HTTP-only, cache en memoria efímero y optimizada para despliegue serverless en Vercel.

## 🚀 Características

- **Múltiples fuentes de datos**: Finviz, Yahoo Finance (HTTP-only)
- **Scraping asíncrono**: Ejecución paralela para mejor rendimiento
- **Cache en memoria**: TTL efímero optimizado para serverless
- **Sin base de datos**: Todo viaja en request/response
- **Rate limiting**: Protección contra spam
- **CORS configurado**: Seguridad para frontends
- **Compresión GZip**: Optimización de transferencia
- **Timeouts estrictos**: Robustez en entornos serverless
- **API RESTful**: Endpoints organizados y documentados
- **Vercel Ready**: Despliegue serverless optimizado

## 📋 Requisitos

- Python 3.12+
- Conexión a internet
- Vercel CLI (para despliegue)

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <tu-repositorio>
cd financial_api
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno (opcional)**
```bash
# Copiar archivo de ejemplo
cp env.example .env
# Editar según necesidades
```

## 🚀 Uso

### Opción 1: Docker (Recomendado)

```bash
# Usar docker-compose (incluye Redis)
docker-compose up -d

# O solo la API
docker build -t financial-api .
docker run -p 8000:8000 financial-api
```

### Opción 2: Local con Redis

```bash
# Instalar Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Iniciar la API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Opción 3: Local sin Redis (fallback a memoria)

```bash
# Iniciar la API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints disponibles:**
- `GET /` - Información de la API
- `GET /datos` - Obtener todos los datos financieros
- `GET /datos/resume` - Obtener resumen de datos
- `GET /sources` - Información de fuentes disponibles
- `POST /scrape` - Ejecutar scraping manualmente
- `GET /health` - Verificar estado de la API

## 🚀 Despliegue en Vercel

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

### Desarrollo Local

```bash
# Usar Makefile
make dev

# O directamente
uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
```

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `http://localhost:3000` |
| `RATE_LIMIT_RPM` | Requests por minuto | `60` |
| `HTTP_TIMEOUT_SECONDS` | Timeout para requests HTTP | `12` |
| `CACHE_TTL_SECONDS` | TTL del cache en memoria | `90` |
| `MAX_BODY_KB` | Tamaño máximo de body en KB | `128` |

### Limitaciones Serverless

- **Cache efímero**: Los datos se pierden entre invocaciones
- **Sin TradingView**: Requiere navegador, deshabilitado en Vercel
- **Timeouts**: Máximo 10 segundos por función
- **Memoria**: Límite de 1024MB por función

### Opción 2: API Separada + Bot

Si prefieres separar el scraping de la API:

```bash
# Terminal 1: API para recibir datos
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Bot de scraping (ejecutar cuando necesites datos)
python bot_scraper.py
```

## 📊 Estructura de Datos

Los datos se almacenan en la siguiente estructura:

```json
{
  "tradingview": {
    "indices": [...],
    "acciones": [...],
    "cripto": [...],
    "forex": [...]
  },
  "finviz": {
    "forex": [...],
    "acciones": [...],
    "indices": [...]
  },
  "yahoo": {
    "forex": [...],
    "acciones": [...],
    "materias_primas": [...],
    "indices": [...]
  },
  "last_updated": "2024-01-01T12:00:00",
  "metadata": {
    "version": "1.0",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `API_HOST` | Host de la API | localhost |
| `API_PORT` | Puerto de la API | 8000 |
| `SCRAPING_INTERVAL_MINUTES` | Intervalo de scraping | 50 |
| `REQUEST_TIMEOUT` | Timeout para requests | 15 |
| `BROWSER_TIMEOUT` | Timeout para navegador | 60000 |
| `DATA_FILE` | Archivo de datos | data.json |
| `BACKUP_FILE` | Archivo de backup | data_backup.json |
| `LOG_LEVEL` | Nivel de logging | INFO |
| `LOG_FILE` | Archivo de logs | financial_api.log |
| `ENABLE_SCREENSHOTS` | Habilitar screenshots | true |
| `CORS_ORIGINS` | Orígenes permitidos para CORS | http://localhost:3000,http://127.0.0.1:3000 |
| `CORS_ALLOW_CREDENTIALS` | Permitir credenciales en CORS | false |
| `CORS_ALLOW_METHODS` | Métodos HTTP permitidos | GET,POST,OPTIONS |
| `CORS_ALLOW_HEADERS` | Headers permitidos | Content-Type,Accept,User-Agent |
| `CORS_MAX_AGE` | Tiempo de cache CORS (segundos) | 3600 |

### Ejemplo de configuración

```bash
# .env
API_HOST=0.0.0.0
API_PORT=8000
SCRAPING_INTERVAL_MINUTES=30
LOG_LEVEL=DEBUG
ENABLE_SCREENSHOTS=false
```

## 📝 Logging

El sistema incluye logging detallado:

- **Archivo de logs**: `financial_api.log`
- **Niveles disponibles**: DEBUG, INFO, WARNING, ERROR
- **Información registrada**: 
  - Operaciones de scraping
  - Errores y excepciones
  - Requests a la API
  - Actualizaciones de datos

## 🔧 Troubleshooting

### Problemas comunes

1. **Error de Playwright**
```bash
playwright install chromium
```

2. **Error de permisos en Windows**
```bash
# Ejecutar como administrador o usar
playwright install --with-deps chromium
```

3. **Timeout en scraping**
- Aumentar `BROWSER_TIMEOUT` en configuración
- Verificar conexión a internet
- Revisar logs para detalles específicos

4. **Datos vacíos**
- Verificar que las URLs de scraping estén accesibles
- Revisar selectores CSS en los scrapers
- Habilitar screenshots para debugging

### Debugging

1. **Habilitar logs detallados**
```bash
LOG_LEVEL=DEBUG
```

2. **Habilitar screenshots**
```bash
ENABLE_SCREENSHOTS=true
```

3. **Verificar estado de la API**
```bash
curl http://localhost:8000/health
```

## 🏗️ Arquitectura

```
financial_api/
├── main.py              # API principal con scheduler
├── api.py               # API para recibir datos
├── bot_scraper.py       # Bot de scraping independiente
├── data_store.py        # Almacenamiento de datos
├── config.py            # Configuración centralizada
├── logger.py            # Sistema de logging
├── scraper/             # Módulos de scraping
│   ├── tradingview.py   # Scraper de TradingView
│   ├── finviz.py        # Scraper de Finviz
│   └── yahoo.py         # Scraper de Yahoo Finance
├── screenshots/         # Screenshots para debugging
├── data.json           # Datos almacenados
├── data_backup.json    # Backup de datos
└── financial_api.log   # Archivo de logs
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## ⚠️ Disclaimer

Este proyecto es solo para fines educativos. Asegúrate de cumplir con los términos de servicio de los sitios web que estás scrapeando. El uso de datos financieros debe cumplir con las regulaciones locales aplicables. 