from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import select, or_
from ..extensions import db
from ..models import Funcionario, Activo, Movimiento
from ..decorators import login_required, role_required

funcionarios_bp = Blueprint("funcionarios", __name__, template_folder="templates")


@funcionarios_bp.route("/")
@login_required
@role_required("Admin")
def ver_funcionarios():
    query = request.args.get("q", "").strip()
    stmt = select(Funcionario)
    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                Funcionario.nombres.ilike(search_term),
                Funcionario.apellidos.ilike(search_term),
                Funcionario.cedula.ilike(search_term),
            )
        )
    stmt = stmt.order_by(Funcionario.apellidos, Funcionario.nombres)
    funcionarios = db.session.execute(stmt).scalars().all()
    return render_template(
        "funcionarios/ver_funcionarios.html",
        funcionarios=funcionarios,
        query=query,
        active_page="funcionarios",
    )


@funcionarios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def add_funcionario():
    if request.method == "POST":
        try:
            nuevo_funcionario = Funcionario(
                nombres=request.form["nombres"],
                apellidos=request.form["apellidos"],
                cedula=request.form.get("cedula"),
                cargo=request.form.get("cargo"),
                area=request.form.get("area"),
            )
            db.session.add(nuevo_funcionario)
            db.session.commit()
            flash("Funcionario agregado exitosamente.", "success")
            return redirect(url_for("funcionarios.ver_funcionarios"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar funcionario: {e}", "danger")
            return redirect(url_for("funcionarios.add_funcionario"))
    return render_template(
        "funcionarios/add_funcionario.html", active_page="funcionarios"
    )


@funcionarios_bp.route("/editar/<int:funcionario_id>", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def edit_funcionario(funcionario_id):
    funcionario = db.session.get(Funcionario, funcionario_id)
    if not funcionario:
        flash("Funcionario no encontrado.", "danger")
        return redirect(url_for("funcionarios.ver_funcionarios"))
    if request.method == "POST":
        try:
            funcionario.nombres = request.form["nombres"]
            funcionario.apellidos = request.form["apellidos"]
            funcionario.cedula = request.form["cedula"]
            funcionario.cargo = request.form.get("cargo")
            funcionario.area = request.form.get("area")
            db.session.commit()
            flash("Datos del funcionario actualizados con éxito.", "success")
            return redirect(url_for("funcionarios.ver_funcionarios"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el funcionario: {e}", "danger")
            return redirect(
                url_for("funcionarios.edit_funcionario", funcionario_id=funcionario_id)
            )
    return render_template(
        "funcionarios/edit_funcionario.html",
        funcionario=funcionario,
        active_page="funcionarios",
    )


@funcionarios_bp.route("/eliminar/<int:funcionario_id>", methods=["POST"])
@login_required
@role_required("Admin")
def delete_funcionario(funcionario_id):
    funcionario = db.session.get(Funcionario, funcionario_id)
    if not funcionario:
        flash("Funcionario no encontrado.", "danger")
        return redirect(url_for("funcionarios.ver_funcionarios"))

    try:
        # Validaciones de integridad
        if funcionario.activos:
            flash(
                "No se puede eliminar el funcionario porque tiene activos asignados. Reasigne los activos primero.",
                "danger",
            )
            return redirect(url_for("funcionarios.ver_funcionarios"))

        # También chequear movimientos relacionados
        movimiento_relacionado = db.session.execute(
            select(Movimiento).where(Movimiento.funcionario_id == funcionario_id)
        ).first()
        if movimiento_relacionado:
            flash(
                "No se puede eliminar el funcionario porque está asociado a uno o más movimientos.",
                "danger",
            )
            return redirect(url_for("funcionarios.ver_funcionarios"))

        db.session.delete(funcionario)
        db.session.commit()
        flash("Funcionario eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el funcionario: {e}", "danger")
    return redirect(url_for("funcionarios.ver_funcionarios"))


@funcionarios_bp.route("/api/buscar")
@login_required
def buscar_funcionarios():
    term = request.args.get("term", "")
    search_term = f"%{term}%"
    stmt = (
        select(Funcionario)
        .where(
            or_(
                Funcionario.nombres.ilike(search_term),
                Funcionario.apellidos.ilike(search_term),
                Funcionario.cedula.ilike(search_term),
            )
        )
        .limit(10)
    )
    funcionarios = db.session.execute(stmt).scalars().all()
    return jsonify(
        [
            {
                "id": f.id,
                "nombres": f.nombres,
                "apellidos": f.apellidos,
                "cedula": f.cedula,
                "cargo": f.cargo,
                "area": f.area,
            }
            for f in funcionarios
        ]
    )
