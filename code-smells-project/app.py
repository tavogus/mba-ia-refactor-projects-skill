"""Entry point. Mantém `python app.py` funcionando; a app real vive em src/ (MVC)."""
import logging

from src.app import app
from src.config.settings import settings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{settings.PORT}")
    print("=" * 50)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
