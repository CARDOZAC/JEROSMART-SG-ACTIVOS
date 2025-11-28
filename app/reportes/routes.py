"""
Módulo para la generación de reportes contables y de gestión.
"""
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, current_app, make_response
)
import weasyprint
from sqlalchemy import select
from ..extensions import db
from ..models import Activo
from ..decorators import login_required, role_required

reportes_bp = Blueprint(
    'reportes',
    __name__,
    template_folder='templates',
    url_prefix='/reportes'
)

@reportes_bp.route('/')
@login_required
@role_required('Admin')
def index():
    """Página principal del módulo de reportes."""
    return render_template('index.html', active_page='reportes')

@reportes_bp.route('/depreciacion', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def reporte_depreciacion():
    """
    Genera y muestra un reporte de depreciación para todos los activos propios.
    Permite la exportación a PDF.
    """
    # 1. Obtener los activos relevantes para el reporte
    stmt = (
        select(Activo)
        .where(
            Activo.tipo_propiedad == 'Propio',
            Activo.valor_comercial.isnot(None),
            Activo.valor_comercial > 0
        )
        .order_by(Activo.nombre_activo)
    )
    activos = db.session.execute(stmt).scalars().all()

    # --- Lógica de negocio robusta (Estilo Gosling) ---
    # Si no hay activos que cumplan con los criterios, no se puede generar el reporte.
    # En lugar de fallar o mostrar una página vacía, informamos al usuario.
    if not activos:
        return render_template(
            'reportes/reporte_depreciacion.html',
            activos=[],
            totales={"valor_comercial": 0, "depreciacion": 0, "valor_libros": 0}
        )
    # 2. Calcular totales para el resumen
    total_valor_comercial = sum(a.valor_comercial for a in activos)
    total_depreciacion = sum(a.depreciacion_acumulada for a in activos)
    total_valor_libros = sum(a.valor_en_libros for a in activos)

    context = {
        "activos": activos,
        "totales": {
            "valor_comercial": total_valor_comercial,
            "depreciacion": total_depreciacion,
            "valor_libros": total_valor_libros
        },
        "generado": datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema" # Placeholder
    }

    # 3. Si la solicitud es para generar un PDF
    if request.method == 'POST' and request.form.get('action') == 'generate_pdf':
        try:
            # Renderizar la plantilla específica para PDF
            html = render_template('pdf_templates/reporte_depreciacion_pdf.html', **context)
            
            # Generar el PDF con WeasyPrint
            pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()

            # Crear y devolver la respuesta PDF
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="Reporte_Depreciacion_{datetime.now().strftime("%Y%m%d")}.pdf"'
            return response

        except Exception as e:
            current_app.logger.error(f"Error generando PDF de depreciación: {e}")
            return "Error al generar el PDF.", 500

    # 4. Por defecto (GET), mostrar el reporte en HTML
    return render_template(
        'reportes/reporte_depreciacion.html',
        **context,
        active_page='reportes'
    )