import sqlite3
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify
)
from ..extensions import db
from ..decorators import login_required, role_required

proveedores_bp = Blueprint('proveedores', __name__, template_folder='templates')

@proveedores_bp.route('/')
@login_required
@role_required('Admin')
def ver_proveedores():
    database = db.get_db()
    query = request.args.get('q', '').strip()
    sql_query = "SELECT * FROM proveedores"
    params = []
    if query:
        sql_query += " WHERE razon_social LIKE ? OR nit LIKE ?"
        search_term = f'%{query}%'
        params.extend([search_term, search_term])
    sql_query += " ORDER BY razon_social"
    proveedores = database.execute(sql_query, tuple(params)).fetchall()
    return render_template(
        'proveedores/ver_proveedores.html',
        proveedores=proveedores,
        query=query,
        active_page='proveedores'
    )

@proveedores_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_proveedor():
    if request.method == 'POST':
        database = db.get_db()
        try:
            database.execute(
                'INSERT INTO proveedores (razon_social, nit, direccion, persona_contacto, numero_contacto) VALUES (?, ?, ?, ?, ?)',
                (request.form['razon_social'], request.form.get('nit'), request.form.get('direccion'), request.form.get('persona_contacto'), request.form.get('numero_contacto'))
            )
            database.commit()
            flash('Proveedor agregado exitosamente.', 'success')
            return redirect(url_for('proveedores.ver_proveedores'))
        except sqlite3.IntegrityError:
            flash('Error: La Razón Social o el NIT de ese proveedor ya existe.', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')
    return render_template('proveedores/add_proveedor.html', active_page='proveedores')

@proveedores_bp.route('/editar/<int:proveedor_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_proveedor(proveedor_id):
    database = db.get_db()
    proveedor = database.execute('SELECT * FROM proveedores WHERE id = ?', (proveedor_id,)).fetchone()
    if not proveedor:
        flash('Proveedor no encontrado.', 'danger')
        return redirect(url_for('proveedores.ver_proveedores'))
    if request.method == 'POST':
        try:
            database.execute("""
                UPDATE proveedores SET razon_social = ?, nit = ?, direccion = ?, persona_contacto = ?, numero_contacto = ?
                WHERE id = ?
            """, (
                request.form['razon_social'], request.form.get('nit'), request.form.get('direccion'),
                request.form.get('persona_contacto'), request.form.get('numero_contacto'),
                proveedor_id
            ))
            database.commit()
            flash('Proveedor actualizado con éxito.', 'success')
            return redirect(url_for('proveedores.ver_proveedores'))
        except sqlite3.IntegrityError:
            flash('Error: Ya existe otro proveedor con esa Razón Social o NIT.', 'danger')
        except Exception as e:
            flash(f'Error al actualizar el proveedor: {e}', 'danger')
    return render_template('proveedores/edit_proveedor.html', proveedor=proveedor, active_page='proveedores')

@proveedores_bp.route('/eliminar/<int:proveedor_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_proveedor(proveedor_id):
    database = db.get_db()
    try:
        movimiento = database.execute('SELECT id FROM movimientos WHERE proveedor_id = ?', (proveedor_id,)).fetchone()
        if movimiento:
            flash('No se puede eliminar el proveedor porque está asociado a uno o más movimientos.', 'danger')
            return redirect(url_for('proveedores.ver_proveedores'))
        database.execute('DELETE FROM proveedores WHERE id = ?', (proveedor_id,))
        database.commit()
        flash('Proveedor eliminado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar el proveedor: {e}', 'danger')
    return redirect(url_for('proveedores.ver_proveedores'))

@proveedores_bp.route('/api/buscar')
@login_required
def buscar_proveedores():
    term = request.args.get('term', '')
    if len(term) < 2:
        return jsonify([])
    database = db.get_db()
    query = "SELECT id, razon_social, nit FROM proveedores WHERE razon_social LIKE ? OR nit LIKE ?"
    search_term = f'%{term}%'
    proveedores = database.execute(query, (search_term, search_term)).fetchall()
    return jsonify([dict(row) for row in proveedores])