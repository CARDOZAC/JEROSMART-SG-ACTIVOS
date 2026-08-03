from flask import Blueprint

movimientos_bp = Blueprint(
    "movimientos", __name__, template_folder="templates"
)

from . import routes
from . import routes_excel  # Rutas de exportación a Excel
