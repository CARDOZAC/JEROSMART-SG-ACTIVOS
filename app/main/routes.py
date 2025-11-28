from flask import (
    Blueprint, render_template, session, current_app,
    jsonify, request, redirect, url_for, flash
)
import json
from sqlalchemy import select, func
from ..extensions import db
from ..models import Activo, Funcionario, Movimiento, ClaseActivo
from ..decorators import login_required

# El Blueprint 'main' es el punto de entrada principal y no debería tener un prefijo de URL.
# Se registrará en la raíz '/'.
main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
@login_required
def index():
    """
    Ruta del panel de control principal (Dashboard).
    """
    # Obtener totales usando SQLAlchemy ORM
    total_activos = db.session.scalar(select(func.count(Activo.id)))
    total_funcionarios = db.session.scalar(select(func.count(Funcionario.id)))
    total_movimientos = db.session.scalar(select(func.count(Movimiento.id)))

    # Últimos activos creados
    stmt = (
        select(Activo, ClaseActivo)
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
        .filter(Activo.fecha_ingreso_ajeno.isnot(None)) # Add this line to filter out NULL values
        .order_by(Activo.id.desc())
        .limit(5)
    )
    results = db.session.execute(stmt).all()
    ultimos_activos = [
        {
            'id': activo.id,
            'nombre_activo': activo.nombre_activo,
            'placa_codigo_interno': activo.placa_codigo_interno,
            'nombre_clase': clase.nombre_clase if clase else None
        }
        for activo, clase in results
    ]

    # Activos por clase
    stmt = (
        select(ClaseActivo.nombre_clase, func.count(Activo.id).label('count'))
        .select_from(Activo)
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
        .group_by(ClaseActivo.nombre_clase)
        .order_by(func.count(Activo.id).desc())
    )
    activos_por_clase_results = db.session.execute(stmt).all()
    activos_por_clase = [
        {'nombre_clase': nombre_clase, 'count': count}
        for nombre_clase, count in activos_por_clase_results
    ]

    # Movimientos por tipo
    stmt = (
        select(Movimiento.tipo_movimiento, func.count(Movimiento.id).label('count'))
        .group_by(Movimiento.tipo_movimiento)
        .order_by(func.count(Movimiento.id).desc())
    )
    movimientos_por_tipo_results = db.session.execute(stmt).all()
    movimientos_por_tipo = [
        {'tipo_movimiento': tipo, 'count': count}
        for tipo, count in movimientos_por_tipo_results
    ]

    # NUEVO: Alertas de activos ajenos próximos a vencer
    from datetime import datetime, timedelta

    alertas_activos_ajenos = []
    stmt_ajenos = select(Activo).where(Activo.tipo_propiedad == 'Ajeno')
    activos_ajenos = db.session.execute(stmt_ajenos).scalars().all()

    hoy = datetime.now()
    for activo in activos_ajenos:
        try:
            if hasattr(activo, 'fecha_fin_contrato') and activo.fecha_fin_contrato:
                for formato in ['%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        fecha_fin = datetime.strptime(activo.fecha_fin_contrato.split()[0], formato)
                        break
                    except:
                        continue
                else:
                    continue

                dias_restantes = (fecha_fin - hoy).days
                if 0 < dias_restantes <= 30:  # Solo próximos 30 días para el dashboard principal
                    alertas_activos_ajenos.append({
                        'nombre_activo': activo.nombre_activo,
                        'propietario_ajeno': activo.propietario_ajeno,
                        'dias_restantes': dias_restantes
                    })
        except:
            pass

    alertas_activos_ajenos = sorted(alertas_activos_ajenos, key=lambda x: x['dias_restantes'])[:5]  # Top 5

    return render_template(
        'index.html',
        total_activos=total_activos,
        total_funcionarios=total_funcionarios,
        total_movimientos=total_movimientos,
        ultimos_activos=ultimos_activos,
        activos_por_clase=activos_por_clase,
        movimientos_por_tipo=movimientos_por_tipo, # noqa
        alertas_activos_ajenos=alertas_activos_ajenos, # noqa
        active_page='index' # noqa
    )

@main_bp.route('/inventario_ajenos')
@login_required
def inventario_ajenos():
    """
    Dashboard profesional de activos ajenos (comodato, arriendo, leasing).
    Incluye KPIs, alertas de vencimiento y estadísticas por proveedor.
    """
    from datetime import datetime, timedelta

    # Obtener todos los activos ajenos
    stmt = (
        select(Activo)
        .where(Activo.tipo_propiedad == 'Ajeno')
        .order_by(Activo.nombre_activo)
    )
    activos_ajenos = db.session.execute(stmt).scalars().all()

    # KPI 1: Total de activos ajenos
    total_ajenos = len(activos_ajenos)

    # KPI 2: Total en comodato (gratuito)
    total_comodato = sum(1 for a in activos_ajenos if a.condicion_tenencia == 'Comodato')

    # KPI 3: Costo mensual total (solo arriendos y leasing)
    # NOTA: Si aún no has ejecutado la migración, usa valor_comercial/10 como estimado
    costo_mensual_total = 0
    for activo in activos_ajenos:
        if activo.condicion_tenencia in ['Arriendo', 'Leasing']:
            # Intentar obtener costo_mensual si existe, sino estimar
            try:
                if hasattr(activo, 'costo_mensual') and activo.costo_mensual:
                    costo_mensual_total += activo.costo_mensual
                elif activo.valor_comercial:
                    # Estimado: 10% del valor comercial mensual
                    costo_mensual_total += activo.valor_comercial * 0.1
            except:
                pass

    # ALERTAS: Contratos próximos a vencer (90 días)
    alertas = []
    hoy = datetime.now()

    for activo in activos_ajenos:
        # Intentar obtener fecha_fin_contrato si existe
        fecha_fin_str = None
        try:
            if hasattr(activo, 'fecha_fin_contrato'):
                fecha_fin_str = activo.fecha_fin_contrato
        except:
            pass

        if fecha_fin_str:
            try:
                # Parsear fecha (soportar varios formatos)
                for formato in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        fecha_fin = datetime.strptime(fecha_fin_str.split()[0], formato)
                        break
                    except:
                        continue
                else:
                    continue  # Si ningún formato funcionó, skip

                dias_restantes = (fecha_fin - hoy).days

                # Solo incluir si está entre 0 y 90 días
                if 0 < dias_restantes <= 90:
                    alertas.append({
                        'nombre_activo': activo.nombre_activo,
                        'propietario_ajeno': activo.propietario_ajeno or 'No especificado',
                        'fecha_fin_contrato': fecha_fin.strftime('%d/%m/%Y'),
                        'dias_restantes': dias_restantes
                    })
            except Exception as e:
                current_app.logger.warning(f"Error procesando fecha de contrato para activo {activo.id}: {e}")
                pass

    # Ordenar alertas por días restantes (más urgentes primero)
    alertas_ordenadas = sorted(alertas, key=lambda x: x['dias_restantes'])

    # ESTADÍSTICAS: Activos por proveedor/propietario
    stmt_proveedores = (
        select(
            Activo.propietario_ajeno.label('propietario'),
            func.count(Activo.id).label('cantidad')
        )
        .where(Activo.tipo_propiedad == 'Ajeno')
        .where(Activo.propietario_ajeno.isnot(None))
        .group_by(Activo.propietario_ajeno)
        .order_by(func.count(Activo.id).desc())
    )

    activos_por_proveedor_results = db.session.execute(stmt_proveedores).all()
    activos_por_proveedor = [
        {'propietario': propietario, 'cantidad': cantidad}
        for propietario, cantidad in activos_por_proveedor_results
    ]

    return render_template('inventario_ajenos.html',
                         activos_ajenos=activos_ajenos,
                         total_ajenos=total_ajenos,
                         total_comodato=total_comodato,
                         costo_mensual_total=costo_mensual_total,
                         contratos_proximos_vencer=len(alertas_ordenadas),
                         alertas=alertas_ordenadas,
                         activos_por_proveedor=activos_por_proveedor,
                         active_page='inventario_ajenos')
