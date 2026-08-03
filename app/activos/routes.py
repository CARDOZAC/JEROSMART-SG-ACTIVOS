import os
import json
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app
)
from werkzeug.utils import secure_filename
from sqlalchemy import select, func, and_, or_, exc
from ..extensions import db
from ..models import (
    Activo, ClaseActivo, Funcionario, Movimiento, MovimientoActivo,
    Mantenimiento, HojaVidaBiomedico, AuditoriaActivo
)
from ..decorators import login_required, role_required

activos_bp = Blueprint(
    'activos',
    __name__,
    template_folder='templates',
)

# Definición de atributos dinámicos por clase de activo.
# FUENTE ÚNICA: app/activos_v2/atributos_dinamicos.py
# Antes este diccionario estaba duplicado aquí y, en una tercera versión más
# pobre, en app/config.py. Según qué módulo validara, un mismo activo pasaba o
# no la validación.
from app.activos_v2.atributos_dinamicos import ATRIBUTOS_POR_CLASE

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _save_file(file_storage, folder_key, placa_codigo, prefix):
    """
    Función auxiliar para guardar un archivo de forma segura.
    Retorna la ruta relativa del archivo guardado o None.
    Incluye validación de tipo y tamaño de archivo.
    
    Asume que current_app.config['UPLOAD_FOLDER'] es el directorio base de subida
    y current_app.config[folder_key] es el nombre de la subcarpeta relativa (ej. 'loan_contracts').
    """
    if file_storage and file_storage.filename:
        # Validar extensión de archivo
        if not allowed_file(file_storage.filename):
            raise ValueError(f"Tipo de archivo no permitido: {file_storage.filename}. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}")
        # Validar tamaño de archivo
        file_storage.seek(0, os.SEEK_END)
        file_length = file_storage.tell()
        if file_length > MAX_FILE_SIZE:
            raise ValueError(f"El archivo es demasiado grande (máximo {MAX_FILE_SIZE // (1024*1024)}MB)")
        file_storage.seek(0)
        
        # OJO: current_app.config[folder_key] es una ruta ABSOLUTA
        # (C:\...\uploads\loan_contracts), no un nombre de subcarpeta. Antes se
        # pasaba tal cual a os.path.join, que descarta el primer argumento
        # cuando el segundo es absoluto, y en la BD terminaba guardándose la
        # ruta absoluta completa: al mover el proyecto o desplegar en Linux,
        # todos los enlaces a facturas y contratos quedaban rotos.
        # Aquí se deriva el nombre de la subcarpeta y se guarda la ruta
        # RELATIVA, con separadores '/' para que sea portable.
        upload_base_dir = current_app.config['UPLOAD_FOLDER']
        subfolder_name = os.path.basename(os.path.normpath(current_app.config[folder_key]))
        target_full_dir = os.path.join(upload_base_dir, subfolder_name)
        os.makedirs(target_full_dir, exist_ok=True) # Asegurar que el directorio exista

        filename = secure_filename(f"{prefix}_{placa_codigo}_{file_storage.filename}")
        filepath = os.path.join(target_full_dir, filename)
        file_storage.save(filepath)
        # Ruta relativa a UPLOAD_FOLDER, que es lo que se almacena en la BD
        return f"{subfolder_name}/{filename}"
    return None

@activos_bp.route('/')
@login_required
def ver_activos():
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Limitar per_page para evitar consultas muy grandes
    per_page = min(per_page, 200)

    filtros = {
        'q': request.args.get('q', '').strip(),
        'tipo': request.args.get('filtro_tipo', ''),
        'clase': request.args.get('filtro_clase', ''),
        'estado': request.args.get('filtro_estado', ''),
        'ubicacion': request.args.get('filtro_ubicacion', '')
    }

    stmt = (
        select(Activo, ClaseActivo.nombre_clase, (Funcionario.nombres + ' ' + Funcionario.apellidos).label('funcionario_responsable'))
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
    if filtros['ubicacion']:
        conditions.append(Activo.ubicacion == filtros['ubicacion'])
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Activo.nombre_activo)

    # Obtener total de registros para paginación
    count_stmt = select(func.count()).select_from(Activo)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_records = db.session.scalar(count_stmt)

    # Aplicar paginación
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = db.session.execute(stmt).all()
    activos = []
    # Procesamos el resultado para "enriquecer" cada objeto Activo con los datos
    # de las tablas unidas, facilitando su uso en la plantilla.
    for row in result:
        activo, nombre_clase, funcionario_responsable = row
        activo.nombre_clase = nombre_clase
        activo.funcionario_responsable = funcionario_responsable

        # Normalizar valor_comercial: asegurar que nunca sea None
        if activo.valor_comercial is None:
            activo.valor_comercial = 0.0

        activos.append(activo)

    # Calcular información de paginación
    total_pages = (total_records + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    estados_activos = db.session.scalars(select(Activo.estado).distinct().where(Activo.estado.isnot(None) & (Activo.estado != '')).order_by(Activo.estado)).all()

    return render_template(
        'ver_activos.html',
        activos=activos,
        clases=clases,
        estados_activos=estados_activos,
        filtros=filtros,
        page=page,
        per_page=per_page,
        total_records=total_records,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next
    )

def validar_atributos_dinamicos(clase_id, atributos_data):
    """
    Valida que los atributos dinámicos cumplan con los requisitos de la clase de activo.
    Incluye validación de presencia, tipo y valores permitidos.
    Retorna (es_valido, errores_dict)
    """
    clase_id_str = str(clase_id)
    if clase_id_str not in ATRIBUTOS_POR_CLASE:
        return True, {}

    errores = {}
    atributos_spec = ATRIBUTOS_POR_CLASE[clase_id_str]

    for attr_spec in atributos_spec:
        attr_name = attr_spec['name']
        attr_label = attr_spec['label']
        es_requerido = attr_spec.get('required', False)
        valor = atributos_data.get(attr_name)

        # 1. Validar campos requeridos
        if es_requerido and not valor:
            errores[attr_name] = f"'{attr_label}' es un campo obligatorio."
            continue # No seguir validando si está vacío y es requerido

        # 2. Validaciones específicas por tipo si el valor existe
        if valor:
            # Validación para Equipo Biomédico (clase_id = 1)
            if clase_id_str == '1':
                if attr_name == 'clasificacion_riesgo' and valor not in ['I', 'IIa', 'IIb', 'III']:
                    errores[attr_name] = f"'{attr_label}' debe ser I, IIa, IIb o III."

                if attr_name == 'vida_util':
                    try:
                        vida_util_num = int(valor)
                        if vida_util_num <= 0:
                            errores[attr_name] = f"'{attr_label}' debe ser un número positivo."
                    except (ValueError, TypeError):
                        errores[attr_name] = f"'{attr_label}' debe ser un número entero."

            # Validación para Electroindustrial (clase_id = 2)
            elif clase_id_str == '2':
                import re
                # Validar formato de voltaje (ej: 220V AC, 110V, 12V DC)
                if attr_name == 'voltaje_nominal':
                    if not re.match(r'^\d+V(\s*(AC|DC))?$', valor.strip(), re.IGNORECASE):
                        errores[attr_name] = f"'{attr_label}' debe tener formato válido (ej: 220V AC, 110V DC)."

                # Validar corriente nominal (debe ser número positivo)
                if attr_name == 'corriente_nominal' and valor.strip():
                    try:
                        corriente = float(valor)
                        if corriente <= 0:
                            errores[attr_name] = f"'{attr_label}' debe ser un número positivo."
                    except (ValueError, TypeError):
                        errores[attr_name] = f"'{attr_label}' debe ser un número válido."

                # Validar cumplimiento RETIE
                if attr_name == 'cumple_retie' and valor not in ['Sí', 'No', 'No Aplica']:
                    errores[attr_name] = f"'{attr_label}' debe ser 'Sí', 'No' o 'No Aplica'."

            # Validación para TICs (clase_id = 3)
            elif clase_id_str == '3':
                import re
                if attr_name == 'vida_util_estimada' and valor not in ['3', '5', '7', '10']:
                    errores[attr_name] = f"'{attr_label}' debe ser 3, 5, 7 o 10 años."

                # Validar formato de dirección IP
                if attr_name == 'direccion_ip' and valor.strip():
                    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', valor.strip()):
                        errores[attr_name] = f"'{attr_label}' debe tener formato válido (ej: 192.168.1.100)."

                # Validar formato de dirección MAC
                if attr_name == 'direccion_mac' and valor.strip():
                    if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', valor.strip()):
                        errores[attr_name] = f"'{attr_label}' debe tener formato válido (ej: 00:1A:2B:3C:4D:5E)."

            # Validación para Muebles y Enseres (clase_id = 4)
            elif clase_id_str == '4':
                if attr_name == 'estado_fisico' and valor not in ['Excelente', 'Bueno', 'Regular', 'Malo']:
                    errores[attr_name] = f"'{attr_label}' debe ser Excelente, Bueno, Regular o Malo."

    return len(errores) == 0, errores

@activos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_activo():
    """
    Crear nuevo activo (POST protegido con CSRF automático vía Flask-WTF).
    """
    # --- Lógica para procesar los datos del wizard ---
    if request.method == 'POST':
        try:
            tipo_propiedad = request.form.get('tipo_propiedad')
            nombre_activo = request.form.get('nombre_activo', '').strip()
            placa_codigo = request.form.get('placa_codigo_interno', '').strip()

            if not tipo_propiedad or not nombre_activo or not placa_codigo:
                flash('Nombre, Placa y Tipo de Propiedad son campos obligatorios.', 'danger')
                return redirect(url_for('activos.add_activo'))
                
            # Usamos la función auxiliar para guardar archivos
            ruta_contrato_arriendo = _save_file(request.files.get('contrato_arriendo'), 'LOAN_CONTRACT_FOLDER', placa_codigo, 'contrato')
            ruta_orden_compra = _save_file(request.files.get('orden_compra'), 'PURCHASE_ORDER_FOLDER', placa_codigo, 'oc')
            ruta_factura = _save_file(request.files.get('factura'), 'INVOICE_FOLDER', placa_codigo, 'factura')

            nuevo_activo = Activo(
                nombre_activo=nombre_activo, # noqa
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
                    nuevo_activo.valor_comercial = float(valor_comercial_str) if valor_comercial_str else 0.0
                except (ValueError, TypeError):
                    flash('El valor comercial debe ser un número válido.', 'danger')
                    return redirect(url_for('activos.add_activo'))

                # Validación de integridad: activos propios deben tener valor comercial > 0
                if nuevo_activo.valor_comercial <= 0:
                    flash('Los activos propios deben tener un valor comercial mayor a cero.', 'danger')
                    return redirect(url_for('activos.add_activo'))

                nuevo_activo.origen_adquisicion = request.form.get('origen_adquisicion')
                clase_id_str = request.form.get('clase_id')
                nuevo_activo.clase_id = int(clase_id_str) if clase_id_str and clase_id_str.isdigit() else None

                atributos_dinamicos_guardar = {}
                if nuevo_activo.clase_id and str(nuevo_activo.clase_id) in ATRIBUTOS_POR_CLASE:
                    for attr_spec in ATRIBUTOS_POR_CLASE[str(nuevo_activo.clase_id)]:
                        attr_name = attr_spec['name']
                        val = request.form.get(attr_name)
                        atributos_dinamicos_guardar[attr_name] = val

                    # Validar atributos dinámicos obligatorios
                    es_valido, errores = validar_atributos_dinamicos(nuevo_activo.clase_id, atributos_dinamicos_guardar)
                    if not es_valido:
                        errores_msg = '; '.join([f"{k}: {v}" for k, v in errores.items()])
                        flash(f'Faltan campos obligatorios: {errores_msg}', 'danger')
                        return redirect(url_for('activos.add_activo'))

                # SQLAlchemy maneja la serialización JSON automáticamente
                nuevo_activo.atributos_dinamicos_json = atributos_dinamicos_guardar

            elif tipo_propiedad == 'Ajeno':
                nuevo_activo.propietario_ajeno = request.form.get('propietario_ajeno')
                nuevo_activo.condicion_tenencia = request.form.get('condicion_tenencia')

                # Validación de integridad: activos ajenos deben tener propietario y condición
                if not nuevo_activo.propietario_ajeno or not nuevo_activo.propietario_ajeno.strip():
                    flash('Los activos ajenos deben tener un propietario especificado.', 'danger')
                    return redirect(url_for('activos.add_activo'))

                if not nuevo_activo.condicion_tenencia or not nuevo_activo.condicion_tenencia.strip():
                    flash('Los activos ajenos deben tener una condición de tenencia especificada.', 'danger')
                    return redirect(url_for('activos.add_activo'))

                # FASE 3: Sistema de Ingreso Temporal
                es_ingreso_temporal_str = request.form.get('es_ingreso_temporal', 'false')
                nuevo_activo.es_ingreso_temporal = es_ingreso_temporal_str.lower() == 'true'
                
                if nuevo_activo.es_ingreso_temporal:
                    from datetime import datetime
                    fecha_inicio_str = request.form.get('fecha_inicio_temporal')
                    if fecha_inicio_str:
                        try:
                            nuevo_activo.fecha_inicio_temporal = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
                        except ValueError:
                            flash(f"Formato de fecha de inicio inválido: {fecha_inicio_str}. Use YYYY-MM-DD.", 'danger')
                            return redirect(url_for('activos.add_activo'))
                    
                    fecha_fin_str = request.form.get('fecha_fin_temporal')
                    if fecha_fin_str:
                        try:
                            nuevo_activo.fecha_fin_temporal = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
                        except ValueError:
                            flash(f"Formato de fecha de fin inválido: {fecha_fin_str}. Use YYYY-MM-DD.", 'danger')
                            return redirect(url_for('activos.add_activo'))


            current_app.logger.debug(f"A punto de agregar activo: {placa_codigo}")
            db.session.add(nuevo_activo)
            current_app.logger.debug(f"A punto de hacer commit para activo: {placa_codigo}")
            db.session.commit()
            current_app.logger.debug(f"Commit exitoso para activo: {placa_codigo}")
            flash('Activo agregado exitosamente.', 'success')
            current_app.logger.debug(f"Flash message agregado, redirigiendo a ver_activos")
            redirect_url = url_for('activos.ver_activos')
            current_app.logger.debug(f"URL de redireccion: {redirect_url}")
            return redirect(redirect_url)
        
        except ValueError as e:
            # Errores de validación (archivos, formato de datos)
            flash(str(e), 'danger')
            current_app.logger.warning(f"ValueError al agregar activo: {e}")
            return redirect(url_for('activos.add_activo'))
        except TypeError as e:
            # Errores de conversión de tipos
            db.session.rollback()
            flash(f'Error en el formato de datos: {str(e)}', 'danger')
            current_app.logger.warning(f"TypeError al agregar activo: {e}")
            return redirect(url_for('activos.add_activo'))
        except exc.IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning(f"IntegrityError al agregar activo (placa duplicada?): {placa_codigo} - {e}")
            flash('Error de base de datos: La placa o código interno ya existe.', 'danger')
            return redirect(url_for('activos.add_activo'))
        except exc.SQLAlchemyError as e:
            # Otros errores de base de datos
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos al agregar activo: {e}")
            flash('Error de base de datos al guardar el activo. Intente nuevamente.', 'danger')
            return redirect(url_for('activos.add_activo'))
        except (OSError, IOError) as e:
            # Errores de operaciones de archivos
            db.session.rollback()
            flash(f'Error al procesar archivos adjuntos: {str(e)}', 'danger')
            current_app.logger.error(f"Error de archivo al agregar activo: {e}")
            return redirect(url_for('activos.add_activo'))
        except Exception as e:
            # Captura de último recurso para errores inesperados
            db.session.rollback()
            import traceback
            current_app.logger.error(f"Error inesperado al agregar activo: {type(e).__name__} - {e}")
            current_app.logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            flash(f'Error inesperado al procesar el formulario. Contacte al administrador.', 'danger')
            return redirect(url_for('activos.add_activo'))

    # --- Lógica para mostrar el wizard de creación ---
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()

    # Datos vacíos para un activo nuevo
    datos_activo = {}

    return render_template(
        'add_activo.html', # Wizard rediseñado con UX/UI estilo iOS
        clases=clases,
        atributos_por_clase_json=json.dumps(ATRIBUTOS_POR_CLASE), # Estandarizar nombre de variable
        datos_activo=datos_activo  # Para formulario nuevo (vacío)
    )
    
@activos_bp.route('/api/buscar-funcionarios')
@login_required
def buscar_funcionarios():
    """
    API endpoint para búsqueda dinámica de funcionarios (GET - solo lectura).
    No requiere protección CSRF ya que es una operación de solo lectura.

    Acepta parámetros:
    - 'q': texto de búsqueda por nombre, apellido o cédula
    - 'page': número de página (default: 1)
    - 'limit': resultados por página (default: 10, max: 50)
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # Limitar el límite máximo para prevenir sobrecarga
    limit = min(limit, 50)

    if len(query) < 2:
        return jsonify({'results': [], 'total': 0, 'page': page, 'has_more': False})

    # Búsqueda flexible: nombre, apellidos o cédula
    from ..models import Funcionario

    # Contar total de resultados
    count_stmt = select(func.count()).select_from(Funcionario).where(
        or_(
            Funcionario.nombres.ilike(f'%{query}%'),
            Funcionario.apellidos.ilike(f'%{query}%'),
            Funcionario.cedula.ilike(f'%{query}%')
        )
    )
    total = db.session.scalar(count_stmt)

    # Consulta con paginación
    offset = (page - 1) * limit
    stmt = select(
        Funcionario.id,
        Funcionario.nombres,
        Funcionario.apellidos,
        Funcionario.cedula,
        Funcionario.cargo
    ).where(
        or_(
            Funcionario.nombres.ilike(f'%{query}%'),
            Funcionario.apellidos.ilike(f'%{query}%'),
            Funcionario.cedula.ilike(f'%{query}%')
        )
    ).order_by(Funcionario.nombres, Funcionario.apellidos).offset(offset).limit(limit)

    funcionarios = db.session.execute(stmt).all()

    # Formatear resultados
    resultados = [
        {
            'id': f.id,
            'nombre_completo': f'{f.nombres or ""} {f.apellidos or ""}'.strip(),
            'cedula': f.cedula,
            'cargo': f.cargo or 'Sin cargo'
        }
        for f in funcionarios
    ]

    has_more = (page * limit) < total

    return jsonify({
        'results': resultados,
        'total': total,
        'page': page,
        'has_more': has_more
    })

@activos_bp.route('/editar/<int:activo_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_activo(activo_id):
    """
    Editar activo existente (POST protegido con CSRF automático vía Flask-WTF).
    """
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
            tipo_propiedad = activo.tipo_propiedad

            if tipo_propiedad == 'Propio':
                valor_comercial_str = data.get('valor_comercial')
                try:
                    activo.valor_comercial = float(valor_comercial_str) if valor_comercial_str else 0.0
                except (ValueError, TypeError):
                    flash('El valor comercial debe ser un número válido.', 'danger')
                    return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                # Validación de integridad: activos propios deben tener valor comercial > 0
                if activo.valor_comercial <= 0:
                    flash('Los activos propios deben tener un valor comercial mayor a cero.', 'danger')
                    return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                activo.origen_adquisicion = data.get('origen_adquisicion')
                activo.clase_id = int(data.get('clase_id')) if data.get('clase_id') else None

            elif tipo_propiedad == 'Ajeno':
                activo.propietario_ajeno = data.get('propietario_ajeno')
                activo.condicion_tenencia = data.get('condicion_tenencia')

                # Validación de integridad: activos ajenos deben tener propietario y condición
                if not activo.propietario_ajeno or not activo.propietario_ajeno.strip():
                    flash('Los activos ajenos deben tener un propietario especificado.', 'danger')
                    return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                if not activo.condicion_tenencia or not activo.condicion_tenencia.strip():
                    flash('Los activos ajenos deben tener una condición de tenencia especificada.', 'danger')
                    return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                # FASE 3: Sistema de Ingreso Temporal
                es_ingreso_temporal_str = data.get('es_ingreso_temporal', 'false')
                activo.es_ingreso_temporal = es_ingreso_temporal_str.lower() == 'true'

                if activo.es_ingreso_temporal:
                    from datetime import datetime
                    fecha_inicio_str = data.get('fecha_inicio_temporal')
                    try:
                        activo.fecha_inicio_temporal = datetime.strptime(fecha_inicio_str, '%Y-%m-%d') if fecha_inicio_str else None
                    except (ValueError, TypeError):
                        activo.fecha_inicio_temporal = None # Clear on format error

                    fecha_fin_str = data.get('fecha_fin_temporal')
                    try:
                        activo.fecha_fin_temporal = datetime.strptime(fecha_fin_str, '%Y-%m-%d') if fecha_fin_str else None
                    except (ValueError, TypeError):
                        activo.fecha_fin_temporal = None # Clear on format error
                else:
                    # Clear dates if it's not a temporary admission
                    activo.es_ingreso_temporal = False
                    activo.fecha_inicio_temporal = None
                    activo.fecha_fin_temporal = None

                # --- DATOS DEL CONTRATO DEL ACTIVO AJENO ---
                from datetime import datetime as _dt

                for field in ['nit_propietario', 'telefono_propietario', 'email_propietario',
                              'numero_contrato', 'observaciones_contrato']:
                    setattr(activo, field, (data.get(field) or '').strip() or None)

                # Las fechas de contrato son columnas Date: hay que convertirlas,
                # no asignar el string crudo del formulario.
                for field in ['fecha_inicio_contrato', 'fecha_fin_contrato']:
                    valor_str = (data.get(field) or '').strip()
                    if not valor_str:
                        setattr(activo, field, None)
                        continue
                    try:
                        setattr(activo, field, _dt.strptime(valor_str, '%Y-%m-%d').date())
                    except ValueError:
                        flash(f"Formato de fecha inválido en '{field}': {valor_str}. Use YYYY-MM-DD.", 'danger')
                        return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                if (activo.fecha_inicio_contrato and activo.fecha_fin_contrato
                        and activo.fecha_fin_contrato < activo.fecha_inicio_contrato):
                    flash('La fecha de fin del contrato no puede ser anterior a la de inicio.', 'danger')
                    return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                costo_mensual_str = (data.get('costo_mensual') or '').strip()
                if costo_mensual_str:
                    try:
                        activo.costo_mensual = float(costo_mensual_str)
                    except ValueError:
                        flash('El costo mensual debe ser un número válido.', 'danger')
                        return redirect(url_for('activos.edit_activo', activo_id=activo_id))
                else:
                    activo.costo_mensual = None

            # --- ATRIBUTOS DINÁMICOS (APLICA A AMBOS TIPOS SI TIENEN CLASE) ---
            if activo.clase_id:
                atributos_dinamicos = {}
                clase_id_str = str(activo.clase_id)
                if clase_id_str in ATRIBUTOS_POR_CLASE:
                    for attr_spec in ATRIBUTOS_POR_CLASE[clase_id_str]:
                        attr_name = attr_spec['name']
                        atributos_dinamicos[attr_name] = data.get(attr_name)

                    # Validar atributos dinámicos obligatorios
                    es_valido, errores = validar_atributos_dinamicos(activo.clase_id, atributos_dinamicos)
                    if not es_valido:
                        errores_msg = '; '.join([f"{k}: {v}" for k, v in errores.items()])
                        flash(f'Faltan campos obligatorios: {errores_msg}', 'danger')
                        return redirect(url_for('activos.edit_activo', activo_id=activo_id))

                # SQLAlchemy maneja la serialización JSON automáticamente
                activo.atributos_dinamicos_json = atributos_dinamicos

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

        except ValueError as e:
            # Errores de validación (archivos, formato de datos)
            flash(str(e), 'danger')
            current_app.logger.warning(f"Error de validación al editar activo: {e}")
        except TypeError as e:
            # Errores de conversión de tipos
            db.session.rollback()
            flash(f'Error en el formato de datos: {str(e)}', 'danger')
            current_app.logger.warning(f"TypeError al editar activo: {e}")
        except exc.IntegrityError as e:
            db.session.rollback()
            flash('Error de base de datos: La placa o código interno ya existe para otro activo.', 'danger')
            current_app.logger.warning(f"IntegrityError al editar activo: {e}")
        except exc.SQLAlchemyError as e:
            # Otros errores de base de datos
            db.session.rollback()
            flash('Error de base de datos al actualizar el activo. Intente nuevamente.', 'danger')
            current_app.logger.error(f"Error de base de datos al editar activo: {e}")
        except (OSError, IOError) as e:
            # Errores de operaciones de archivos
            db.session.rollback()
            flash(f'Error al procesar archivos adjuntos: {str(e)}', 'danger')
            current_app.logger.error(f"Error de archivo al editar activo: {e}")
        except Exception as e:
            # Captura de último recurso para errores inesperados
            db.session.rollback()
            import traceback
            current_app.logger.error(f"Error inesperado al editar activo: {type(e).__name__} - {e}")
            current_app.logger.error(f"Traceback:\n{traceback.format_exc()}")
            flash(f'Error inesperado al actualizar el activo. Contacte al administrador.', 'danger')
        return redirect(url_for('activos.edit_activo', activo_id=activo_id))
    
    # --- Lógica para mostrar el wizard en modo edición ---
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()

    # Enriquecer el objeto 'activo' con sus atributos dinámicos para fácil acceso en el template
    if activo.atributos_dinamicos_json:
        try:
            # Verificar si es string o ya es dict
            if isinstance(activo.atributos_dinamicos_json, str):
                dinamicos = json.loads(activo.atributos_dinamicos_json)
            elif isinstance(activo.atributos_dinamicos_json, dict):
                dinamicos = activo.atributos_dinamicos_json
            else:
                dinamicos = {}

            # Solo agregar si hay datos
            if dinamicos:
                for key, value in dinamicos.items():
                    setattr(activo, key, value)
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            # Solo mostrar warning si realmente hay un error, no si está vacío
            if activo.atributos_dinamicos_json:
                current_app.logger.warning(f"Error al cargar atributos dinámicos: {e}")
                flash("Advertencia: No se pudieron cargar algunos atributos dinámicos del activo.", "warning")

    # Serializar los datos del activo para que el wizard de JS pueda leerlos fácilmente
    # Esto es útil si el wizard necesita una copia inicial de los datos.
    datos_activo_dict = {}
    for c in activo.__table__.columns:
        val = getattr(activo, c.name)
        if isinstance(val, (int, float, str, bool)):
            datos_activo_dict[c.name] = val
        elif val is not None:
            datos_activo_dict[c.name] = str(val)
        else:
            # Convertir None a string vacío para que React lo maneje correctamente
            datos_activo_dict[c.name] = ''

    # Añadir atributos dinámicos al diccionario
    if activo.atributos_dinamicos_json:
        try:
            if isinstance(activo.atributos_dinamicos_json, str):
                datos_activo_dict.update(json.loads(activo.atributos_dinamicos_json))
            elif isinstance(activo.atributos_dinamicos_json, dict):
                datos_activo_dict.update(activo.atributos_dinamicos_json)
        except (json.JSONDecodeError, TypeError):
            pass # El error ya se flashea arriba

    # Añadir nombre del funcionario responsable si existe
    if activo.funcionario:
        datos_activo_dict['funcionario_responsable'] = f"{activo.funcionario.nombres} {activo.funcionario.apellidos}"

    datos_activo_json = json.dumps(datos_activo_dict)

    return render_template(
        'add_activo.html', # Template unificado para edición y creación
        activo=activo,
        clases=clases,
        atributos_por_clase_json=json.dumps(ATRIBUTOS_POR_CLASE),
        modo_edicion=True, # Flag para que el wizard sepa que está en modo edición
        datos_activo_json=datos_activo_json # Datos para precargar el form
    )

@activos_bp.route('/eliminar/<int:activo_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_activo(activo_id):
    """
    Eliminar activo (POST protegido con CSRF automático vía Flask-WTF).
    Valida relaciones antes de permitir eliminación.
    """
    try:
        # VALIDACIÓN COMPLETA: Verificar TODAS las relaciones antes de eliminar
        # Esto previene pérdida de trazabilidad y auditoría
        checks = [
            (MovimientoActivo, "movimientos", MovimientoActivo.activo_id),
            (Mantenimiento, "mantenimientos", Mantenimiento.activo_id),
            (AuditoriaActivo, "auditorías", AuditoriaActivo.activo_id),
            (HojaVidaBiomedico, "hojas de vida", HojaVidaBiomedico.activo_id),
        ]

        for model, nombre, campo in checks:
            count = db.session.scalar(select(func.count()).select_from(model).where(campo == activo_id))
            if count > 0:
                flash(
                    f'No se puede eliminar el activo porque tiene {count} {nombre} asociado(s). '
                    f'Para activos con historial, use la función "Dar de Baja" en lugar de eliminar.',
                    'danger'
                )
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

@activos_bp.route('/api/clases')
@login_required
def get_clases():
    """
    API endpoint para obtener todas las clases de activos (GET - solo lectura).
    No requiere protección CSRF ya que es una operación de solo lectura.
    Usado por el wizard de React para popular el selector de clases.
    """
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    return jsonify([
        {
            'id': clase.id,
            'nombre_clase': clase.nombre_clase
        }
        for clase in clases
    ])

@activos_bp.route('/api/clase_atributos/<int:clase_id>')
def get_clase_atributos(clase_id):
    """
    API endpoint para obtener atributos dinámicos de una clase (GET - solo lectura).
    No requiere protección CSRF ya que es una operación de solo lectura.
    """
    return jsonify(ATRIBUTOS_POR_CLASE.get(str(clase_id), []))

@activos_bp.route('/detalle/<int:activo_id>')
@login_required
def detalle_activo(activo_id):
    """
    Vista detallada de activo con historial de movimientos y mantenimientos.
    Estilo iOS con modal slide-up.
    """
    activo = db.session.get(Activo, activo_id)
    if not activo:
        flash('Activo no encontrado.', 'danger')
        return redirect(url_for('activos.ver_activos'))

    # Obtener datos relacionados
    clase = db.session.get(ClaseActivo, activo.clase_id) if activo.clase_id else None
    funcionario = db.session.get(Funcionario, activo.funcionario_id) if activo.funcionario_id else None

    # Obtener historial de movimientos
    movimientos = db.session.scalars(
        select(MovimientoActivo)
        .where(MovimientoActivo.activo_id == activo_id)
        .join(Movimiento)
        .order_by(Movimiento.fecha.desc())
        .limit(10)
    ).all()

    # Obtener historial de mantenimientos
    mantenimientos = db.session.scalars(
        select(Mantenimiento)
        .where(Mantenimiento.activo_id == activo_id)
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
        .limit(10)
    ).all()

    # Obtener hoja de vida si existe
    hoja_vida = db.session.scalar(
        select(HojaVidaBiomedico).where(HojaVidaBiomedico.activo_id == activo_id)
    )

    # Parsear atributos dinámicos (la columna db.JSON ya entrega un dict;
    # se soporta string por compatibilidad con datos antiguos)
    atributos_dinamicos = {}
    if activo.atributos_dinamicos_json:
        if isinstance(activo.atributos_dinamicos_json, dict):
            atributos_dinamicos = activo.atributos_dinamicos_json
        elif isinstance(activo.atributos_dinamicos_json, str):
            try:
                atributos_dinamicos = json.loads(activo.atributos_dinamicos_json)
            except (json.JSONDecodeError, TypeError):
                pass

    return render_template(
        'detalle_activo.html',
        activo=activo,
        clase=clase,
        funcionario=funcionario,
        atributos_dinamicos=atributos_dinamicos,
        movimientos=movimientos,
        mantenimientos=mantenimientos,
        hoja_vida=hoja_vida,
        atributos_spec=ATRIBUTOS_POR_CLASE.get(str(activo.clase_id), []) if activo.clase_id else []
    )

# ============================================================================
# IMPORTACIÓN MASIVA DE ACTIVOS DESDE CSV
# ============================================================================

@activos_bp.route('/descargar-plantilla-csv')
@login_required
@role_required('Admin')
def descargar_plantilla_csv():
    """
    Endpoint para descargar la plantilla CSV de ejemplo para importación.
    Solo accesible para administradores.
    """
    from flask import send_file
    plantilla_path = os.path.join(current_app.root_path, 'static', 'templates', 'plantilla_importacion_activos.csv')

    if not os.path.exists(plantilla_path):
        flash('Plantilla CSV no encontrada. Contacte al administrador.', 'danger')
        return redirect(url_for('activos.ver_activos'))

    return send_file(
        plantilla_path,
        as_attachment=True,
        download_name='plantilla_importacion_activos.csv',
        mimetype='text/csv'
    )

@activos_bp.route('/importar-activos', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def importar_activos():
    """
    Vista para importación masiva de activos desde archivo CSV.

    El CSV debe tener las siguientes columnas (coincidiendo con la plantilla):
    - nombre_activo (obligatorio)
    - placa_codigo_interno (obligatorio)
    - marca
    - modelo
    - serie
    - ubicacion
    - estado (Operativo, En Mantenimiento, Dado de Baja, etc.)
    - tipo_propiedad (Propio/Ajeno - obligatorio)
    - valor_comercial (solo si tipo_propiedad=Propio)
    - origen_adquisicion (Compra, Donación, Comodato, etc.)
    - clase_id (ID de ClaseActivo - 1=Biomédico, 2=Electroindustrial, 3=TICs, 4=Muebles)
    - funcionario_cedula (cédula del funcionario responsable)
    - propietario_ajeno (nombre del propietario si tipo_propiedad=Ajeno)
    - condicion_tenencia (Comodato, Arriendo, etc. si tipo_propiedad=Ajeno)
    - observaciones

    Normativa aplicada:
    - NIC 16: Propiedades, Planta y Equipo
    - NIIF para PYMES Sección 17: Activos fijos
    - Circular Única Supersalud: Inventario de activos clínicos
    """
    import csv
    import io
    from datetime import datetime

    if request.method == 'POST':
        try:
            archivo_csv = request.files.get('archivo_csv')

            if not archivo_csv or archivo_csv.filename == '':
                flash('Por favor seleccione un archivo CSV.', 'warning')
                return redirect(url_for('activos.importar_activos'))

            # Validar extensión
            if not archivo_csv.filename.endswith('.csv'):
                flash('El archivo debe ser formato CSV (.csv)', 'danger')
                return redirect(url_for('activos.importar_activos'))

            # Leer el contenido del archivo con detección automática de codificación
            contenido_bytes = archivo_csv.stream.read()

            # Intentar decodificar con varias codificaciones comunes
            contenido_csv = None
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']

            for encoding in encodings:
                try:
                    contenido_csv = contenido_bytes.decode(encoding)
                    current_app.logger.info(f"[Import Activos] Archivo decodificado exitosamente con '{encoding}'")
                    break
                except UnicodeDecodeError:
                    continue

            if contenido_csv is None:
                flash('No se pudo leer el archivo CSV. Verifica que esté en un formato de texto válido.', 'danger')
                return redirect(url_for('activos.importar_activos'))

            # Detectar el delimitador automáticamente
            # Intentar detectar con csv.Sniffer
            delimitador = ','  # Por defecto
            try:
                muestra = contenido_csv[:1024]
                sniffer = csv.Sniffer()
                delimitador = sniffer.sniff(muestra).delimiter
                current_app.logger.info(f"Delimitador detectado automáticamente: {repr(delimitador)}")
            except Exception as e:
                # Si falla la detección automática, intentar con los delimitadores comunes
                primera_linea = contenido_csv.split('\n')[0] if contenido_csv else ''
                if ';' in primera_linea:
                    delimitador = ';'
                    current_app.logger.info("Delimitador detectado manualmente: ';'")
                elif ',' in primera_linea:
                    delimitador = ','
                    current_app.logger.info("Delimitador detectado manualmente: ','")
                elif '\t' in primera_linea:
                    delimitador = '\t'
                    current_app.logger.info("Delimitador detectado manualmente: '\\t'")
                else:
                    current_app.logger.warning(f"No se pudo detectar delimitador, usando coma por defecto. Error: {e}")

            stream = io.StringIO(contenido_csv, newline=None)
            csv_reader = csv.DictReader(stream, delimiter=delimitador)

            # Validar que existan las columnas obligatorias (solo lo básico)
            columnas_csv = csv_reader.fieldnames

            if not columnas_csv:
                flash('El archivo CSV está vacío o mal formateado.', 'danger')
                return redirect(url_for('activos.importar_activos'))

            # Limpiar espacios en blanco de los nombres de las columnas
            columnas_csv = [col.strip() if col else col for col in columnas_csv]

            # Mapeo de columnas alternativas (para compatibilidad)
            # Permite usar 'placa_codigo' en lugar de 'placa_codigo_interno'
            mapeo_columnas = {
                'placa_codigo': 'placa_codigo_interno'
            }

            # Log de las columnas detectadas (para debugging)
            current_app.logger.info(f"Columnas detectadas en CSV: {columnas_csv}")

            # Validar columnas obligatorias con soporte para nombres alternativos
            columnas_requeridas = ['nombre_activo', 'placa_codigo_interno']
            columnas_faltantes = []

            for col_requerida in columnas_requeridas:
                # Verificar si la columna está presente o si existe una alternativa
                columna_presente = col_requerida in columnas_csv
                alternativa_presente = any(
                    mapeo_columnas.get(col_csv) == col_requerida
                    for col_csv in columnas_csv
                )

                if not columna_presente and not alternativa_presente:
                    columnas_faltantes.append(col_requerida)

            if columnas_faltantes:
                flash(f'Columnas faltantes en el CSV: {", ".join(columnas_faltantes)}', 'danger')
                return redirect(url_for('activos.importar_activos'))

            # Procesar cada fila
            activos_creados = 0
            activos_omitidos = 0
            errores = []

            # Límite de filas para prevenir timeout en importaciones masivas
            MAX_FILAS_IMPORTACION = 1000
            fila_count = 0

            for idx, fila in enumerate(csv_reader, start=2):  # start=2 porque la fila 1 son los headers
                fila_count += 1

                # Verificar límite de filas
                if fila_count > MAX_FILAS_IMPORTACION:
                    errores.append(f"Límite de importación alcanzado: {MAX_FILAS_IMPORTACION} filas. Las filas restantes no fueron procesadas.")
                    flash(f'Advertencia: Se procesaron solo las primeras {MAX_FILAS_IMPORTACION} filas. Divida el archivo para importar más activos.', 'warning')
                    break
                try:
                    # Validaciones básicas (solo nombre y placa son obligatorios)
                    nombre = fila.get('nombre_activo', '').strip()
                    # Intentar obtener placa_codigo_interno o su alternativa 'placa_codigo'
                    placa = fila.get('placa_codigo_interno', '').strip()
                    if not placa:
                        placa = fila.get('placa_codigo', '').strip()

                    if not nombre or not placa:
                        errores.append(f"Fila {idx}: Campos obligatorios vacíos (nombre o placa)")
                        activos_omitidos += 1
                        continue

                    # Verificar si ya existe la placa
                    activo_existente = db.session.scalar(
                        select(Activo).where(Activo.placa_codigo_interno == placa)
                    )
                    if activo_existente:
                        errores.append(f"Fila {idx}: Placa '{placa}' ya existe en la base de datos")
                        activos_omitidos += 1
                        continue

                    # Crear nuevo activo con campos básicos
                    nuevo_activo = Activo(
                        nombre_activo=nombre,
                        placa_codigo_interno=placa,
                        marca=fila.get('marca', '').strip() or None,
                        modelo=fila.get('modelo', '').strip() or None,
                        serie=fila.get('serie', '').strip() or None,
                        ubicacion=fila.get('ubicacion', '').strip() or None,
                        estado='Operativo',  # Por defecto
                        tipo_propiedad='Propio',  # Por defecto, se puede editar después
                        origen_adquisicion='Compra'  # Por defecto
                    )

                    # Valor comercial (OPCIONAL - para activos fantasma)
                    valor_str = fila.get('valor_comercial', '').strip()
                    if valor_str:
                        try:
                            nuevo_activo.valor_comercial = float(valor_str)
                        except ValueError:
                            # Si no es un número válido, dejar en 0 y continuar
                            nuevo_activo.valor_comercial = 0.0
                            errores.append(f"Fila {idx}: Warning - valor_comercial '{valor_str}' no válido, se asignó 0")
                    else:
                        nuevo_activo.valor_comercial = 0.0  # Activo fantasma sin valor

                    # Clase de activo (OPCIONAL)
                    clase_id_str = fila.get('clase_id', '').strip()
                    if clase_id_str and clase_id_str.isdigit():
                        clase_id = int(clase_id_str)
                        # Validar que la clase exista
                        clase_existe = db.session.scalar(
                            select(ClaseActivo).where(ClaseActivo.id == clase_id)
                        )
                        if clase_existe:
                            nuevo_activo.clase_id = clase_id
                        else:
                            errores.append(f"Fila {idx}: Warning - clase_id {clase_id} no existe, se omitió")

                    # Guardar en la base de datos
                    db.session.add(nuevo_activo)
                    activos_creados += 1

                except Exception as e:
                    errores.append(f"Fila {idx}: Error inesperado - {str(e)}")
                    activos_omitidos += 1
                    current_app.logger.error(f"Error al importar fila {idx}: {e}")

            # Commit de todos los activos válidos
            try:
                db.session.commit()

                # Mensaje de éxito
                mensaje_exito = f'Importación completada: {activos_creados} activo(s) creado(s)'
                if activos_omitidos > 0:
                    mensaje_exito += f', {activos_omitidos} omitido(s)'

                flash(mensaje_exito, 'success')

                # Mostrar errores si los hay
                if errores:
                    errores_limitados = errores[:10]  # Mostrar máximo 10 errores
                    for error in errores_limitados:
                        flash(error, 'warning')
                    if len(errores) > 10:
                        flash(f'... y {len(errores) - 10} error(es) más', 'info')

                return redirect(url_for('activos.ver_activos'))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al hacer commit de importación: {e}")
                flash(f'Error al guardar los activos: {str(e)}', 'danger')
                return redirect(url_for('activos.importar_activos'))

        except Exception as e:
            current_app.logger.error(f"Error general en importación CSV: {e}")
            flash(f'Error al procesar el archivo CSV: {str(e)}', 'danger')
            return redirect(url_for('activos.importar_activos'))

    # GET - Mostrar formulario de importación
    return render_template('importar_activos.html')


# ============================================================================
# IMPORTACIÓN MASIVA DE ACTIVOS AJENOS DESDE CSV (MIGRACIÓN)
# ============================================================================

@activos_bp.route('/descargar-plantilla-ajenos-csv')
@login_required
@role_required('Admin')
def descargar_plantilla_ajenos_csv():
    """
    Genera y sirve una plantilla CSV para la migración de activos ajenos.
    """
    import io
    import csv
    from flask import make_response

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';') # Usamos punto y coma para compatibilidad con Excel en español
    
    # Escribir el encabezado
    writer.writerow(['nombre', 'placa_codigo_interno', 'serial', 'referencia'])
    
    # Escribir una fila de ejemplo
    writer.writerow(['Monitor de Signos Vitales (Comodato)', 'AJENO-001', 'SN-MONITOR-XYZ', 'Mindray ePM12'])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=plantilla_migracion_ajenos.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

@activos_bp.route('/importar-ajenos', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def importar_activos_ajenos():
    """
    Vista para la migración masiva de activos ajenos desde un archivo CSV simple.
    El CSV debe tener las columnas: "serial", "placa_codigo_interno", "referencia", "nombre".
    """
    import csv
    import io

    if request.method == 'POST':
        try:
            archivo_csv = request.files.get('archivo_csv')

            if not archivo_csv or archivo_csv.filename == '':
                flash('Por favor, seleccione un archivo CSV para la migración.', 'warning')
                return redirect(url_for('activos.importar_activos_ajenos'))

            if not archivo_csv.filename.endswith('.csv'):
                flash('El archivo debe tener formato CSV (.csv)', 'danger')
                return redirect(url_for('activos.importar_activos_ajenos'))

            # Leer el contenido del archivo con detección automática de codificación
            contenido_bytes = archivo_csv.stream.read()

            # Intentar decodificar con varias codificaciones comunes
            contenido_csv = None
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']

            for encoding in encodings:
                try:
                    contenido_csv = contenido_bytes.decode(encoding)
                    current_app.logger.info(f"[Import Ajeno] Archivo decodificado exitosamente con '{encoding}'")
                    break
                except UnicodeDecodeError:
                    continue

            if contenido_csv is None:
                flash('No se pudo leer el archivo CSV. Verifica que esté en un formato de texto válido.', 'danger')
                return redirect(url_for('activos.importar_activos_ajenos'))

            # Detección de delimitador
            delimitador = ','
            try:
                sniffer = csv.Sniffer()
                delimitador = sniffer.sniff(contenido_csv[:1024]).delimiter
                current_app.logger.info(f"[Import Ajeno] Delimitador detectado: '{delimitador}'")
            except csv.Error:
                current_app.logger.warning("[Import Ajeno] No se pudo detectar el delimitador, usando ',' por defecto.")

            stream = io.StringIO(contenido_csv)
            csv_reader = csv.DictReader(stream, delimiter=delimitador)
            
            columnas_csv = [col.strip().lower() for col in csv_reader.fieldnames or []]
            columnas_requeridas = ['serial', 'placa_codigo_interno', 'referencia', 'nombre']

            if not all(col in columnas_csv for col in columnas_requeridas):
                columnas_faltantes = [col for col in columnas_requeridas if col not in columnas_csv]
                flash(f'El archivo CSV no contiene las columnas requeridas. Faltan: {", ".join(columnas_faltantes)}', 'danger')
                return redirect(url_for('activos.importar_activos_ajenos'))

            activos_creados = 0
            activos_omitidos = 0
            errores = []

            # Límite de filas para prevenir timeout en importaciones masivas
            MAX_FILAS_IMPORTACION = 1000
            fila_count = 0

            for idx, fila in enumerate(csv_reader, start=2):
                fila_count += 1

                # Verificar límite de filas
                if fila_count > MAX_FILAS_IMPORTACION:
                    errores.append(f"Límite de importación alcanzado: {MAX_FILAS_IMPORTACION} filas. Las filas restantes no fueron procesadas.")
                    flash(f'Advertencia: Se procesaron solo las primeras {MAX_FILAS_IMPORTACION} filas. Divida el archivo para importar más activos.', 'warning')
                    break
                try:
                    placa = fila.get('placa_codigo_interno', '').strip()
                    nombre = fila.get('nombre', '').strip()

                    if not placa or not nombre:
                        errores.append(f"Fila {idx}: 'placa_codigo_interno' y 'nombre' son obligatorios.")
                        activos_omitidos += 1
                        continue

                    # Verificar si el activo ya existe
                    activo_existente = db.session.scalar(
                        select(Activo).where(Activo.placa_codigo_interno == placa)
                    )
                    if activo_existente:
                        errores.append(f"Fila {idx}: La placa '{placa}' ya existe. Se omite.")
                        activos_omitidos += 1
                        continue

                    # Crear el nuevo activo ajeno
                    nuevo_activo = Activo(
                        nombre_activo=nombre,
                        placa_codigo_interno=placa,
                        serie=fila.get('serial', '').strip() or None,
                        modelo=fila.get('referencia', '').strip() or None, # Mapeamos 'referencia' a 'modelo'
                        tipo_propiedad='Ajeno', # Marcado como Ajeno
                        estado='Operativo', # Estado inicial por defecto (mismo valor canónico que el resto del sistema)
                        valor_comercial=0.0, # Valor por defecto para activos ajenos
                        ubicacion=fila.get('ubicacion', '').strip() or 'Pendiente de Asignación' # Lee del CSV o usa valor por defecto
                    )
                    db.session.add(nuevo_activo)
                    activos_creados += 1

                except Exception as e:
                    errores.append(f"Fila {idx}: Error inesperado - {str(e)}")
                    activos_omitidos += 1
                    current_app.logger.error(f"Error al importar activo ajeno en fila {idx}: {e}")

            db.session.commit()

            # Mensajes de feedback para el usuario
            mensaje_exito = f'Migración completada: {activos_creados} activo(s) ajeno(s) creado(s).'
            if activos_omitidos > 0:
                mensaje_exito += f' {activos_omitidos} fila(s) omitida(s).'
            
            flash(mensaje_exito, 'success')

            if errores:
                for error in errores[:5]: # Mostrar hasta 5 errores detallados
                    flash(error, 'warning')
                if len(errores) > 5:
                    flash(f'... y {len(errores) - 5} errores más. Revise los logs para más detalles.', 'info')

            return redirect(url_for('activos.ver_activos', filtro_tipo='Ajeno'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error crítico en la importación de activos ajenos: {e}", exc_info=True)
            flash(f'Ocurrió un error grave durante la migración: {str(e)}', 'danger')
            return redirect(url_for('activos.importar_activos_ajenos'))

    # Método GET: renderizar la plantilla de importación
    return render_template('importar_activos_ajenos.html')


# ============================================================================
# EXPORTACIÓN DE INVENTARIO A EXCEL Y PDF
# ============================================================================

@activos_bp.route('/exportar-inventario-excel', methods=['GET'])
@login_required
def exportar_inventario_excel():
    """
    Exporta el inventario de activos a Excel con opción de filtrar por rango de fechas.

    Parámetros GET:
    - exportar_todo: 'true' para exportar todo el inventario
    - fecha_desde: Fecha de inicio del rango (formato YYYY-MM-DD)
    - fecha_hasta: Fecha de fin del rango (formato YYYY-MM-DD)
    """
    from flask import send_file
    from datetime import datetime
    from ..excel_export import exportar_inventario_excel

    try:
        # Obtener parámetros
        exportar_todo = request.args.get('exportar_todo', 'false').lower() == 'true'
        fecha_desde_str = request.args.get('fecha_desde', '').strip()
        fecha_hasta_str = request.args.get('fecha_hasta', '').strip()

        # Construir consulta base
        stmt = (
            select(Activo, ClaseActivo.nombre_clase, (Funcionario.nombres + ' ' + Funcionario.apellidos).label('funcionario_responsable'))
            .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
            .outerjoin(Funcionario, Activo.funcionario_id == Funcionario.id)
        )

        conditions = []
        filtros_info = {}

        # Si no es exportar todo, aplicar filtro de fechas
        if not exportar_todo:
            if fecha_desde_str:
                try:
                    fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
                    conditions.append(Activo.created_at >= fecha_desde)
                    filtros_info['fecha_desde'] = fecha_desde_str
                except ValueError:
                    flash('Formato de fecha de inicio inválido. Use YYYY-MM-DD.', 'danger')
                    return redirect(url_for('activos.ver_activos'))

            if fecha_hasta_str:
                try:
                    # Agregar un día completo a la fecha hasta (hasta las 23:59:59)
                    fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d')
                    from datetime import timedelta
                    fecha_hasta = fecha_hasta + timedelta(days=1)
                    conditions.append(Activo.created_at < fecha_hasta)
                    filtros_info['fecha_hasta'] = fecha_hasta_str
                except ValueError:
                    flash('Formato de fecha de fin inválido. Use YYYY-MM-DD.', 'danger')
                    return redirect(url_for('activos.ver_activos'))

        # Aplicar condiciones si existen
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Ordenar por fecha de ingreso (más recientes primero)
        stmt = stmt.order_by(Activo.created_at.desc())

        # Ejecutar consulta
        result = db.session.execute(stmt).all()

        # Procesar resultados
        activos = []
        for row in result:
            activo, nombre_clase, funcionario_responsable = row
            activo.nombre_clase = nombre_clase
            activo.funcionario_responsable = funcionario_responsable

            # Normalizar valor_comercial
            if activo.valor_comercial is None:
                activo.valor_comercial = 0.0

            activos.append(activo)

        # Verificar que haya activos para exportar
        if not activos:
            flash('No hay activos que cumplan con los criterios de exportación.', 'warning')
            return redirect(url_for('activos.ver_activos'))

        # Generar archivo Excel
        excel_file = exportar_inventario_excel(activos, filtros=filtros_info)

        # Generar nombre de archivo
        if exportar_todo:
            nombre_archivo = f"inventario_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:
            nombre_archivo = f"inventario_{fecha_desde_str or 'inicio'}_{fecha_hasta_str or 'hoy'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Enviar archivo
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        current_app.logger.error(f"Error al exportar inventario a Excel: {e}", exc_info=True)
        flash(f'Error al generar el archivo Excel: {str(e)}', 'danger')
        return redirect(url_for('activos.ver_activos'))


@activos_bp.route('/exportar-inventario-pdf', methods=['GET'])
@login_required
def exportar_inventario_pdf():
    """
    Exporta el inventario de activos a PDF con opción de filtrar por rango de fechas.

    Parámetros GET:
    - exportar_todo: 'true' para exportar todo el inventario
    - fecha_desde: Fecha de inicio del rango (formato YYYY-MM-DD)
    - fecha_hasta: Fecha de fin del rango (formato YYYY-MM-DD)
    """
    from flask import send_file
    from datetime import datetime, timedelta
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from io import BytesIO

    try:
        # Obtener parámetros
        exportar_todo = request.args.get('exportar_todo', 'false').lower() == 'true'
        fecha_desde_str = request.args.get('fecha_desde', '').strip()
        fecha_hasta_str = request.args.get('fecha_hasta', '').strip()

        # Construir consulta base
        stmt = (
            select(Activo, ClaseActivo.nombre_clase, (Funcionario.nombres + ' ' + Funcionario.apellidos).label('funcionario_responsable'))
            .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
            .outerjoin(Funcionario, Activo.funcionario_id == Funcionario.id)
        )

        conditions = []
        filtros_texto = []

        # Si no es exportar todo, aplicar filtro de fechas
        if not exportar_todo:
            if fecha_desde_str:
                try:
                    fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
                    conditions.append(Activo.created_at >= fecha_desde)
                    filtros_texto.append(f"Desde: {fecha_desde_str}")
                except ValueError:
                    flash('Formato de fecha de inicio inválido. Use YYYY-MM-DD.', 'danger')
                    return redirect(url_for('activos.ver_activos'))

            if fecha_hasta_str:
                try:
                    fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d')
                    fecha_hasta = fecha_hasta + timedelta(days=1)
                    conditions.append(Activo.created_at < fecha_hasta)
                    filtros_texto.append(f"Hasta: {fecha_hasta_str}")
                except ValueError:
                    flash('Formato de fecha de fin inválido. Use YYYY-MM-DD.', 'danger')
                    return redirect(url_for('activos.ver_activos'))

        # Aplicar condiciones si existen
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Ordenar por fecha de ingreso
        stmt = stmt.order_by(Activo.created_at.desc())

        # Ejecutar consulta
        result = db.session.execute(stmt).all()

        # Procesar resultados
        activos = []
        for row in result:
            activo, nombre_clase, funcionario_responsable = row
            activo.nombre_clase = nombre_clase
            activo.funcionario_responsable = funcionario_responsable

            if activo.valor_comercial is None:
                activo.valor_comercial = 0.0

            activos.append(activo)

        # Verificar que haya activos
        if not activos:
            flash('No hay activos que cumplan con los criterios de exportación.', 'warning')
            return redirect(url_for('activos.ver_activos'))

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)

        # Contenedor de elementos
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#0066CC'),
            spaceAfter=12,
            alignment=1  # Centro
        )

        # Título
        titulo = Paragraph("INVENTARIO GENERAL DE ACTIVOS - JEROSMART", title_style)
        elements.append(titulo)

        # Información del reporte
        info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=9, alignment=1)
        fecha_generacion = Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", info_style)
        elements.append(fecha_generacion)

        if filtros_texto:
            filtros_info = Paragraph(f"Filtros: {' | '.join(filtros_texto)}", info_style)
            elements.append(filtros_info)

        elements.append(Spacer(1, 0.3*inch))

        # Crear tabla
        data = [['Placa', 'Nombre', 'Tipo', 'Clase', 'Estado', 'Ubicación', 'Valor', 'Fecha Ingreso']]

        valor_total = 0
        for activo in activos:
            nombre_clase = activo.nombre_clase or ''
            valor = activo.valor_comercial if activo.valor_comercial else 0
            valor_total += valor

            data.append([
                activo.placa_codigo_interno[:15],  # Truncar para ajustar
                activo.nombre_activo[:25],
                activo.tipo_propiedad or 'Propio',
                nombre_clase[:15],
                activo.estado[:15],
                (activo.ubicacion or '')[:20],
                f"${valor:,.0f}",
                activo.created_at.strftime('%d/%m/%Y') if activo.created_at else ''
            ])

        # Agregar fila de totales
        data.append(['', '', '', '', '', 'TOTAL:', f"${valor_total:,.0f}", f"{len(activos)} activos"])

        # Crear tabla
        t = Table(data, colWidths=[0.8*inch, 1.8*inch, 0.7*inch, 1.0*inch, 0.9*inch, 1.3*inch, 0.9*inch, 0.9*inch])

        # Estilo de tabla
        t.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Datos
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F5F5')]),

            # Fila de totales
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E6F2FF')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#0066CC')),
        ]))

        elements.append(t)

        # Construir PDF
        doc.build(elements)

        # Preparar para envío
        buffer.seek(0)

        # Generar nombre de archivo
        if exportar_todo:
            nombre_archivo = f"inventario_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            nombre_archivo = f"inventario_{fecha_desde_str or 'inicio'}_{fecha_hasta_str or 'hoy'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/pdf'
        )

    except Exception as e:
        current_app.logger.error(f"Error al exportar inventario a PDF: {e}", exc_info=True)
        flash(f'Error al generar el archivo PDF: {str(e)}', 'danger')
        return redirect(url_for('activos.ver_activos'))
