"""Composition root — cria a app, carrega config, injeta dependências e registra tudo."""
from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.database import init_db
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.views.routes import api_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["DB_PATH"] = settings.DB_PATH

    # Injeção de dependência: o service é montado aqui, não dentro do controller.
    app.config["NOTIFICATIONS"] = NotificationService()

    CORS(app)
    init_db(app)
    app.register_blueprint(api_bp)
    register_error_handlers(app)
    return app


app = create_app()
