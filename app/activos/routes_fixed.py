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
    Activo, ClaseActivo, Funcionario, Movimiento, MovimientoActivo,
    Mantenimiento, HojasDeVida
)
from ..decorators import login_required, role_required

activos_bp = Blueprint(
    'activos',
    __name__,
    template_folder='templates',
)

# Atributos dinámicos según normativa colombiana
# Clase 1: Equipo Biomédico (Res. 4725/2011, Dec. 4725/2005)
# Clase 2: Electroindustrial (RETIE, NTC 2050)
# Clase 3: Tecnología Comunicación e Información - TICs (NIIF Sección 17)
# Clase 4: Muebles y Enseres (NIIF Sección 17, PGCP Colombia)
ATRIBUTOS_POR_CLASE = {
    '1': [  # EQUIPO BIOMÉDICO
        {'name': 'registro_invima', 'label': 'Registro Sanitario INVIMA', 'type': 'text',
         'required': True, 'placeholder': 'Ej: 2024DM-0012345'},
        {'name': 'clasificacion_riesgo', 'label': 'Clasificación de Riesgo (Res. 4725/2011)',
         'type': 'select', 'options': ['I', 'IIa', 'IIb', 'III'], 'required': True},
        {'name': 'clasificacion_biomedica', 'label': 'Clasificación Biomédica', 'type': 'select',
         'options': ['Diagnóstico', 'Tratamiento y Mantenimiento de la Vida', 'Prevención',
                    'Rehabilitación', 'Análisis de Laboratorio'], 'required': True},
        {'name': 'fabricante', 'label': 'Fabricante', 'type': 'text', 'required': True},
        {'name': 'pais_origen', 'label': 'País de Origen', 'type': 'text', 'required': False},
        {'name': 'vida_util', 'label': 'Vida Útil según Fabricante (años)', 'type': 'number',
         'required': True, 'min': 1, 'max': 30},
        {'name': 'frecuencia_mantenimiento', 'label': 'Frecuencia Mantenimiento Preventivo',
         'type': 'select', 'options': ['Mensual', 'Trimestral', 'Semestral', 'Anual'],
         'required': True},
        {'name': 'requiere_calibracion', 'label': '¿Requiere Calibración?', 'type': 'select',
         'options': ['Sí', 'No'], 'required': True},
        {'name': 'voltaje_operacion', 'label': 'Voltaje de Operación (V)', 'type': 'text',
         'required': False, 'placeholder': 'Ej: 110V AC'},
        {'name': 'potencia', 'label': 'Potencia (W)', 'type': 'number', 'required': False},
        {'name': 'ultimo_mantenimiento', 'label': 'Último Mantenimiento', 'type': 'date',
         'required': False}
    ],
    '2': [  # ELECTROINDUSTRIAL
        {'name': 'voltaje_nominal', 'label': 'Voltaje Nominal (V)', 'type': 'text',
         'required': True, 'placeholder': 'Ej: 220V AC'},
        {'name': 'corriente_nominal', 'label': 'Corriente Nominal (A)', 'type': 'number',
         'required': False, 'step': 0.1},
        {'name': 'potencia_nominal', 'label': 'Potencia Nominal (W/kW)', 'type': 'text',
         'required': False},
        {'name': 'cumple_retie', 'label': '¿Cumple RETIE?', 'type': 'select',
         'options': ['Sí', 'No', 'No Aplica'], 'required': True},
        {'name': 'certificado_conformidad', 'label': 'Certificado de Conformidad', 'type': 'text',
         'required': False, 'placeholder': 'Número de certificado'},
        {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones Técnicas',
         'type': 'textarea', 'required': False, 'rows': 3}
    ],
    '3': [  # TECNOLOGÍA DE COMUNICACIÓN E INFORMACIÓN (TICs)
        {'name': 'tipo_equipo', 'label': 'Tipo de Equipo', 'type': 'select',
         'options': ['Computador de Escritorio', 'Portátil', 'Servidor', 'Impresora',
                    'Scanner', 'Router/Switch', 'Tablet', 'Otro'], 'required': True},
        {'name': 'procesador', 'label': 'Procesador', 'type': 'text', 'required': False,
         'placeholder': 'Ej: Intel Core i7 10ma Gen'},
        {'name': 'ram', 'label': 'Memoria RAM', 'type': 'text', 'required': False,
         'placeholder': 'Ej: 16GB DDR4'},
        {'name': 'almacenamiento', 'label': 'Almacenamiento', 'type': 'text', 'required': False,
         'placeholder': 'Ej: SSD 512GB'},
        {'name': 'sistema_operativo', 'label': 'Sistema Operativo', 'type': 'text',
         'required': False, 'placeholder': 'Ej: Windows 11 Pro'},
        {'name': 'licencia_software', 'label': 'Licencia de Software', 'type': 'text',
         'required': False, 'placeholder': 'Número de licencia o tipo'},
        {'name': 'direccion_ip', 'label': 'Dirección IP Asignada', 'type': 'text',
         'required': False, 'placeholder': 'Ej: 192.168.1.100'},
        {'name': 'direccion_mac', 'label': 'Dirección MAC', 'type': 'text', 'required': False,
         'placeholder': 'Ej: 00:1A:2B:3C:4D:5E'},
        {'name': 'vida_util_estimada', 'label': 'Vida Útil Estimada (años)', 'type': 'select',
         'options': ['3', '5', '7', '10'], 'required': True},
        {'name': 'especificaciones_tecnicas', 'label': 'Otras Especificaciones',
         'type': 'textarea', 'required': False, 'rows': 3}
    ],
    '4': [  # MUEBLES Y ENSERES
        {'name': 'tipo_mueble', 'label': 'Tipo de Mueble', 'type': 'select',
         'options': ['Escritorio', 'Silla', 'Archivador', 'Estantería', 'Mesa',
                    'Locker', 'Vitrina', 'Otro'], 'required': True},
        {'name': 'material', 'label': 'Material Principal', 'type': 'select',
         'options': ['Madera', 'Metal', 'Plástico', 'Vidrio', 'Mixto'], 'required': True},
        {'name': 'dimensiones', 'label': 'Dimensiones (Alto x Ancho x Fondo)', 'type': 'text',
         'required': False, 'placeholder': 'Ej: 75cm x 120cm x 60cm'},
        {'name': 'color', 'label': 'Color', 'type': 'text', 'required': False},
        {'name': 'estado_fisico', 'label': 'Estado Físico', 'type': 'select',
         'options': ['Excelente', 'Bueno', 'Regular', 'Malo'], 'required': True},
        {'name': 'tipo_adquisicion', 'label': 'Tipo de Adquisición', 'type': 'select',
         'options': ['Compra', 'Donación', 'Comodato', 'Fabricación Propia'], 'required': False},
        {'name': 'fecha_ingreso', 'label': 'Fecha de Ingreso', 'type': 'date', 'required': False},
        {'name': 'especificaciones_tecnicas', 'label': 'Descripción Adicional',
         'type': 'textarea', 'required': False, 'rows': 3}
    ]
}

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
        
        # Construir la ruta completa para guardar el archivo
        upload_base_dir = current_app.config['UPLOAD_FOLDER']
        subfolder_name = current_app.config[folder_key] # Ej. 'loan_contracts'
        target_full_dir = os.path.join(upload_base_dir, subfolder_name)
        os.makedirs(target_full_dir, exist_ok=True) # Asegurar que el directorio exista

        filename = secure_filename(f"{prefix}_{placa_codigo}_{file_storage.filename}")
        filepath = os.path.join(target_full_dir, filename)
        file_storage.save(filepath)
        # Retorna la ruta relativa para ser guardada en la BD
        return os.path.join(subfolder_name, filename)
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

        # Normalizar valor_comercial: asegurar que nunca sea None
        if activo.valor_comercial is None:
            activo.valor_comercial = 0.0

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

            # Validación para TICs (clase_id = 3)
            elif clase_id_str == '3':
                if attr_name == 'vida_util_estimada' and valor not in ['3', '5', '7', '10']:
                    errores[attr_name] = f"'{attr_label}' debe ser 3, 5, 7 o 10 años."

            # Validación para Muebles y Enseres (clase_id = 4)
            elif clase_id_str == '4':
                if attr_name == 'estado_fisico' and valor not in ['Excelente', 'Bueno', 'Regular', 'Malo']:
                    errores[attr_name] = f"'{attr_label}' debe ser Excelente, Bueno, Regular o Malo."

            # Se pueden agregar más validaciones específicas aquí...
            # Ejemplo: if attr_name == 'voltaje' and not re.match(r'^\d+V$', valor):
            #              errores[attr_name] = "Formato de voltaje inválido (ej: 110V)."

    return len(errores) == 0, errores

@activos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_activo():
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

                    # Validar atributos dinámicos obligatorios
                    es_valido, errores = validar_atributos_dinamicos(nuevo_activo.clase_id, atributos_dinamicos_guardar)
                    if not es_valido:
                        errores_msg = '; '.join([f"{k}: {v}" for k, v in errores.items()])
                        flash(f'Faltan campos obligatorios: {errores_msg}', 'danger')
                        return redirect(url_for('activos.add_activo'))

                nuevo_activo.atributos_dinamicos_json = json.dumps(atributos_dinamicos_guardar)

            elif tipo_propiedad == 'Ajeno':
                nuevo_activo.propietario_ajeno = request.form.get('propietario_ajeno')
                nuevo_activo.condicion_tenencia = request.form.get('condicion_tenencia')
            
            db.session.add(nuevo_activo)
            db.session.commit()
            flash('Activo agregado exitosamente.', 'success')
            return redirect(url_for('activos.ver_activos'))
        
        except ValueError as e:
            # Errores de validación (archivos, formato de datos)
            flash(str(e), 'danger')
            current_app.logger.warning(f"Error de validación al agregar activo: {e}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f"Fallo de integridad al agregar activo (placa duplicada?): {placa_codigo}")
            flash('Error de base de datos: La placa o código interno ya existe.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al agregar activo: {e}")
            flash(f'Error inesperado al procesar el formulario: {str(e)}', 'danger')
        return redirect(url_for('activos.ver_activos'))

    # --- Lógica para mostrar el wizard de creación ---
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    funcionarios = db.session.scalars(select(Funcionario).order_by(Funcionario.nombres, Funcionario.apellidos)).all()

    return render_template(
        'add_activo_wizard.html', # Usamos la nueva plantilla del wizard
        clases=clases,
        funcionarios=funcionarios,
        atributos_por_clase_json=json.dumps(ATRIBUTOS_POR_CLASE) # Pasamos los atributos para el wizard
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
                valor_comercial_str = data.get('valor_comercial')
                try:
                    activo.valor_comercial = float(valor_comercial_str) if valor_comercial_str else 0.0
                except (ValueError, TypeError):
                    flash('El valor comercial debe ser un número válido.', 'danger')
                    return redirect(url_for('activos.edit_activo', activo_id=activo_id))
                activo.origen_adquisicion = data.get('origen_adquisicion')
                activo.clase_id = int(data.get('clase_id')) if data.get('clase_id') else None
                activo.funcionario_id = int(data.get('funcionario_id')) if data.get('funcionario_id') else None
                
                atributos_dinamicos = {}
                if activo.clase_id and str(activo.clase_id) in ATRIBUTOS_POR_CLASE:
                    for attr_spec in ATRIBUTOS_POR_CLASE[str(activo.clase_id)]:
                        attr_name = attr_spec['name']
                        atributos_dinamicos[attr_name] = data.get(attr_name)

                    # Validar atributos dinámicos obligatorios
                    es_valido, errores = validar_atributos_dinamicos(activo.clase_id, atributos_dinamicos)
                    if not es_valido:
                        errores_msg = '; '.join([f"{k}: {v}" for k, v in errores.items()])
                        flash(f'Faltan campos obligatorios: {errores_msg}', 'danger')
                        return redirect(url_for('activos.edit_activo', activo_id=activo_id))

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

        except ValueError as e:
            # Errores de validación (archivos, formato de datos)
            flash(str(e), 'danger')
            current_app.logger.warning(f"Error de validación al editar activo: {e}")
        except exc.IntegrityError:
            db.session.rollback()
            flash('Error de base de datos: La placa o código interno ya existe para otro activo.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error inesperado al actualizar el activo: {e}', 'danger')
        return redirect(url_for('activos.edit_activo', activo_id=activo_id))
    
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    funcionarios = db.session.scalars(select(Funcionario).order_by(Funcionario.nombres, Funcionario.apellidos)).all()

    # Construir diccionario serializable (sin metadatos SQLAlchemy)
    datos_activo_para_frontend = {
        'id': activo.id,
        'nombre_activo': activo.nombre_activo,
        'placa_codigo_interno': activo.placa_codigo_interno,
        'marca': activo.marca,
        'modelo': activo.modelo,
        'serie': activo.serie,
        'ubicacion': activo.ubicacion,
        'estado': activo.estado,
        'observaciones': activo.observaciones,
        'tipo_propiedad': activo.tipo_propiedad,
        'valor_comercial': activo.valor_comercial,
        'origen_adquisicion': activo.origen_adquisicion,
        'clase_id': activo.clase_id,
        'funcionario_id': activo.funcionario_id,
        'propietario_ajeno': activo.propietario_ajeno,
        'condicion_tenencia': activo.condicion_tenencia,
    }

    # Agregar atributos dinámicos al diccionario
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
        funcionarios=funcionarios,
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
        select(HojasDeVida).where(HojasDeVida.activo_id == activo_id)
    )

    # Parsear atributos dinámicos
    atributos_dinamicos = {}
    if activo.atributos_dinamicos_json:
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
