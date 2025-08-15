try:
    # Import absoluto (preferido en Vercel)
    from core.app_core import create_app
except Exception:  # fallback por si el path difiere en runtime
    # Ajuste de sys.path para ciertos entornos
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.app_core import create_app

# Crear la aplicación para Vercel
app = create_app(runtime="vercel")
