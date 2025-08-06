# 📊 Financial Data API - Endpoints Completos

## 🌐 URL Base
```
http://localhost:8000
```

## 📋 Endpoints Generales

### **Información de la API**
```
GET http://localhost:8000/
```
**Descripción**: Información general, versión y lista de todos los endpoints disponibles

### **Todos los Datos**
```
GET http://localhost:8000/datos
```
**Descripción**: Obtiene todos los datos financieros de todas las fuentes

### **Resumen de Datos**
```
GET http://localhost:8000/datos/resume
```
**Descripción**: Resumen estadístico de los datos disponibles

### **Estado de la API**
```
GET http://localhost:8000/health
```
**Descripción**: Health check de la API

### **Scraping Manual**
```
POST http://localhost:8000/scrape
```
**Descripción**: Ejecuta el scraping manualmente

---

## 📈 Endpoints por Tipo de Dato

### **1. Índices Bursátiles** 📊
```
GET http://localhost:8000/datos/indices
```
**Datos**: S&P 500, NASDAQ, Dow Jones, DAX, CAC 40, etc.
**Fuentes**: TradingView, Finviz, Yahoo Finance

### **2. Acciones** 💼
```
GET http://localhost:8000/datos/acciones
```
**Datos**: Acciones individuales de empresas
**Fuentes**: TradingView, Finviz, Yahoo Finance (gainers, losers, most-active)

### **3. Criptomonedas** 🪙
```
GET http://localhost:8000/datos/cripto
```
**Datos**: Bitcoin, Ethereum, y otras criptos
**Fuente**: TradingView

### **4. Forex** 💱
```
GET http://localhost:8000/datos/forex
```
**Datos**: Pares de divisas (EUR/USD, GBP/USD, etc.)
**Fuentes**: TradingView, Finviz, Yahoo Finance

### **5. ETFs** 📊
```
GET http://localhost:8000/datos/etfs
```
**Datos**: Fondos cotizados
**Fuente**: Yahoo Finance

### **6. Materias Primas** 🛢️
```
GET http://localhost:8000/datos/materias-primas
```
**Datos**: Oro, plata, petróleo, etc.
**Fuente**: Yahoo Finance

---

## 🌐 Endpoints por Fuente

### **TradingView** 📈
```
GET http://localhost:8000/datos/tradingview
```
**Incluye**: Índices, Acciones, Cripto, Forex

### **Finviz** 📊
```
GET http://localhost:8000/datos/finviz
```
**Incluye**: Forex, Acciones, Índices

### **Yahoo Finance** 📈
```
GET http://localhost:8000/datos/yahoo
```
**Incluye**: Forex, Gainers, Losers, Most Active Stocks/ETFs, Undervalued Growth, Materias Primas, Índices

---

## 📊 Endpoints Específicos de Yahoo Finance

### **Acciones con Mayor Ganancia** 📈
```
GET http://localhost:8000/datos/yahoo/gainers
```
**Datos**: Top 149 páginas de acciones con mayor ganancia del día

### **Acciones con Mayor Pérdida** 📉
```
GET http://localhost:8000/datos/yahoo/losers
```
**Datos**: Top 148 páginas de acciones con mayor pérdida del día

### **Más Activos** 🔥
```
GET http://localhost:8000/datos/yahoo/most-active
```
**Datos**: Acciones y ETFs más activos (50 páginas cada uno)

### **Crecimiento Infravalorado** 💎
```
GET http://localhost:8000/datos/yahoo/undervalued
```
**Datos**: Acciones de crecimiento infravaloradas (20 páginas)

---

## 🧪 Ejemplos de Uso

### **Usando curl**
```bash
# Obtener solo índices
curl http://localhost:8000/datos/indices

# Obtener solo datos de TradingView
curl http://localhost:8000/datos/tradingview

# Obtener gainers de Yahoo
curl http://localhost:8000/datos/yahoo/gainers

# Ejecutar scraping manual
curl -X POST http://localhost:8000/scrape
```

### **Usando JavaScript/Fetch**
```javascript
// Obtener índices
fetch('http://localhost:8000/datos/indices')
  .then(response => response.json())
  .then(data => console.log(data));

// Obtener forex
fetch('http://localhost:8000/datos/forex')
  .then(response => response.json())
  .then(data => console.log(data));
```

### **Usando Python/Requests**
```python
import requests

# Obtener cripto
response = requests.get('http://localhost:8000/datos/cripto')
cripto_data = response.json()

# Obtener materias primas
response = requests.get('http://localhost:8000/datos/materias-primas')
commodities_data = response.json()
```

---

## 📊 Estructura de Respuesta

### **Ejemplo: /datos/indices**
```json
{
  "tradingview": [
    {
      "nombre": "S&P 500",
      "precio": "6,299.20 USD",
      "cambio": "-0,49%",
      "maximo": "6,346.00 USD",
      "minimo": "6,289.37 USD",
      "calificacion": "Compra"
    }
  ],
  "finviz": [...],
  "yahoo": [...],
  "last_updated": "2024-01-01T12:00:00"
}
```

### **Ejemplo: /datos/yahoo/gainers**
```json
{
  "gainers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "price": "150.00",
      "change": "+5.00",
      "change_percent": "+3.45%",
      "volume": "50.2M"
    }
  ],
  "last_updated": "2024-01-01T12:00:00"
}
```

---

## 🔧 Configuración

### **Cambiar Puerto**
```bash
# Variable de entorno
export API_PORT=8080

# Al iniciar
python start.py --port 8080

# Directo con uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080
```

### **Acceso desde Red Local**
```
http://[TU_IP_LOCAL]:8000/datos/indices
http://[TU_IP_LOCAL]:8000/datos/acciones
http://[TU_IP_LOCAL]:8000/datos/forex
```

---

## 🎯 Casos de Uso

### **Para Dashboard de Trading**
- `/datos/indices` - Resumen del mercado
- `/datos/forex` - Pares de divisas
- `/datos/cripto` - Criptomonedas

### **Para Análisis de Acciones**
- `/datos/acciones` - Todas las acciones
- `/datos/yahoo/gainers` - Mejores performers
- `/datos/yahoo/losers` - Peores performers

### **Para Monitoreo de Mercado**
- `/datos/yahoo/most-active` - Actividad del mercado
- `/datos/etfs` - Fondos cotizados
- `/datos/materias-primas` - Commodities

### **Para Desarrollo**
- `/health` - Verificar estado
- `/datos/resume` - Estadísticas generales
- `/scrape` - Actualizar datos manualmente

---

## 📝 Notas Importantes

1. **CORS**: Configurado para permitir requests desde dominios autorizados
2. **Rate Limiting**: Se recomienda no hacer más de 10 requests por minuto
3. **Datos**: Se actualizan automáticamente cada 50 minutos
4. **Logs**: Todas las requests se registran en `financial_api.log`
5. **Backup**: Los datos se respaldan automáticamente en `data_backup.json`

---

## 🚀 Versión
**API Version**: 1.1.0 - Production Ready! 🎉
