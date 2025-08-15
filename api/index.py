from core.env import load_env
from core.app_core import create_app

load_env()
app = create_app(runtime="vercel")
