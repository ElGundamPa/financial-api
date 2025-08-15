from core.app_core import create_app

# Nota: Vercel @vercel/python selecciona internamente la versión de Python. No forzamos pip/py aquí.

# Crear la aplicación para Vercel
# Cuando se sirve como /api/index (subpath), establecemos root_path para que FastAPI construya /docs y rutas correctamente
app = create_app(runtime="vercel", root_path="/api/index")
