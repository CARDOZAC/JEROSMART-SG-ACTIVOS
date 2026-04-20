from flask import (
    Blueprint,
    render_template,
    session,
    current_app,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
)
from sqlalchemy import select, func
from ..extensions import db
from ..decorators import login_required
from ..models import Activo, Funcionario, Movimiento, ClaseActivo

# El Blueprint 'main' es el punto de entrada principal y no debería tener un prefijo de URL.
# Se registrará en la raíz '/'.
main_bp = Blueprint("main", __name__, template_folder="templates")


@main_bp.route("/")
@login_required
def index():
    """
    Ruta del panel de control principal (Dashboard).
    """
    total_activos = db.session.scalar(select(func.count(Activo.id)))
    total_funcionarios = db.session.scalar(select(func.count(Funcionario.id)))
    total_movimientos = db.session.scalar(select(func.count(Movimiento.id)))

    # Últimos activos con su clase
    stmt_ultimos = (
        select(Activo, ClaseActivo.nombre_clase)
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
        .order_by(Activo.id.desc())
        .limit(5)
    )
    result_ultimos = db.session.execute(stmt_ultimos).all()
    ultimos_activos = []
    for activo, nombre_clase in result_ultimos:
        activo_dict = {
            "id": activo.id,
            "nombre_activo": activo.nombre_activo,
            "placa_codigo_interno": activo.placa_codigo_interno,
            "nombre_clase": nombre_clase,
        }
        ultimos_activos.append(activo_dict)

    # Activos por clase
    stmt_clase = (
        select(ClaseActivo.nombre_clase, func.count(Activo.id).label("count"))
        .join(Activo, ClaseActivo.id == Activo.clase_id)
        .group_by(ClaseActivo.nombre_clase)
        .order_by(func.count(Activo.id).desc())
    )
    activos_por_clase = [
        dict(row) for row in db.session.execute(stmt_clase).mappings().all()
    ]

    # Movimientos por tipo
    stmt_mov = (
        select(Movimiento.tipo_movimiento, func.count(Movimiento.id).label("count"))
        .group_by(Movimiento.tipo_movimiento)
        .order_by(func.count(Movimiento.id).desc())
    )
    movimientos_por_tipo = [
        dict(row) for row in db.session.execute(stmt_mov).mappings().all()
    ]

    return render_template(
        "index.html",
        total_activos=total_activos,
        total_funcionarios=total_funcionarios,
        total_movimientos=total_movimientos,
        ultimos_activos=ultimos_activos,
        activos_por_clase=activos_por_clase,
        movimientos_por_tipo=movimientos_por_tipo,
        active_page="index",
    )


@main_bp.route("/inventario_ajenos")
@login_required
def inventario_ajenos():
    stmt = (
        select(Activo)
        .where(Activo.tipo_propiedad == "Ajeno")
        .order_by(Activo.nombre_activo)
    )
    activos_ajenos = db.session.execute(stmt).scalars().all()
    return render_template(
        "inventario_ajenos.html",
        activos_ajenos=activos_ajenos,
        active_page="inventario_ajenos",
    )
