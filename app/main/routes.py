from flask import (
    Blueprint, render_template, session, current_app,
    jsonify, request, redirect, url_for, flash
)
import json
from ..extensions import db
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
    database = db.get_db()
    total_activos = database.execute("SELECT COUNT(id) FROM activos").fetchone()[0]
    total_funcionarios = database.execute("SELECT COUNT(id) FROM funcionarios").fetchone()[0]
    total_movimientos = database.execute("SELECT COUNT(id) FROM movimientos").fetchone()[0]

    ultimos_activos = database.execute(
        "SELECT a.id, a.nombre_activo, a.placa_codigo_interno, c.nombre_clase "
        "FROM activos a LEFT JOIN clases_activo c ON a.clase_id = c.id "
        "ORDER BY a.id DESC LIMIT 5"
    ).fetchall()

    activos_por_clase = database.execute("""
        SELECT c.nombre_clase, COUNT(a.id) as count
        FROM activos a
        LEFT JOIN clases_activo c ON a.clase_id = c.id
        GROUP BY c.nombre_clase
        ORDER BY count DESC
    """).fetchall()

    movimientos_por_tipo = database.execute("""
        SELECT tipo_movimiento, COUNT(id) as count
        FROM movimientos
        GROUP BY tipo_movimiento
        ORDER BY count DESC
    """).fetchall()

    return render_template(
        'index.html',
        total_activos=total_activos,
        total_funcionarios=total_funcionarios,
        total_movimientos=total_movimientos,
        ultimos_activos=ultimos_activos,
        activos_por_clase=[dict(row) for row in activos_por_clase],
        movimientos_por_tipo=[dict(row) for row in movimientos_por_tipo],
        active_page='index'
    )

@main_bp.route('/inventario_ajenos')
@login_required
def inventario_ajenos():
    database = db.get_db()
    activos_ajenos = database.execute("SELECT * FROM activos WHERE tipo_propiedad = 'Ajeno' ORDER BY nombre_activo").fetchall()
    return render_template('inventario_ajenos.html', activos_ajenos=activos_ajenos, active_page='inventario_ajenos')