# ==============================================================================
# MÓDULO ACTIVOS V2 - Blueprint Principal
# ==============================================================================
# Versión moderna con Alpine.js + HTMX para gestión eficiente de 6000+ activos
# ==============================================================================

from flask import Blueprint

activos_v2_bp = Blueprint(
    'activos_v2',
    __name__,
    url_prefix='/activos-v2',
    template_folder='../templates/activos_v2',
    static_folder='../static'
)

from app.activos_v2 import routes
