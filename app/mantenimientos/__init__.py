from flask import Blueprint

mantenimientos_bp = Blueprint(
    'mantenimientos',
    __name__,
    template_folder='templates'
)

from . import routes
