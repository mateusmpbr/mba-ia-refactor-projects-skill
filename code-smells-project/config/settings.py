import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DATABASE_URL = os.environ.get("DATABASE_URL", "loja.db")