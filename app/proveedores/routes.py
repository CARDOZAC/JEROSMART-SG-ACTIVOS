from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import select, or_
from ..extensions import db
from ..models import Proveedor, DetalleEntrega
from ..decorators import login_required, role_required

proveedores_bp = Blueprint("proveedores", __name__, template_folder="templates")


@proveedores_bp.route("/")
@login_required
@role_required("Admin")
def ver_proveedores():
    query = request.args.get("q", "").strip()
    stmt = select(Proveedor)
    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                Proveedor.razon_social.ilike(search_term),
                Proveedor.nit.ilike(search_term),
            )
        )
    stmt = stmt.order_by(Proveedor.razon_social)
    proveedores = db.session.execute(stmt).scalars().all()
    return render_template(
        "proveedores/ver_proveedores.html",
        proveedores=proveedores,
        query=query,
        active_page="proveedores",
    )


@proveedores_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def add_proveedor():
    if request.method == "POST":
        try:
            nuevo_proveedor = Proveedor(
                razon_social=request.form["razon_social"],
                nit=request.form.get("nit"),
                direccion=request.form.get("direccion"),
                persona_contacto=request.form.get("persona_contacto"),
                numero_contacto=request.form.get("numero_contacto"),
            )
            db.session.add(nuevo_proveedor)
            db.session.commit()
            flash("Proveedor agregado exitosamente.", "success")
            return redirect(url_for("proveedores.ver_proveedores"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar proveedor: {e}", "danger")
    return render_template("proveedores/add_proveedor.html", active_page="proveedores")


@proveedores_bp.route("/editar/<int:proveedor_id>", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def edit_proveedor(proveedor_id):
    proveedor = db.session.get(Proveedor, proveedor_id)
    if not proveedor:
        flash("Proveedor no encontrado.", "danger")
        return redirect(url_for("proveedores.ver_proveedores"))
    if request.method == "POST":
        try:
            proveedor.razon_social = request.form["razon_social"]
            proveedor.nit = request.form.get("nit")
            proveedor.direccion = request.form.get("direccion")
            proveedor.persona_contacto = request.form.get("persona_contacto")
            proveedor.numero_contacto = request.form.get("numero_contacto")
            db.session.commit()
            flash("Proveedor actualizado con éxito.", "success")
            return redirect(url_for("proveedores.ver_proveedores"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el proveedor: {e}", "danger")
    return render_template(
        "proveedores/edit_proveedor.html",
        proveedor=proveedor,
        active_page="proveedores",
    )


@proveedores_bp.route("/eliminar/<int:proveedor_id>", methods=["POST"])
@login_required
@role_required("Admin")
def delete_proveedor(proveedor_id):
    proveedor = db.session.get(Proveedor, proveedor_id)
    if not proveedor:
        flash("Proveedor no encontrado.", "danger")
        return redirect(url_for("proveedores.ver_proveedores"))

    try:
        # Chequear si está asociado a algún DetalleEntrega
        if proveedor.detalles_entrega:
            flash(
                "No se puede eliminar el proveedor porque está asociado a uno o más movimientos.",
                "danger",
            )
            return redirect(url_for("proveedores.ver_proveedores"))

        db.session.delete(proveedor)
        db.session.commit()
        flash("Proveedor eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el proveedor: {e}", "danger")
    return redirect(url_for("proveedores.ver_proveedores"))


@proveedores_bp.route("/api/buscar")
@login_required
def buscar_proveedores():
    term = request.args.get("term", "")
    if len(term) < 2:
        return jsonify([])
    search_term = f"%{term}%"
    stmt = (
        select(Proveedor)
        .where(
            or_(
                Proveedor.razon_social.ilike(search_term),
                Proveedor.nit.ilike(search_term),
            )
        )
        .limit(10)
    )
    proveedores = db.session.execute(stmt).scalars().all()
    return jsonify(
        [
            {"id": p.id, "razon_social": p.razon_social, "nit": p.nit}
            for p in proveedores
        ]
    )
