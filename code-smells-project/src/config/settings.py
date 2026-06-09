"""Configuração centralizada — segredos via variáveis de ambiente (cura AP-02/AP-11)."""
import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    # Limite default de paginação para listagens.
    PAGE_SIZE = int(os.environ.get("PAGE_SIZE", "50"))


settings = Settings()
