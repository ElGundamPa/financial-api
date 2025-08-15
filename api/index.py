from api.core.app_core import create_app
from api.core.settings import AppSettings

# Crear la aplicación para Vercel
# Cuando se sirve como /api/index (subpath), establecemos root_path para que FastAPI construya /docs y rutas correctamente
settings = AppSettings(runtime="vercel")
app = create_app(settings=settings, root_path="/api/index")
