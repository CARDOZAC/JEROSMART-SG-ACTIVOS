"""
Rutas para exportación de movimientos a Excel.
Se separan en un archivo independiente para mantener routes.py organizado.
"""

from flask import send_file, current_app
from datetime import datetime
from ..decorators import login_required
from ..permissions import require_permission
from ..models import Movimiento, MovimientoActivo
from ..extensions import db
from ..excel_export import (
    exportar_movimientos_excel,
    exportar_movimiento_detallado_excel,
    exportar_estadisticas_excel
)
from . import movimientos_bp
from sqlalchemy import select, func


@movimientos_bp.route('/exportar/excel')
@login_required
@require_permission('exportar_datos')
def exportar_movimientos_excel_route():
    """
    Exporta todos los movimientos a Excel con filtros aplicados.
    """
    from flask import request

    # Obtener filtros desde query params
    filtros = {
        'q': request.args.get('q', '').strip(),
        'tipo': request.args.get('tipo', '')
    }

    # Construir consulta base
    query = db.session.query(Movimiento)\
        .join(MovimientoActivo, isouter=True)

    # Aplicar filtros
    if filtros['tipo']:
        query = query.filter(Movimiento.tipo_movimiento == filtros['tipo'])
    if filtros['q']:
        search_term = f"%{filtros['q']}%"
        query = query.filter(Movimiento.observaciones_generales.ilike(search_term))

    # Obtener movimientos ordenados
    movimientos = query.order_by(Movimiento.fecha.desc()).all()

    try:
        # Generar archivo Excel
        excel_file = exportar_movimientos_excel(movimientos, filtros)

        # Nombre del archivo con timestamp
        filename = f"movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Enviar archivo
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error exportando movimientos a Excel: {e}", exc_info=True)
        from flask import flash, redirect, url_for
        flash(f'Error al exportar a Excel: {str(e)}', 'danger')
        return redirect(url_for('movimientos.ver_movimientos'))


@movimientos_bp.route('/<int:movimiento_id>/exportar/excel')
@login_required
@require_permission('ver_movimiento')
def exportar_movimiento_detalle_excel(movimiento_id):
    """
    Exporta un movimiento individual con todos sus detalles a Excel.
    """
    movimiento = db.session.get(Movimiento, movimiento_id)

    if not movimiento:
        from flask import flash, redirect, url_for
        flash(f'Movimiento #{movimiento_id} no encontrado.', 'danger')
        return redirect(url_for('movimientos.ver_movimientos'))

    try:
        # Generar archivo Excel
        excel_file = exportar_movimiento_detallado_excel(movimiento)

        # Nombre del archivo
        filename = f"movimiento_{movimiento_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error exportando movimiento {movimiento_id} a Excel: {e}", exc_info=True)
        from flask import flash, redirect, url_for
        flash(f'Error al exportar a Excel: {str(e)}', 'danger')
        return redirect(url_for('movimientos.ver_movimiento', movimiento_id=movimiento_id))


@movimientos_bp.route('/dashboard/exportar/excel')
@login_required
@require_permission('ver_reportes')
def exportar_dashboard_excel():
    """
    Exporta las estadísticas del dashboard a Excel.
    """
    from datetime import timedelta
    from sqlalchemy import extract
    from ..models import User, Activo

    # Reutilizar la misma lógica del dashboard
    hoy = datetime.now()
    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calcular estadísticas
    stats = {}
    stats['total_movimientos'] = db.session.query(func.count(Movimiento.id)).scalar() or 0
    stats['movimientos_mes_actual'] = db.session.query(func.count(Movimiento.id))\
        .filter(Movimiento.fecha >= primer_dia_mes).scalar() or 0
    stats['pendientes_aprobacion'] = db.session.query(func.count(Movimiento.id))\
        .filter(Movimiento.estado_aprobacion == 'Pendiente').scalar() or 0
    stats['aprobados_mes'] = db.session.query(func.count(Movimiento.id))\
        .filter(Movimiento.estado_aprobacion == 'Aprobado', Movimiento.fecha >= primer_dia_mes).scalar() or 0
    stats['valor_total_mes'] = db.session.query(func.sum(MovimientoActivo.valor_libros_momento))\
        .join(Movimiento).filter(Movimiento.fecha >= primer_dia_mes).scalar() or 0

    # Movimientos por tipo
    tipos_query = db.session.query(Movimiento.tipo_movimiento, func.count(Movimiento.id))\
        .group_by(Movimiento.tipo_movimiento).all()
    stats['tipos_labels'] = [t[0] for t in tipos_query]
    stats['tipos_data'] = [t[1] for t in tipos_query]

    # Activos más movidos
    activos_query = db.session.query(
        Activo.placa_codigo_interno,
        Activo.nombre_activo,
        func.count(MovimientoActivo.id)
    )\
    .join(MovimientoActivo)\
    .group_by(Activo.id, Activo.placa_codigo_interno, Activo.nombre_activo)\
    .order_by(func.count(MovimientoActivo.id).desc())\
    .limit(10)\
    .all()

    stats['activos_mas_movidos'] = [
        {'placa': a[0], 'nombre': a[1], 'cantidad': a[2]}
        for a in activos_query
    ]

    try:
        # Generar archivo Excel
        excel_file = exportar_estadisticas_excel(stats)

        filename = f"estadisticas_movimientos_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error exportando estadísticas a Excel: {e}", exc_info=True)
        from flask import flash, redirect, url_for
        flash(f'Error al exportar estadísticas: {str(e)}', 'danger')
        return redirect(url_for('movimientos.dashboard'))
