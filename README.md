# Financial Data API

Una API robusta para obtener datos financieros de múltiples fuentes (TradingView, Finviz, Yahoo Finance) con scraping automatizado y persistencia de datos.

## 🚀 Características

- **Múltiples fuentes de datos**: TradingView, Finviz, Yahoo Finance
- **Scraping automatizado**: Programado cada 50 minutos (configurable)
- **Persistencia de datos**: Almacenamiento en JSON con backup automático
- **Logging completo**: Sistema de logs detallado para debugging
- **API RESTful**: Endpoints para obtener datos y controlar scraping
- **Manejo robusto de errores**: Recuperación automática y validación de datos
- **Configuración flexible**: Variables de entorno para personalización

## 📋 Requisitos

- Python 3.8+
- Playwright (navegador automatizado)
- Conexión a internet

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

4. **Instalar navegadores para Playwright**
```bash
playwright install chromium
```

5. **Configurar variables de entorno (opcional)**
```bash
# Copiar archivo de ejemplo
cp .env.example .env
# Editar según necesidades
```

## 🚀 Uso

### Opción 1: API Principal (Recomendado)

La API principal incluye scraping automático y scheduler:

```bash
# Iniciar la API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints disponibles:**
- `GET /` - Información de la API
- `GET /datos` - Obtener todos los datos financieros
- `GET /datos/summary` - Obtener resumen de datos
- `POST /scrape` - Ejecutar scraping manualmente
- `GET /health` - Verificar estado de la API

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