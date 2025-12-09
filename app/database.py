import sqlite3
from flask import current_app, g


class Database:
    """
    Clase para gestionar la conexión a la base de datos SQLite
    dentro del contexto de la aplicación Flask.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Registra las funciones de teardown con la aplicación."""
        app.teardown_appcontext(self.close_db)

    def get_db(self):
        """
        Abre una nueva conexión a la base de datos si no existe una para el
        contexto actual de la aplicación.
        """
        if "db" not in g:
            g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
            g.db.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
        return g.db

    def close_db(self, e=None):
        """Cierra la conexión a la base de datos."""
        db = g.pop("db", None)
        if db is not None:
            db.close()
