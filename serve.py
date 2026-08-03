"""
Punto de entrada de PRODUCCIÓN, servido con Waitress.

`run.py` levanta el servidor de desarrollo de Flask, que no está pensado para
uso real: atiende de forma limitada, se cae con facilidad y, con debug activo,
expone el depurador de Werkzeug, desde el cual se puede ejecutar código en el
servidor.

Uso:
    venv\\Scripts\\python.exe serve.py

Variables de entorno admitidas (opcionales, en .env):
    HOST     Interfaz de escucha        (por defecto 0.0.0.0)
    PORT     Puerto                     (por defecto 5000)
    THREADS  Hilos de atención          (por defecto 8)
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from waitress import serve

load_dotenv()

from app import create_app  # noqa: E402  (después de load_dotenv, a propósito)

app = create_app()

HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
THREADS = int(os.environ.get('THREADS', 8))


def configurar_logging():
    """
    Escribe el log en logs/jerosmart.log con rotación.

    En desarrollo los mensajes van a la consola y se pierden al cerrarla; en
    producción hacen falta para investigar un incidente después.
    """
    directorio = Path(__file__).resolve().parent / 'logs'
    directorio.mkdir(exist_ok=True)

    formato = logging.Formatter(
        '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
    )

    archivo = RotatingFileHandler(
        directorio / 'jerosmart.log',
        maxBytes=5 * 1024 * 1024,   # 5 MB por archivo
        backupCount=5,              # conserva 5 archivos anteriores
        encoding='utf-8'
    )
    archivo.setFormatter(formato)
    archivo.setLevel(logging.INFO)

    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    consola.setLevel(logging.INFO)

    for handler in (archivo, consola):
        app.logger.addHandler(handler)
        logging.getLogger('waitress').addHandler(handler)

    app.logger.setLevel(logging.INFO)
    logging.getLogger('waitress').setLevel(logging.INFO)


if __name__ == '__main__':
    configurar_logging()

    app.logger.info('=' * 62)
    app.logger.info('SG Activos Fijos - servidor de produccion (Waitress)')
    app.logger.info(f'Escuchando en http://{HOST}:{PORT}  ({THREADS} hilos)')
    app.logger.info(f'Organizacion: {app.config.get("ORG_NOMBRE")}')
    app.logger.info('Log: logs/jerosmart.log   |   Detener: Ctrl+C')
    app.logger.info('=' * 62)

    serve(
        app,
        host=HOST,
        port=PORT,
        threads=THREADS,
        # Identificador del servidor en las cabeceras de respuesta
        ident='SG Activos Fijos',
        # Corta conexiones ociosas para no agotar los hilos
        channel_timeout=120,
    )
