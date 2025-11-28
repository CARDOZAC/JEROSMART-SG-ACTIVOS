import os
from flask import Flask
import datetime as dt
import json
from .extensions import db, login_manager, migrate
import click
from flask.cli import with_appcontext
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
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirige a esta vista si no está logueado
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # --- Registrar Comandos CLI (FASE 1.1) ---
    from .cli import init_cli
    init_cli(app)

    # --- Registrar Filtros de Plantilla (Jinja2) ---
    @app.template_filter('formatdatetime')
    def format_datetime(value, fmt='%d/%m/%Y %H:%M'):
        """Formatea una fecha y hora para mostrar en las plantillas."""
        if not value:
            return "N/A"
        if isinstance(value, str):
            try:
                # Intenta parsear varios formatos comunes
                for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                    try:
                        value = dt.datetime.strptime(value.split('.')[0], pattern)
                        break
                    except ValueError:
                        continue
                if not isinstance(value, dt.datetime):
                    return value
            except Exception:
                return value
        if isinstance(value, dt.datetime):
            return value.strftime(fmt)
        return value

    @app.template_filter('formatdate')
    def format_date(value, fmt='%d/%m/%Y'):
        """Formatea solo la fecha (sin hora) para mostrar en las plantillas."""
        if not value:
            return "N/A"
        if isinstance(value, str):
            try:
                # Intenta parsear varios formatos comunes
                for pattern in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
                    try:
                        value = dt.datetime.strptime(value.split(' ')[0], pattern.split(' ')[0])
                        break
                    except ValueError:
                        continue
                if not isinstance(value, (dt.datetime, dt.date)):
                    return value
            except Exception:
                return value
        if isinstance(value, dt.datetime):
            return value.strftime(fmt)
        if isinstance(value, dt.date):
            return value.strftime(fmt)
        return value

    @app.template_filter('format_currency')
    def format_currency(value):
        """Formatea un número como moneda colombiana (COP)."""
        if value is None:
            return "$ 0"
        try:
            # Formato con separador de miles y sin decimales si es entero
            if float(value).is_integer():
                return f"$ {int(value):,}".replace(",", ".")
            else:
                return f"$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return value

    @app.template_filter('from_json')
    def from_json_filter(value):
        """
        Parsea una cadena JSON y retorna el objeto Python correspondiente.
        Retorna una lista vacía si hay error o si el valor es None.

        Estilo James Gosling: Manejo robusto de errores y tipos de datos.
        """
        if not value:
            return []
        try:
            result = json.loads(value)
            # Retornar el tipo correcto según el JSON parseado
            return result if result is not None else []
        except (json.JSONDecodeError, TypeError) as e:
            # Log del error para debugging
            app.logger.warning(f"[from_json Filter] Error parseando JSON: {e}. Valor: {value}")
            return []

    @app.template_filter('default_empty')
    def default_empty(value, default=''):
        """
        Convierte valores None, 'null', 'None', o strings vacíos a un valor por defecto.
        Útil para evitar mostrar "null" o "None" en PDFs.

        FASE 2.2: Mejora para templates PDF de Entrada/Salida
        """
        if value is None:
            return default
        if isinstance(value, str):
            # Limpia strings que contengan "null", "None", o estén vacíos
            value_stripped = value.strip()
            if value_stripped.lower() in ('null', 'none', ''):
                return default
        return value

    # --- Registrar Blueprints (módulos de rutas) ---
    # Los imports se hacen aquí para evitar importaciones circulares
    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .activos.routes import activos_bp
    from .activos_v2 import activos_v2_bp  # Nuevo módulo optimizado
    from .movimientos.routes import movimientos_bp
    from .funcionarios.routes import funcionarios_bp
    from .reportes.routes import reportes_bp
    from .proveedores.routes import proveedores_bp
    from .biomedicos.routes import biomedicos_bp
    from .mantenimientos.routes import mantenimientos_bp

    app.register_blueprint(main_bp)  # Se registra en la raíz '/'
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(activos_bp, url_prefix='/activos')
    app.register_blueprint(activos_v2_bp)  # Registrado con prefijo en __init__.py
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(movimientos_bp, url_prefix='/movimientos')
    app.register_blueprint(funcionarios_bp, url_prefix='/funcionarios')
    app.register_blueprint(proveedores_bp, url_prefix='/proveedores')
    app.register_blueprint(biomedicos_bp, url_prefix='/biomedicos')
    app.register_blueprint(mantenimientos_bp, url_prefix='/mantenimientos')

    # --- Registrar Comandos CLI ---
    # Esto es mejor manejarlo en run.py para mantener __init__.py limpio

    # --- Crear carpetas de subida ---
    # Llama a la función de inicialización de la configuración
    config_class.init_app(app)

    # --- Registrar Comandos CLI ---
    # Se registra el comando aquí para que Flask lo descubra.
    app.cli.add_command(init_db_command)

    return app

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Limpia los datos existentes y crea nuevas tablas."""
    # Aquí usamos db.drop_all() y db.create_all() para un reinicio completo.
    # En un entorno de producción, usarías migraciones (Flask-Migrate).
    db.drop_all()
    db.create_all()
    click.echo('Base de datos inicializada.')
