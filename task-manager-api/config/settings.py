"""
Centralized configuration — all secrets come from environment variables.
Copy .env.example to .env and fill in real values before running in production.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMTP — leave empty to disable email sending in development
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    # App behaviour
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
