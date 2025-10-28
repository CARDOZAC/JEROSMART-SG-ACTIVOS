from flask import Blueprint

movimientos_bp = Blueprint(
    "movimientos", __name__, template_folder="templates"
)

from . import routes
