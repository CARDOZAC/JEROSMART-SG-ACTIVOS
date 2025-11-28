from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
)
from sqlalchemy import select, or_, exc
from sqlalchemy.sql import func
from ..extensions import db
from ..models import Funcionario, Activo, DetallePazSalvo
from ..decorators import login_required, role_required

funcionarios_bp = Blueprint('funcionarios', __name__, template_folder='templates')

@funcionarios_bp.route('/')
@login_required
def ver_funcionarios():
    """Muestra una lista de todos los funcionarios, con opción de búsqueda."""
    query = request.args.get('q', '').strip()

    stmt = select(Funcionario)
    if query:
        search_term = f'%{query}%'
        stmt = stmt.where(or_(
            Funcionario.nombres.ilike(search_term),
            Funcionario.apellidos.ilike(search_term),
            Funcionario.cedula.ilike(search_term)
        ))

    stmt = stmt.order_by(Funcionario.apellidos, Funcionario.nombres)
    funcionarios = db.session.execute(stmt).scalars().all()

    return render_template(
        'ver_funcionarios.html',
        funcionarios=funcionarios,
        query=query,
        active_page='funcionarios'
    )

@funcionarios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_funcionario():
    """Agrega un nuevo funcionario a la base de datos."""
    if request.method == 'POST':
        try:
            nuevo_funcionario = Funcionario(
                nombres=request.form['nombres'],
                apellidos=request.form['apellidos'],
                cedula=request.form.get('cedula'),
                cargo=request.form.get('cargo'),
                area=request.form.get('area'),
                centro_costo=request.form.get('centro_costo')
            )
            db.session.add(nuevo_funcionario)
            db.session.commit()
            flash('Funcionario agregado exitosamente.', 'success')
            return redirect(url_for('funcionarios.ver_funcionarios'))
        except exc.IntegrityError:
            db.session.rollback()
            flash('Error: La cédula de ese funcionario ya existe.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error inesperado: {e}', 'danger')

    return render_template('add_funcionario.html', active_page='funcionarios')

@funcionarios_bp.route('/editar/<int:funcionario_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_funcionario(funcionario_id):
    """Edita los datos de un funcionario existente."""
    funcionario = db.session.get(Funcionario, funcionario_id)
    if not funcionario:
        flash('Funcionario no encontrado.', 'danger')
        return redirect(url_for('funcionarios.ver_funcionarios'))

    if request.method == 'POST':
        try:
            funcionario.nombres = request.form['nombres']
            funcionario.apellidos = request.form['apellidos']
            funcionario.cedula = request.form['cedula']
            funcionario.cargo = request.form['cargo']
            funcionario.area = request.form['area']
            funcionario.centro_costo = request.form.get('centro_costo')
            db.session.commit()
            flash('Datos del funcionario actualizados con éxito.', 'success')
            return redirect(url_for('funcionarios.ver_funcionarios'))
        except exc.IntegrityError:
            db.session.rollback()
            flash('Error: La cédula ya pertenece a otro funcionario.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el funcionario: {e}', 'danger')

    return render_template('edit_funcionario.html', funcionario=funcionario, active_page='funcionarios')

@funcionarios_bp.route('/eliminar/<int:funcionario_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_funcionario(funcionario_id):
    """Elimina un funcionario, con validaciones de integridad referencial."""
    funcionario = db.session.get(Funcionario, funcionario_id)
    if not funcionario:
        flash('Funcionario no encontrado.', 'danger')
        return redirect(url_for('funcionarios.ver_funcionarios'))

    try:
        # Validar si tiene activos asignados
        if db.session.query(Activo).filter_by(funcionario_id=funcionario_id).first():
            flash('No se puede eliminar el funcionario porque tiene activos asignados. Reasigne los activos primero.', 'danger')
            return redirect(url_for('funcionarios.ver_funcionarios'))

        # Validar si está en un acta de paz y salvo
        if db.session.query(DetallePazSalvo).filter_by(funcionario_desvinculado_id=funcionario_id).first():
            flash('No se puede eliminar el funcionario porque está asociado a un acta de Paz y Salvo.', 'danger')
            return redirect(url_for('funcionarios.ver_funcionarios'))

        db.session.delete(funcionario)
        db.session.commit()
        flash('Funcionario eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el funcionario: {e}', 'danger')
    return redirect(url_for('funcionarios.ver_funcionarios'))

@funcionarios_bp.route('/api/buscar')
@login_required
def buscar_funcionarios():
    term = request.args.get('term', '')
    if len(term) < 3: # Aumentamos a 3 caracteres para no sobrecargar la BD
        return jsonify([])

    search_term = f'%{term}%'
    # Se modifica la consulta para seleccionar solo las columnas necesarias
    # y eliminar la referencia a 'Funcionario.estado' que no existe en la BD.
    stmt = (
        select(
            Funcionario.id,
            Funcionario.nombres,
            Funcionario.apellidos,
            Funcionario.cedula,
            Funcionario.cargo,
            Funcionario.area,
            Funcionario.centro_costo
        )
        .where(
            or_(
                (Funcionario.nombres + ' ' + Funcionario.apellidos).ilike(search_term),
                Funcionario.cedula.ilike(search_term)
            )
        )
        .limit(10)
    )
    funcionarios = db.session.execute(stmt).all()

    # Devolver solo los campos necesarios para evitar exponer datos de más
    # El formato ahora es más útil para un autocompletado
    resultados = [{
        'id': f.id,
        'label': f"{f.nombres} {f.apellidos}", # Texto principal a mostrar
        'sublabel': f"C.C. {f.cedula} - {f.cargo or 'Sin Cargo'}", # Texto secundario
        'value': f"{f.nombres} {f.apellidos}", # Valor para el campo de nombre (autocompletado)
        'cedula': f.cedula,
        'cargo': f.cargo or '',
        'area': f.area or '',
        'centro_costo': f.centro_costo or ''
    } for f in funcionarios]
    return jsonify(resultados)


# ==============================================================================
# IMPORTACIÓN MASIVA DE FUNCIONARIOS DESDE CSV
# Implementación: James Gosling style - Robustez y detección automática
# ==============================================================================

@funcionarios_bp.route('/descargar-plantilla-csv')
@login_required
@role_required('Admin')
def descargar_plantilla_csv():
    """
    Endpoint para descargar la plantilla CSV de ejemplo para importación de funcionarios.
    """
    import os
    from flask import send_file, current_app

    plantilla_path = os.path.join(current_app.root_path, 'static', 'templates', 'plantilla_importacion_funcionarios.csv')

    if not os.path.exists(plantilla_path):
        flash('Plantilla CSV no encontrada. Contacte al administrador.', 'danger')
        return redirect(url_for('funcionarios.ver_funcionarios'))

    return send_file(
        plantilla_path,
        as_attachment=True,
        download_name='plantilla_importacion_funcionarios.csv',
        mimetype='text/csv'
    )

@funcionarios_bp.route('/importar', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def importar_csv():
    """
    Importación masiva de funcionarios desde archivo CSV.

    Mapeo de columnas CSV -> Modelo Funcionario:
    - 'Identificación' -> cedula (PK/Unique)
    - 'Nombres' -> nombres
    - 'Apellidos' -> apellidos
    - 'Descripción Cargo' -> cargo
    - 'Área' -> area

    Lógica de negocio (UPSERT):
    - Si existe un funcionario con esa cédula: ACTUALIZAR
    - Si no existe: CREAR nuevo registro
    """
    import csv
    import io
    from flask import current_app

    if request.method == 'POST':
        try:
            archivo_csv = request.files.get('archivo_csv')

            # Validación básica del archivo
            if not archivo_csv or archivo_csv.filename == '':
                flash('Por favor seleccione un archivo CSV.', 'warning')
                return redirect(url_for('funcionarios.importar_csv'))

            if not archivo_csv.filename.endswith('.csv'):
                flash('El archivo debe ser formato CSV (.csv)', 'danger')
                return redirect(url_for('funcionarios.importar_csv'))

            # Leer contenido del archivo con encoding UTF-8
            contenido_csv = archivo_csv.stream.read().decode('utf-8-sig')

            # Detección automática de delimitador (robustez)
            delimitador = ';'  # Por defecto punto y coma según requerimientos
            try:
                muestra = contenido_csv[:1024]
                sniffer = csv.Sniffer()
                delimitador = sniffer.sniff(muestra).delimiter
                current_app.logger.info(f"[Funcionarios CSV] Delimitador detectado automáticamente: {repr(delimitador)}")
            except Exception as e:
                # Fallback: detección manual
                primera_linea = contenido_csv.split('\n')[0] if contenido_csv else ''
                if ';' in primera_linea:
                    delimitador = ';'
                elif ',' in primera_linea:
                    delimitador = ','
                elif '\t' in primera_linea:
                    delimitador = '\t'
                current_app.logger.info(f"[Funcionarios CSV] Delimitador detectado manualmente: {repr(delimitador)}")

            # Procesar CSV
            stream = io.StringIO(contenido_csv, newline=None)
            csv_reader = csv.DictReader(stream, delimiter=delimitador)

            # Validación de columnas
            columnas_csv = csv_reader.fieldnames
            if not columnas_csv:
                flash('El archivo CSV está vacío o mal formateado.', 'danger')
                return redirect(url_for('funcionarios.importar_csv'))

            # Limpiar espacios en blanco de los headers
            columnas_csv = [col.strip() if col else col for col in columnas_csv]
            current_app.logger.info(f"[Funcionarios CSV] Columnas detectadas: {columnas_csv}")

            # Mapeo flexible de columnas (CSV -> Modelo)
            mapeo_columnas = {
                'Identificación': 'cedula',
                'Identificacion': 'cedula',
                'identificacion': 'cedula',
                'Cédula': 'cedula',
                'Cedula': 'cedula',
                'cedula': 'cedula',
                'Nombres': 'nombres',
                'nombres': 'nombres',
                'Apellidos': 'apellidos',
                'apellidos': 'apellidos',
                'Descripción Cargo': 'cargo',
                'Descripcion Cargo': 'cargo',
                'descripcion_cargo': 'cargo',
                'Cargo': 'cargo',
                'cargo': 'cargo',
                'Area': 'area',
                'Área': 'area',
                'area': 'area'
            }

            # Validar que existan las columnas obligatorias
            campos_requeridos = ['cedula', 'nombres', 'apellidos']
            campos_mapeados = set()

            for col_csv in columnas_csv:
                campo_modelo = mapeo_columnas.get(col_csv)
                if campo_modelo:
                    campos_mapeados.add(campo_modelo)

            campos_faltantes = [campo for campo in campos_requeridos if campo not in campos_mapeados]
            if campos_faltantes:
                flash(f'Columnas obligatorias faltantes: {", ".join(campos_faltantes)}. Necesita: Identificación, Nombres, Apellidos', 'danger')
                return redirect(url_for('funcionarios.importar_csv'))

            # Procesamiento de filas (UPSERT Logic)
            filas_exitosas = []
            filas_fallidas = []
            funcionarios_creados = 0
            funcionarios_actualizados = 0

            for idx, fila in enumerate(csv_reader, start=2):  # start=2 (fila 1 = headers)
                try:
                    # Extraer valores usando el mapeo
                    datos = {}
                    for col_csv, valor in fila.items():
                        col_csv = col_csv.strip() if col_csv else col_csv
                        campo_modelo = mapeo_columnas.get(col_csv)
                        if campo_modelo:
                            datos[campo_modelo] = valor.strip() if valor else ''

                    # Validaciones de negocio
                    cedula = datos.get('cedula', '').strip()
                    nombres = datos.get('nombres', '').strip()
                    apellidos = datos.get('apellidos', '').strip()

                    if not cedula:
                        filas_fallidas.append(f"Fila {idx}: La Identificación no puede estar vacía")
                        continue

                    if not nombres:
                        filas_fallidas.append(f"Fila {idx}: El campo Nombres no puede estar vacío")
                        continue

                    if not apellidos:
                        filas_fallidas.append(f"Fila {idx}: El campo Apellidos no puede estar vacío")
                        continue

                    # UPSERT: Buscar si existe el funcionario por cédula
                    funcionario_existente = db.session.scalar(
                        select(Funcionario).where(Funcionario.cedula == cedula)
                    )

                    if funcionario_existente:
                        # ACTUALIZAR funcionario existente
                        funcionario_existente.nombres = nombres
                        funcionario_existente.apellidos = apellidos
                        funcionario_existente.cargo = datos.get('cargo', funcionario_existente.cargo)
                        funcionario_existente.area = datos.get('area', funcionario_existente.area)
                        funcionarios_actualizados += 1
                        filas_exitosas.append(f"Fila {idx}: Funcionario {cedula} actualizado")
                        current_app.logger.info(f"[Funcionarios CSV] Actualizado: {cedula} - {nombres} {apellidos}")
                    else:
                        # CREAR nuevo funcionario
                        nuevo_funcionario = Funcionario(
                            cedula=cedula,
                            nombres=nombres,
                            apellidos=apellidos,
                            cargo=datos.get('cargo', ''),
                            area=datos.get('area', '')
                        )
                        db.session.add(nuevo_funcionario)
                        funcionarios_creados += 1
                        filas_exitosas.append(f"Fila {idx}: Funcionario {cedula} creado")
                        current_app.logger.info(f"[Funcionarios CSV] Creado: {cedula} - {nombres} {apellidos}")

                except Exception as e:
                    filas_fallidas.append(f"Fila {idx}: Error inesperado - {str(e)}")
                    current_app.logger.error(f"[Funcionarios CSV] Error en fila {idx}: {e}")

            # Commit de todos los cambios
            try:
                db.session.commit()

                # Mensaje de éxito
                mensaje_resumen = f'Importación completada: {funcionarios_creados} creado(s), {funcionarios_actualizados} actualizado(s)'
                if filas_fallidas:
                    mensaje_resumen += f', {len(filas_fallidas)} fallo(s)'
                    flash(mensaje_resumen, 'warning')
                else:
                    flash(mensaje_resumen, 'success')

                # Mostrar errores (máximo 10)
                if filas_fallidas:
                    errores_mostrar = filas_fallidas[:10]
                    for error in errores_mostrar:
                        flash(error, 'danger')
                    if len(filas_fallidas) > 10:
                        flash(f'... y {len(filas_fallidas) - 10} error(es) adicional(es)', 'info')

                current_app.logger.info(f"[Funcionarios CSV] Completado: {funcionarios_creados} creados, {funcionarios_actualizados} actualizados, {len(filas_fallidas)} fallos")

                return redirect(url_for('funcionarios.ver_funcionarios'))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"[Funcionarios CSV] Error en commit: {e}")
                flash(f'Error al guardar los datos: {str(e)}', 'danger')
                return redirect(url_for('funcionarios.importar_csv'))

        except Exception as e:
            current_app.logger.error(f"[Funcionarios CSV] Error general: {e}")
            flash(f'Error al procesar el archivo CSV: {str(e)}', 'danger')
            return redirect(url_for('funcionarios.importar_csv'))

    # GET - Mostrar formulario de importación
    return render_template('importar_funcionarios.html', active_page='funcionarios')


@funcionarios_bp.route('/api/buscar-con-activos')
@login_required
def buscar_funcionarios_con_activos():
    """
    API endpoint para buscar funcionarios y obtener sus activos asignados.
    Usado en el wizard de Paz y Salvo para autocompletado inteligente.

    Query params:
        - term: Término de búsqueda (nombre o cédula)

    Returns:
        JSON con lista de funcionarios y sus activos asignados
    """
    term = request.args.get('term', '').strip()

    if len(term) < 2:
        return jsonify([])

    search_term = f'%{term}%'

    # Buscar funcionarios por nombre o cédula
    stmt = select(Funcionario).where(
        or_(
            Funcionario.nombres.ilike(search_term),
            Funcionario.apellidos.ilike(search_term),
            Funcionario.cedula.ilike(search_term)
        )
    ).limit(10)

    funcionarios = db.session.execute(stmt).scalars().all()

    # Construir respuesta con activos asignados
    resultados = []
    for func in funcionarios:
        # Obtener activos asignados a este funcionario
        activos_asignados = db.session.scalars(
            select(Activo).where(Activo.funcionario_id == func.id)
        ).all()

        activos_data = []
        for activo in activos_asignados:
            activos_data.append({
                'id': activo.id,
                'nombre_activo': activo.nombre_activo,
                'placa_codigo_interno': activo.placa_codigo_interno,
                'marca': activo.marca or '',
                'modelo': activo.modelo or '',
                'serie': activo.serie or ''
            })

        resultados.append({
            'id': func.id,
            'nombres': func.nombres,
            'apellidos': func.apellidos,
            'nombre_completo': f"{func.nombres} {func.apellidos}",
            'cedula': func.cedula or '',
            'cargo': func.cargo or '',
            'area': func.area or '',
            'centro_costo': func.centro_costo or '',
            'activos_count': len(activos_data),
            'activos': activos_data
        })

    return jsonify(resultados)


@funcionarios_bp.route('/api/lista')
@login_required
def api_lista_funcionarios():
    """
    Endpoint API para obtener lista simple de funcionarios para el wizard.
    Retorna JSON con id, nombres, apellidos y cédula.
    """
    from flask import jsonify

    funcionarios = db.session.scalars(
        select(Funcionario)
        .where(Funcionario.estado == 'Activo')
        .order_by(Funcionario.apellidos, Funcionario.nombres)
    ).all()

    return jsonify([
        {
            'id': f.id,
            'nombres': f.nombres,
            'apellidos': f.apellidos,
            'cedula': f.cedula or '',
            'cargo': f.cargo or ''
        }
        for f in funcionarios
    ])


@funcionarios_bp.route('/api/search')
@login_required
def api_search_funcionarios():
    """
    Endpoint API para búsqueda rápida de funcionarios por cédula o nombre.
    Usado en el formulario de edición de activos.

    Query params:
        - q: Término de búsqueda (mínimo 2 caracteres)

    Returns:
        JSON con lista de funcionarios que coinciden con la búsqueda
    """
    from flask import jsonify

    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    search_term = f'%{query}%'

    funcionarios = db.session.scalars(
        select(Funcionario)
        .where(
            or_(
                Funcionario.nombres.ilike(search_term),
                Funcionario.apellidos.ilike(search_term),
                Funcionario.cedula.ilike(search_term)
            )
        )
        .where(Funcionario.estado == 'Activo')
        .order_by(Funcionario.apellidos, Funcionario.nombres)
        .limit(15)
    ).all()

    return jsonify([
        {
            'id': f.id,
            'nombres': f.nombres,
            'apellidos': f.apellidos,
            'cedula': f.cedula or '',
            'cargo': f.cargo or ''
        }
        for f in funcionarios
    ])
