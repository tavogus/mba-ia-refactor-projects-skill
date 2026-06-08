"""Tratamento de erros centralizado (cura AP-14) — remove o try/except repetido."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger("app")


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http(e):
        return jsonify({"erro": e.description, "sucesso": False}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Erro não tratado: %s", e)
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
