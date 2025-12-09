from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Instancia de la base de datos (ORM)
db = SQLAlchemy()
migrate = Migrate()

# Configuramos el gestor de sesiones de usuario
login_manager = LoginManager()
login_manager.login_view = (
    "auth.login"  # Redirige a la página de login si no se está autenticado
)
login_manager.login_message_category = "info"
login_manager.login_message = "Por favor, inicie sesión para acceder a esta página."


@login_manager.user_loader
def load_user(user_id):
    """
    Callback requerido por Flask-Login para cargar un usuario desde la sesión.
    Se importa aquí para evitar importaciones circulares.
    """
    from .models import User

    return db.session.get(User, int(user_id))
