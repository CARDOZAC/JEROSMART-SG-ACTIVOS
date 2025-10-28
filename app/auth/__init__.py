from flask import Blueprint

# Crear el Blueprint del módulo de autenticación
auth_bp = Blueprint(
    "auth", __name__, template_folder="templates"
)

# Importar las rutas después de crear el blueprint (evita dependencias circulares)
from . import routes
