# Financial Data API v2.1.0 — Serverless (Vercel) y Python 3.10 Ready

API para obtener datos financieros (Finviz, Yahoo Finance) con scraping HTTP-only, cache efímero en memoria, autenticación configurable y despliegue como Serverless Functions en Vercel.

## 🚀 Características

- **HTTP-only scrapers**: Finviz, Yahoo (sin navegador en producción)
- **Asíncrono**: scraping en paralelo
- **Cache efímero**: `cachetools.TTLCache` (por instancia/región)
- **Sin base de datos**: todo viaja en request/response
- **Rate limiting**: configurable por entorno
- **CORS**: orígenes configurables
- **Compresión y timeouts**: para serverless
- **Autenticación**: `AUTH_MODE=apikey|basic|jwt (RS256)`
- **2 funciones serverless**: `api/index.py` y `api/receiver.py`

## 📋 Requisitos

- Local: Python 3.10 (recomendado para desarrollo)
- Vercel: Runtime Python 3.12 (el código es compatible 3.10–3.12)

## 📂 Estructura

```
financial_api/
├── api/
│   ├── index.py         # Serverless principal (FastAPI)
│   └── receiver.py      # Serverless receptor de datos
├── core/
│   ├── app_core.py      # App factory, middlewares, auth, rate-limit, endpoints
│   ├── config.py
│   ├── logger.py
│   ├── data_store.py
│   └── __init__.py
├── scrapers/            # Scrapers HTTP-only (Finviz/Yahoo)
├── data/                # Datos locales opcionales
├── vercel.json          # Config de Vercel (functions + routes)
└── requirements.txt
```

## 🔐 Autenticación

- `AUTH_MODE` soporta: `none | apikey | basic | jwt`
- API Key: header `x-api-key: <clave>` o `Authorization: ApiKey <clave>`
- Basic: header `Authorization: Basic <base64(user:pass)>`
- JWT (RS256): header `Authorization: Bearer <token>` con verificación de firma usando `JWT_PUBLIC_KEY` (PEM). Opcional: `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_REQUIRED_SCOPE`.

## ⚙️ Variables de entorno (principales)

```
# Seguridad
AUTH_MODE=apikey                  # o jwt|basic|none
API_KEYS=mi-super-clave           # si apikey (múltiples separadas por coma)
BASIC_USER=                       # si basic
BASIC_PASSWORD=                   # si basic
JWT_PUBLIC_KEY="""-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"""   # si jwt
JWT_ISSUER=
JWT_AUDIENCE=
JWT_REQUIRED_SCOPE=

# Red y performance
CORS_ORIGINS=https://tu-frontend.com
RATE_LIMIT_RPM=60
HTTP_TIMEOUT_SECONDS=12
CACHE_TTL_SECONDS=90
MAX_BODY_KB=128
AUTH_EXCLUDE_PATHS=/health,/docs,/openapi.json   # deja vacío para proteger todo
```

## 🧪 Desarrollo local (Python 3.10)

1) Crear venv 3.10 y activar
```
python3.10 -m venv venv
source venv/bin/activate            # Linux/Mac
# Windows PowerShell
# py -3.10 -m venv venv; .\venv\Scripts\Activate.ps1
```

2) Instalar dependencias
```
pip install -r requirements.txt
```

3) Exportar variables (ejemplo con API Key)
```
export AUTH_MODE=apikey
export API_KEYS=mi-super-clave
export CORS_ORIGINS=http://localhost:3000
```
En PowerShell:
```
$env:AUTH_MODE="apikey"; $env:API_KEYS="mi-super-clave"; $env:CORS_ORIGINS="http://localhost:3000"
```

4) Iniciar FastAPI (uvicorn)
```
uvicorn api.index:app --host 0.0.0.0 --port 8000
```

5) Probar endpoints
```
curl -i http://localhost:8000/health                                 # 401 sin auth
curl -H "x-api-key: mi-super-clave" http://localhost:8000/health      # 200 OK
curl -H "x-api-key: mi-super-clave" http://localhost:8000/datos
curl -H "x-api-key: mi-super-clave" http://localhost:8000/datos/resume
```

Receiver (segunda función):
```
curl -H "x-api-key: mi-super-clave" http://localhost:8000/api/receiver/health
```

## 🚀 Despliegue en Vercel (paso a paso)

1) Preparación
- Confirma que `vercel.json` contiene:
  - functions: `api/index.py` y `api/receiver.py` con `runtime: python3.12`
  - routes: `/api/receiver(.*)` → `/api/receiver.py` y `/(.*)` → `/api/index.py`
  - regions: `["gru1"]` (opcional)

2) Conectar el repo
- Entra a vercel.com → Importar proyecto desde GitHub
- Selecciona la rama (`main` o `deploy/vercel`)
- Framework: “Other”

3) Variables de entorno (Production)
- Al menos:
  - `AUTH_MODE=apikey` (o `jwt` si usas tokens)
  - `API_KEYS=mi-super-clave` (si apikey)
  - `CORS_ORIGINS=https://tu-frontend.com`
- Si `AUTH_MODE=jwt`:
  - `JWT_PUBLIC_KEY` (PEM completo)
  - Opcional: `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_REQUIRED_SCOPE`

4) Deploy
- Click “Deploy” (o con CLI: `vercel --prod`)

5) Probar en producción
```
curl -H "x-api-key: mi-super-clave" https://<project>.vercel.app/health
curl -H "x-api-key: mi-super-clave" https://<project>.vercel.app/datos
curl -H "x-api-key: mi-super-clave" https://<project>.vercel.app/api/receiver/health
```

## 🔎 Endpoints

- `GET /` — info API, estado de fuentes
- `GET /health` — estado
- `GET /sources` — fuentes disponibles y estado
- `GET /datos` — datos agregados de fuentes habilitadas
- `GET /datos/resume` — resumen por categorías
- `POST /scrape` — disparar scraping manual (sin persistencia)
- `GET /api/receiver/health` — health del receiver
- `POST /api/receiver/receive` — recibir datos externos (bots/webhooks)

## ⚠️ Limitaciones Serverless

- Cache por instancia/región (no compartido, no persistente)
- Sin TradingView en producción (requiere navegador): responde 503 con `browser_required_disabled_in_prod`
- Respuestas con `Cache-Control: public, max-age=60` y `Vary: Accept-Encoding`

## 🧰 Troubleshooting

- 401 en producción → revisa `AUTH_MODE` y headers (`x-api-key` o `Authorization`)
- CORS bloqueado → actualiza `CORS_ORIGINS`
- Timeouts scraping → sube `HTTP_TIMEOUT_SECONDS` (ojo con límites de Vercel)

---

Lista para producción con Python 3.10 (local) y Vercel (Python 3.12 en runtime). Si necesitas que lo deje desplegado automáticamente con Vercel CLI, indícame el proyecto/organización y realizo el despliegue.