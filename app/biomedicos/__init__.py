from flask import Blueprint

biomedicos_bp = Blueprint(
    "biomedicos",
    __name__,
    template_folder="templates",
    static_folder="static"
)

from . import routes
