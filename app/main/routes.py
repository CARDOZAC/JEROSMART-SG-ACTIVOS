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

    # Alertas de activos ajenos con contrato próximo a vencer (30 días)
    from datetime import date, timedelta

    hoy = date.today()
    limite_alerta = hoy + timedelta(days=30)

    # Se filtra en SQL sobre la columna Date, sin parsear strings en Python.
    activos_por_vencer = db.session.scalars(
        select(Activo)
        .where(
            Activo.tipo_propiedad == 'Ajeno',
            Activo.fecha_fin_contrato.isnot(None),
            Activo.fecha_fin_contrato >= hoy,
            Activo.fecha_fin_contrato <= limite_alerta
        )
        .order_by(Activo.fecha_fin_contrato.asc())
        .limit(5)
    ).all()

    alertas_activos_ajenos = [
        {
            'nombre_activo': a.nombre_activo,
            'propietario_ajeno': a.propietario_ajeno,
            'dias_restantes': a.dias_para_vencimiento_contrato
        }
        for a in activos_por_vencer
    ]

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
    # Si el activo no tiene costo_mensual registrado se estima en 10% del valor comercial.
    costo_mensual_total = 0.0
    for activo in activos_ajenos:
        if activo.condicion_tenencia in ['Arriendo', 'Leasing']:
            if activo.costo_mensual:
                costo_mensual_total += activo.costo_mensual
            elif activo.valor_comercial:
                costo_mensual_total += activo.valor_comercial * 0.1

    # ALERTAS: Contratos próximos a vencer (90 días)
    alertas = [
        {
            'nombre_activo': activo.nombre_activo,
            'propietario_ajeno': activo.propietario_ajeno or 'No especificado',
            'fecha_fin_contrato': activo.fecha_fin_contrato.strftime('%d/%m/%Y'),
            'dias_restantes': activo.dias_para_vencimiento_contrato
        }
        for activo in activos_ajenos
        if activo.contrato_proximo_a_vencer(dias_alerta=90)
    ]

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
