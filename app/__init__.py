import os
from flask import Flask
from .extensions import db, login_manager
from .config import Config

def create_app(config_class=Config):
    """Factory para crear la aplicación Flask."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuración ---
    # Carga la configuración desde el objeto importado de config.py
    app.config.from_object(config_class)

    # Asegúrate de que la carpeta de instancia exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Inicializar Extensiones ---
    db.init_app(app)
    login_manager.init_app(app)

    # --- Registrar Blueprints (módulos de rutas) ---
    # Los imports se hacen aquí para evitar importaciones circulares
    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .activos.routes import activos_bp
    from .movimientos.routes import movimientos_bp
    # from .admin.routes import admin_bp  # Descomenta si tienes un blueprint admin
    from .biomedicos.routes import biomedicos_bp

    app.register_blueprint(main_bp) # Se registra en la raíz '/'
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(activos_bp, url_prefix='/activos')
    app.register_blueprint(movimientos_bp, url_prefix='/movimientos')
    # app.register_blueprint(admin_bp)
    app.register_blueprint(biomedicos_bp, url_prefix='/biomedicos')

    # --- Registrar Comandos CLI ---
    # Esto es mejor manejarlo en run.py para mantener __init__.py limpio

    # --- Crear carpetas de subida ---
    # Llama a la función de inicialización de la configuración
    config_class.init_app(app)

    return app
