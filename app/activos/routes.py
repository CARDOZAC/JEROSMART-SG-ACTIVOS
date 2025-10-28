import os
import json
import sqlite3
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app
)
from werkzeug.utils import secure_filename
from sqlalchemy import select, func, and_, or_, exc
from ..extensions import db
from ..models import (
    Activo, ClaseActivo, Funcionario, MovimientoActivo, Mantenimiento,
    HojasDeVida
)
from ..decorators import login_required, role_required

activos_bp = Blueprint(
    'activos',
    __name__,
    template_folder='templates',
)

ATRIBUTOS_POR_CLASE = {
    '1': [
        {'name': 'registro_invima', 'label': 'Registro Invima', 'type': 'text', 'required': False},
        {'name': 'clasificacion_riesgo', 'label': 'Clasificación de Riesgo', 'type': 'select',
         'options': ['I', 'IIa', 'IIb', 'III'], 'required': False},
        {'name': 'vida_util', 'label': 'Vida Útil (años)', 'type': 'number', 'required': False},
        {'name': 'ultimo_mantenimiento', 'label': 'Último Mantenimiento', 'type': 'date', 'required': False}
    ],
    '2': [
        {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones Técnicas (Electr.)', 'type': 'textarea', 'required': False}
    ],
    '3': [
        {'name': 'procesador', 'label': 'Procesador', 'type': 'text', 'required': False},
        {'name': 'disco_duro', 'label': 'Disco Duro', 'type': 'text', 'required': False},
        {'name': 'ram', 'label': 'RAM', 'type': 'text', 'required': False},
        {'name': 'sistema_operativo', 'label': 'Sistema Operativo', 'type': 'text', 'required': False},
        {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones Técnicas (TICs)', 'type': 'textarea', 'required': False}
    ],
    '4': [
        {'name': 'tipo_adquisicion', 'label': 'Tipo de Adquisición', 'type': 'select',
         'options': ['Compra', 'Donación', 'Comodato'], 'required': False},
        {'name': 'fecha_ingreso', 'label': 'Fecha de Ingreso', 'type': 'date', 'required': False},
        {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones (Material, Dimensiones, etc.)', 'type': 'textarea', 'required': False}
    ]
}

def _save_file(file_storage, folder_key, placa_codigo, prefix):
    """
    Función auxiliar para guardar un archivo de forma segura.
    Retorna la ruta relativa del archivo guardado o None.
    """
    if file_storage and file_storage.filename:
        folder_path = current_app.config[folder_key]
        filename = secure_filename(f"{prefix}_{placa_codigo}_{file_storage.filename}")
        filepath = os.path.join(folder_path, filename)
        file_storage.save(filepath)
        # Retorna la ruta relativa para ser guardada en la BD
        return os.path.join(folder_path.name, filename)
    return None

@activos_bp.route('/')
@login_required
def ver_activos():
    filtros = {
        'q': request.args.get('q', '').strip(),
        'tipo': request.args.get('filtro_tipo', ''),
        'clase': request.args.get('filtro_clase', ''),
        'estado': request.args.get('filtro_estado', '')
    }

    stmt = (
        select(Activo, ClaseActivo.nombre_clase, func.concat(Funcionario.nombres, ' ', Funcionario.apellidos).label('funcionario_responsable'))
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
        .outerjoin(Funcionario, Activo.funcionario_id == Funcionario.id)
    )

    conditions = []
    if filtros['q']:
        search_term = f"%{filtros['q']}%"
        conditions.append(or_(
            Activo.nombre_activo.ilike(search_term),
            Activo.placa_codigo_interno.ilike(search_term),
            Activo.serie.ilike(search_term)
        ))
    if filtros['tipo']:
        conditions.append(Activo.tipo_propiedad == filtros['tipo'])
    if filtros['clase']:
        conditions.append(Activo.clase_id == filtros['clase'])
    if filtros['estado']:
        conditions.append(Activo.estado == filtros['estado'])
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Activo.nombre_activo)
    
    result = db.session.execute(stmt).all()
    activos = []
    # Procesamos el resultado para "enriquecer" cada objeto Activo con los datos
    # de las tablas unidas, facilitando su uso en la plantilla.
    for row in result:
        activo, nombre_clase, funcionario_responsable = row
        activo.nombre_clase = nombre_clase
        activo.funcionario_responsable = funcionario_responsable
        activos.append(activo)

    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    estados_activos = db.session.scalars(select(Activo.estado).distinct().where(Activo.estado.isnot(None) & (Activo.estado != '')).order_by(Activo.estado)).all()

    return render_template(
        'ver_activos.html',
        activos=activos,
        clases=clases,
        estados_activos=estados_activos,
        filtros=filtros
    )

@activos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_activo():
    if request.method == 'POST':
        try:
            tipo_propiedad = request.form.get('tipo_propiedad')
            nombre_activo = request.form.get('nombre_activo')
            placa_codigo = request.form.get('placa_codigo_interno')

            if not tipo_propiedad or not nombre_activo or not placa_codigo:
                flash('Nombre, Placa y Tipo de Propiedad son campos obligatorios.', 'danger')
                return redirect(url_for('activos.add_activo'))
                
            # Usamos la función auxiliar para guardar archivos
            ruta_contrato_arriendo = _save_file(request.files.get('contrato_arriendo'), 'LOAN_CONTRACT_FOLDER', placa_codigo, 'contrato')
            ruta_orden_compra = _save_file(request.files.get('orden_compra'), 'PURCHASE_ORDER_FOLDER', placa_codigo, 'oc')
            ruta_factura = _save_file(request.files.get('factura'), 'INVOICE_FOLDER', placa_codigo, 'factura')

            nuevo_activo = Activo(
                nombre_activo=nombre_activo,
                placa_codigo_interno=placa_codigo,
                marca=request.form.get('marca'),
                modelo=request.form.get('modelo'),
                serie=request.form.get('serie'),
                ubicacion=request.form.get('ubicacion'),
                estado=request.form.get('estado') or 'Operativo',
                observaciones=request.form.get('observaciones'),
                tipo_propiedad=tipo_propiedad,
                ruta_orden_compra=ruta_orden_compra,
                ruta_factura=ruta_factura,
                ruta_contrato_arriendo=ruta_contrato_arriendo
            )
            
            if tipo_propiedad == 'Propio':
                valor_comercial_str = request.form.get('valor_comercial')
                try:
                    nuevo_activo.valor_comercial = float(valor_comercial_str) if valor_comercial_str else None
                except (ValueError, TypeError):
                    flash('El valor comercial debe ser un número válido.', 'danger')
                    return redirect(url_for('activos.add_activo'))
                
                nuevo_activo.origen_adquisicion = request.form.get('origen_adquisicion')
                clase_id_str = request.form.get('clase_id')
                nuevo_activo.clase_id = int(clase_id_str) if clase_id_str and clase_id_str.isdigit() else None
                funcionario_id_str = request.form.get('funcionario_id')
                nuevo_activo.funcionario_id = int(funcionario_id_str) if funcionario_id_str and funcionario_id_str.isdigit() else None

                atributos_dinamicos_guardar = {}
                if nuevo_activo.clase_id and str(nuevo_activo.clase_id) in ATRIBUTOS_POR_CLASE:
                    for attr_spec in ATRIBUTOS_POR_CLASE[str(nuevo_activo.clase_id)]:
                        attr_name = attr_spec['name']
                        val = request.form.get(attr_name)
                        atributos_dinamicos_guardar[attr_name] = val
                
                nuevo_activo.atributos_dinamicos_json = json.dumps(atributos_dinamicos_guardar)

            elif tipo_propiedad == 'Ajeno':
                nuevo_activo.propietario_ajeno = request.form.get('propietario_ajeno')
                nuevo_activo.condicion_tenencia = request.form.get('condicion_tenencia')
            
            db.session.add(nuevo_activo)
            db.session.commit()
            flash('Activo agregado exitosamente.', 'success')
            return redirect(url_for('activos.ver_activos'))
        
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f"Fallo de integridad al agregar activo (placa duplicada?): {placa_codigo}")
            flash('Error de base de datos: La placa o código interno ya existe.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al agregar activo: {e}")
        return redirect(url_for('activos.add_activo'))

    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    
    return render_template(
        'add_activo.html',
        clases=clases,
        active_page='add_activo',
        atributos_por_clase_json=json.dumps(ATRIBUTOS_POR_CLASE)
    )
    
@activos_bp.route('/editar/<int:activo_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_activo(activo_id):
    activo = db.session.get(Activo, activo_id)
    if not activo:
        flash('Activo no encontrado.', 'danger')
        return redirect(url_for('activos.ver_activos'))
    
    if request.method == 'POST':
        try:
            data = request.form
            # Actualizar campos básicos
            activo.nombre_activo = data.get('nombre_activo')
            activo.placa_codigo_interno = data.get('placa_codigo_interno')
            activo.marca = data.get('marca')
            activo.modelo = data.get('modelo')
            activo.serie = data.get('serie')
            activo.ubicacion = data.get('ubicacion')
            activo.estado = data.get('estado')
            activo.observaciones = data.get('observaciones')

            # Actualizar campos dependientes del tipo
            if activo.tipo_propiedad == 'Propio':
                activo.valor_comercial = float(data.get('valor_comercial')) if data.get('valor_comercial') else None
                activo.origen_adquisicion = data.get('origen_adquisicion')
                activo.clase_id = int(data.get('clase_id')) if data.get('clase_id') else None
                activo.funcionario_id = int(data.get('funcionario_id')) if data.get('funcionario_id') else None
                
                atributos_dinamicos = {}
                if activo.clase_id and str(activo.clase_id) in ATRIBUTOS_POR_CLASE:
                    for attr_spec in ATRIBUTOS_POR_CLASE[str(activo.clase_id)]:
                        attr_name = attr_spec['name']
                        atributos_dinamicos[attr_name] = data.get(attr_name)
                activo.atributos_dinamicos_json = json.dumps(atributos_dinamicos)

            elif activo.tipo_propiedad == 'Ajeno':
                activo.propietario_ajeno = data.get('propietario_ajeno')
                activo.condicion_tenencia = data.get('condicion_tenencia')

            # Lógica para actualizar archivos (borrar el antiguo si se sube uno nuevo)
            for file_key, folder_key, prefix, attr_name in [
                ('contrato_arriendo', 'LOAN_CONTRACT_FOLDER', 'contrato', 'ruta_contrato_arriendo'),
                ('orden_compra', 'PURCHASE_ORDER_FOLDER', 'oc', 'ruta_orden_compra'),
                ('factura', 'INVOICE_FOLDER', 'factura', 'ruta_factura')
            ]:
                new_file = request.files.get(file_key)
                if new_file and new_file.filename:
                    # Borrar archivo antiguo si existe
                    old_path = getattr(activo, attr_name)
                    if old_path:
                        try:
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], old_path))
                        except OSError:
                            current_app.logger.warning(f"No se pudo borrar el archivo antiguo: {old_path}")
                    # Guardar archivo nuevo
                    setattr(activo, attr_name, _save_file(new_file, folder_key, activo.placa_codigo_interno, prefix))

            db.session.commit()
            flash('Activo actualizado exitosamente.', 'success')
            return redirect(url_for('activos.edit_activo', activo_id=activo_id))

        except exc.IntegrityError:
            db.session.rollback()
            flash('Error de base de datos: La placa o código interno ya existe para otro activo.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error inesperado al actualizar el activo: {e}', 'danger')
        return redirect(url_for('activos.edit_activo', activo_id=activo_id))
    
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    datos_activo_para_frontend = activo.__dict__
    if activo.atributos_dinamicos_json:
        try:
            dinamicos = json.loads(activo.atributos_dinamicos_json)
            datos_activo_para_frontend.update(dinamicos)
        except (json.JSONDecodeError, TypeError):
            flash("Advertencia: No se pudieron cargar los atributos dinámicos del activo.", "warning")

    return render_template(
        'edit_activo.html',
        activo=activo,
        clases=clases,
        atributos_por_clase_json=json.dumps(ATRIBUTOS_POR_CLASE),
        datos_activo_json=json.dumps(datos_activo_para_frontend)
    )

@activos_bp.route('/eliminar/<int:activo_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_activo(activo_id):
    try:
        # Validaciones para evitar borrados que rompan la integridad referencial
        movimientos_asociados = db.session.execute(select(MovimientoActivo).where(MovimientoActivo.activo_id == activo_id)).first()
        if movimientos_asociados:
            flash('No se puede eliminar el activo porque está asociado a uno o más movimientos.', 'danger')
            return redirect(url_for('activos.ver_activos'))
        
        mantenimientos_asociados = db.session.execute(select(Mantenimiento).where(Mantenimiento.activo_id == activo_id)).first()
        if mantenimientos_asociados:
            flash('No se puede eliminar el activo porque tiene mantenimientos registrados.', 'danger')
            return redirect(url_for('activos.ver_activos'))
            
        hoja_vida_asociada = db.session.execute(select(HojasDeVida).where(HojasDeVida.activo_id == activo_id)).first()
        if hoja_vida_asociada:
            flash('No se puede eliminar el activo porque tiene una hoja de vida asociada.', 'danger')
            return redirect(url_for('activos.ver_activos'))
            
        activo = db.session.get(Activo, activo_id)
        if activo:
            # Borrar archivos asociados del sistema de archivos antes de eliminar el registro
            for attr_name in ['ruta_orden_compra', 'ruta_factura', 'ruta_contrato_arriendo']:
                file_path = getattr(activo, attr_name)
                if file_path:
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
                    try:
                        os.remove(full_path)
                        current_app.logger.info(f"Archivo eliminado: {full_path}")
                    except OSError as e:
                        current_app.logger.warning(f"No se pudo borrar el archivo {full_path}: {e}")
            
            db.session.delete(activo)
            db.session.commit()
            flash('Activo y sus archivos asociados han sido eliminados exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el activo: {e}', 'danger')
    return redirect(url_for('activos.ver_activos'))

@activos_bp.route('/api/clase_atributos/<int:clase_id>')
@login_required
def get_clase_atributos(clase_id):
    return jsonify(ATRIBUTOS_POR_CLASE.get(str(clase_id), []))
