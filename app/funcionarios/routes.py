import sqlite3
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify
)
from ..extensions import db
from ..decorators import login_required, role_required

funcionarios_bp = Blueprint('funcionarios', __name__, template_folder='templates')

@funcionarios_bp.route('/')
@login_required
@role_required('Admin')
def ver_funcionarios():
    database = db.get_db()
    query = request.args.get('q', '').strip()
    sql_query = "SELECT * FROM funcionarios"
    params = []
    if query:
        sql_query += " WHERE nombres LIKE ? OR apellidos LIKE ? OR cedula LIKE ?"
        search_term = f'%{query}%'
        params.extend([search_term, search_term, search_term])
    sql_query += " ORDER BY apellidos, nombres"
    funcionarios = database.execute(sql_query, tuple(params)).fetchall()
    return render_template(
        'funcionarios/ver_funcionarios.html',
        funcionarios=funcionarios,
        query=query,
        active_page='funcionarios'
    )

@funcionarios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_funcionario():
    if request.method == 'POST':
        database = db.get_db()
        try:
            database.execute(
                'INSERT INTO funcionarios (nombres, apellidos, cedula, cargo, area) VALUES (?, ?, ?, ?, ?)',
                (request.form['nombres'], request.form['apellidos'], request.form.get('cedula'), request.form.get('cargo'), request.form.get('area'))
            )
            database.commit()
            flash('Funcionario agregado exitosamente.', 'success')
            return redirect(url_for('funcionarios.ver_funcionarios'))
        except sqlite3.IntegrityError:
            flash('Error: La cédula de ese funcionario ya existe.', 'danger')
            return redirect(url_for('funcionarios.add_funcionario'))
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')
    return render_template('funcionarios/add_funcionario.html', active_page='funcionarios')

@funcionarios_bp.route('/editar/<int:funcionario_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_funcionario(funcionario_id):
    database = db.get_db()
    funcionario = database.execute('SELECT * FROM funcionarios WHERE id = ?', (funcionario_id,)).fetchone()
    if not funcionario:
        flash('Funcionario no encontrado.', 'danger')
        return redirect(url_for('funcionarios.ver_funcionarios'))
    if request.method == 'POST':
        try:
            database.execute(
                'UPDATE funcionarios SET nombres = ?, apellidos = ?, cedula = ?, cargo = ?, area = ? WHERE id = ?',
                (request.form['nombres'], request.form['apellidos'], request.form['cedula'], request.form['cargo'], request.form['area'], funcionario_id)
            )
            database.commit()
            flash('Datos del funcionario actualizados con éxito.', 'success')
            return redirect(url_for('funcionarios.ver_funcionarios'))
        except sqlite3.IntegrityError:
            flash('Error: La cédula ya pertenece a otro funcionario.', 'danger')
            return redirect(url_for('funcionarios.edit_funcionario', funcionario_id=funcionario_id))
        except Exception as e:
            flash(f'Error al actualizar el funcionario: {e}', 'danger')
    return render_template('funcionarios/edit_funcionario.html', funcionario=funcionario, active_page='funcionarios')

@funcionarios_bp.route('/eliminar/<int:funcionario_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_funcionario(funcionario_id):
    database = db.get_db()
    try:
        activos_asignados = database.execute('SELECT id FROM activos WHERE funcionario_id = ?', (funcionario_id,)).fetchone()
        if activos_asignados:
            flash('No se puede eliminar el funcionario porque tiene activos asignados. Reasigne los activos primero.', 'danger')
            return redirect(url_for('funcionarios.ver_funcionarios'))
        movimientos_relacionados = database.execute('SELECT id FROM movimientos WHERE funcionario_id = ?', (funcionario_id,)).fetchone()
        if movimientos_relacionados:
            flash('No se puede eliminar el funcionario porque está asociado a uno o más movimientos.', 'danger')
            return redirect(url_for('funcionarios.ver_funcionarios'))
        database.execute('DELETE FROM funcionarios WHERE id = ?', (funcionario_id,))
        database.commit()
        flash('Funcionario eliminado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar el funcionario: {e}', 'danger')
    return redirect(url_for('funcionarios.ver_funcionarios'))

@funcionarios_bp.route('/api/buscar')
@login_required
def buscar_funcionarios():
    term = request.args.get('term', '')
    database = db.get_db()
    query = """
        SELECT id, nombres, apellidos, cedula, cargo, area FROM funcionarios
        WHERE nombres LIKE ? OR apellidos LIKE ? OR cedula LIKE ?
        LIMIT 10
    """
    term_like = f'%{term}%'
    funcionarios = database.execute(query, (term_like, term_like, term_like)).fetchall()
    return jsonify([dict(row) for row in funcionarios])