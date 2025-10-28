from flask import Blueprint

funcionarios_bp = Blueprint(
    "funcionarios", __name__, template_folder="templates"
)

from . import routes
