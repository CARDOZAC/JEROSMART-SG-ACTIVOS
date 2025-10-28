from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instancia de la base de datos (ORM)
db = SQLAlchemy()

# Configuramos el gestor de sesiones de usuario
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirige a la página de login si no se está autenticado
login_manager.login_message_category = 'info'
login_manager.login_message = 'Por favor, inicie sesión para acceder a esta página.'
