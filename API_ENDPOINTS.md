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

## 🎯 Endpoints Específicos por Fuente y Tipo

### **TradingView Específico** 📈

#### **Índices de TradingView**
```
GET http://localhost:8000/datos/tradingview/indices
```
**Datos**: Solo índices de TradingView (S&P 500, NASDAQ, etc.)

#### **Acciones de TradingView**
```
GET http://localhost:8000/datos/tradingview/acciones
```
**Datos**: Solo acciones de TradingView

#### **Criptomonedas de TradingView**
```
GET http://localhost:8000/datos/tradingview/cripto
```
**Datos**: Solo criptomonedas de TradingView (Bitcoin, Ethereum, etc.)

#### **Forex de TradingView**
```
GET http://localhost:8000/datos/tradingview/forex
```
**Datos**: Solo forex de TradingView (pares de divisas)

### **Finviz Específico** 📊

#### **Índices de Finviz**
```
GET http://localhost:8000/datos/finviz/indices
```
**Datos**: Solo índices de Finviz

#### **Acciones de Finviz**
```
GET http://localhost:8000/datos/finviz/acciones
```
**Datos**: Solo acciones de Finviz

#### **Forex de Finviz**
```
GET http://localhost:8000/datos/finviz/forex
```
**Datos**: Solo forex de Finviz

### **Yahoo Finance Específico** 📈

#### **Índices de Yahoo**
```
GET http://localhost:8000/datos/yahoo/indices
```
**Datos**: Solo índices de Yahoo Finance

#### **Acciones de Yahoo**
```
GET http://localhost:8000/datos/yahoo/acciones
```
**Datos**: Acciones de Yahoo (gainers, losers, most-active, undervalued)

#### **Forex de Yahoo**
```
GET http://localhost:8000/datos/yahoo/forex
```
**Datos**: Solo forex de Yahoo Finance

#### **ETFs de Yahoo**
```
GET http://localhost:8000/datos/yahoo/etfs
```
**Datos**: Solo ETFs de Yahoo Finance

#### **Materias Primas de Yahoo**
```
GET http://localhost:8000/datos/yahoo/materias-primas
```
**Datos**: Solo materias primas de Yahoo Finance

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
# Obtener solo índices de TradingView
curl http://localhost:8000/datos/tradingview/indices

# Obtener solo forex de Finviz
curl http://localhost:8000/datos/finviz/forex

# Obtener solo gainers de Yahoo
curl http://localhost:8000/datos/yahoo/gainers

# Obtener solo cripto de TradingView
curl http://localhost:8000/datos/tradingview/cripto

# Ejecutar scraping manual
curl -X POST http://localhost:8000/scrape
```

### **Usando JavaScript/Fetch**
```javascript
// Obtener solo índices de TradingView
fetch('http://localhost:8000/datos/tradingview/indices')
  .then(response => response.json())
  .then(data => console.log(data));

// Obtener solo forex de Finviz
fetch('http://localhost:8000/datos/finviz/forex')
  .then(response => response.json())
  .then(data => console.log(data));

// Obtener solo ETFs de Yahoo
fetch('http://localhost:8000/datos/yahoo/etfs')
  .then(response => response.json())
  .then(data => console.log(data));
```

### **Usando Python/Requests**
```python
import requests

# Obtener solo cripto de TradingView
response = requests.get('http://localhost:8000/datos/tradingview/cripto')
cripto_data = response.json()

# Obtener solo materias primas de Yahoo
response = requests.get('http://localhost:8000/datos/yahoo/materias-primas')
commodities_data = response.json()

# Obtener solo acciones de Finviz
response = requests.get('http://localhost:8000/datos/finviz/acciones')
stocks_data = response.json()
```

---

## 📊 Estructura de Respuesta

### **Ejemplo: /datos/tradingview/indices**
```json
{
  "indices": [
    {
      "nombre": "S&P 500",
      "precio": "6,299.20 USD",
      "cambio": "-0,49%",
      "maximo": "6,346.00 USD",
      "minimo": "6,289.37 USD",
      "calificacion": "Compra"
    }
  ],
  "last_updated": "2024-01-01T12:00:00"
}
```

### **Ejemplo: /datos/finviz/forex**
```json
{
  "forex": [
    {
      "par": "EUR/USD",
      "precio": "1.0850",
      "cambio": "+0.0020"
    }
  ],
  "last_updated": "2024-01-01T12:00:00"
}
```

### **Ejemplo: /datos/yahoo/acciones**
```json
{
  "gainers": [...],
  "losers": [...],
  "most_active_stocks": [...],
  "undervalued_growth": [...],
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
http://[TU_IP_LOCAL]:8000/datos/tradingview/indices
http://[TU_IP_LOCAL]:8000/datos/finviz/forex
http://[TU_IP_LOCAL]:8000/datos/yahoo/acciones
```

---

## 🎯 Casos de Uso

### **Para Dashboard de Trading**
- `/datos/tradingview/indices` - Resumen del mercado desde TradingView
- `/datos/finviz/forex` - Pares de divisas desde Finviz
- `/datos/tradingview/cripto` - Criptomonedas desde TradingView

### **Para Análisis de Acciones**
- `/datos/yahoo/acciones` - Todas las acciones de Yahoo
- `/datos/yahoo/gainers` - Mejores performers
- `/datos/yahoo/losers` - Peores performers
- `/datos/finviz/acciones` - Acciones desde Finviz

### **Para Monitoreo de Mercado**
- `/datos/yahoo/most-active` - Actividad del mercado
- `/datos/yahoo/etfs` - Fondos cotizados
- `/datos/yahoo/materias-primas` - Commodities

### **Para Desarrollo**
- `/health` - Verificar estado
- `/datos/resume` - Estadísticas generales
- `/scrape` - Actualizar datos manualmente

---

## 🚀 Mejoras Implementadas

### **✅ Optimizaciones Realizadas**
1. **🔧 Compresión Gzip**: Respuestas comprimidas para mejor rendimiento
2. **📊 Scrapers Mejorados**: 
   - TradingView: Selectors optimizados para forex
   - Finviz: Mejor extracción de datos y validación
   - Yahoo: Mantiene funcionalidad completa
3. **🎯 Endpoints Específicos**: Acceso directo por fuente y tipo
4. **⚡ Mejor Rendimiento**: Respuestas más rápidas y eficientes

### **📈 Beneficios**
- **Menor tráfico**: Compresión reduce el tamaño de las respuestas
- **Acceso específico**: Obtén solo los datos que necesitas
- **Mejor organización**: URLs intuitivas y fáciles de recordar
- **Datos más completos**: Scrapers optimizados extraen más información

---

## 📝 Notas Importantes

1. **CORS**: Configurado para permitir requests desde dominios autorizados
2. **Rate Limiting**: Se recomienda no hacer más de 10 requests por minuto
3. **Datos**: Se actualizan automáticamente cada 50 minutos
4. **Logs**: Todas las requests se registran en `financial_api.log`
5. **Backup**: Los datos se respaldan automáticamente en `data_backup.json`
6. **Compresión**: Las respuestas grandes se comprimen automáticamente

---

## 🚀 Versión
**API Version**: 1.2.0 - Optimizada y Organizada! 🎉
