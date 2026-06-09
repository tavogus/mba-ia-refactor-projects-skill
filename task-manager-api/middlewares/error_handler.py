import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register centralized error handlers on the Flask app."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        logger.warning("HTTP %s: %s", e.code, e.description)
        return jsonify({"error": e.description, "sucesso": False}), e.code

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.exception("Unhandled exception: %s", str(e))
        return jsonify({"error": "Erro interno do servidor", "sucesso": False}), 500
