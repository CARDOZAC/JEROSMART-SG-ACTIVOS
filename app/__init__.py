import os
from flask import Flask
from .extensions import db, login_manager
from .config import Config

def create_app(config_class=Config):
    """Factory para crear la aplicación Flask."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuración ---
    app.config.from_object(config_class)

    # Asegúrate de que la carpeta de instancia exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Inicializar Extensiones ---
    db.init_app(app)
    login_manager.init_app(app)

    # --- Registrar Blueprints ---
    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .activos.routes import activos_bp
    from .movimientos.routes import movimientos_bp
    from .biomedicos.routes import biomedicos_bp
    from .funcionarios.routes import funcionarios_bp
    from .proveedores.routes import proveedores_bp
    from .reportes import reportes_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(activos_bp, url_prefix='/activos')
    app.register_blueprint(movimientos_bp, url_prefix='/movimientos')
    app.register_blueprint(biomedicos_bp, url_prefix='/biomedicos')
    app.register_blueprint(funcionarios_bp, url_prefix='/funcionarios')
    app.register_blueprint(proveedores_bp, url_prefix='/proveedores')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')

    # --- Custom Jinja Filters ---
    from .utils import format_datetime, from_json
    app.jinja_env.filters['formatdatetime'] = format_datetime
    app.jinja_env.filters['from_json'] = from_json

    # --- Crear carpetas de subida ---
    config_class.init_app(app)

    return app
