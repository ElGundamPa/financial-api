from core.app_core import create_app

# Nota: Vercel @vercel/python selecciona internamente la versión de Python. No forzamos pip/py aquí.

# Crear la aplicación para Vercel
app = create_app(runtime="vercel")
