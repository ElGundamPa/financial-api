from core.app_core import create_app

# Nota: Vercel @vercel/python maneja el root_path automáticamente.
# No establecemos root_path manualmente para evitar desajustes y 404.
app = create_app(runtime="vercel")
