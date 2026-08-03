"""
Módulo de Proveedores - JeroSmart Activos
Gestión completa de proveedores con importación CSV
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import csv
import os
from werkzeug.utils import secure_filename

from app import db
from app.models import Proveedor
from app.proveedores.forms import ProveedorForm
from app.decorators import login_required, role_required


proveedores_bp = Blueprint(
    'proveedores',
    __name__,
    template_folder='templates',
    url_prefix='/proveedores'
)



# LISTAR PROVEEDORES

@proveedores_bp.route('/')
@login_required
def listar_proveedores():
    """
    Lista todos los proveedores con paginación y búsqueda.
    Estilo iOS con cards y animaciones.
    """
    # Búsqueda
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Query base
    query = select(Proveedor).order_by(Proveedor.razon_social)

    # Aplicar búsqueda si existe
    if q:
        search_filter = (
            Proveedor.razon_social.ilike(f'%{q}%') |
            Proveedor.nit.ilike(f'%{q}%') |
            Proveedor.persona_contacto.ilike(f'%{q}%')
        )
        query = query.where(search_filter)

    # Ejecutar query con paginación
    proveedores_paginated = db.paginate(
        query,
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template(
        'proveedores/ver_proveedores.html',
        proveedores=proveedores_paginated,
        search_query=q
    )


# ============================================================================
# NUEVO PROVEEDOR
# ============================================================================
@proveedores_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def nuevo_proveedor():
    """
    Crea un nuevo proveedor.
    """
    form = ProveedorForm()

    if form.validate_on_submit():
        try:
            # Verificar duplicados antes de crear
            if db.session.scalar(select(Proveedor).where(Proveedor.nit == form.nit.data)):
                flash('Ya existe un proveedor con ese NIT.', 'danger')
                return render_template(
                    'proveedores/formulario_proveedor.html',
                    form=form,
                    titulo='Nuevo Proveedor',
                    modo='crear'
                )

            proveedor = Proveedor(
                nit=form.nit.data.strip(),
                razon_social=form.razon_social.data.strip(),
                direccion=form.direccion.data.strip(),
                numero_contacto=form.numero_contacto.data.strip() if form.numero_contacto.data else None,
                persona_contacto=form.persona_contacto.data.strip() if form.persona_contacto.data else None
            )

            db.session.add(proveedor)
            db.session.commit()

            flash(f'Proveedor "{proveedor.razon_social}" creado exitosamente.', 'success')
            return redirect(url_for('proveedores.listar_proveedores'))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al crear proveedor: {e}")
            flash('Error: Ya existe un proveedor con ese NIT o Razón Social.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al crear proveedor: {e}")
            flash(f'Error inesperado al crear el proveedor: {str(e)}', 'danger')

    return render_template(
        'proveedores/formulario_proveedor.html',
        form=form,
        titulo='Nuevo Proveedor',
        modo='crear'
    )


# ============================================================================
# EDITAR PROVEEDOR
# ============================================================================
@proveedores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def editar_proveedor(id):
    """
    Edita un proveedor existente.
    """
    proveedor = db.session.get(Proveedor, id)
    if not proveedor:
        flash('Proveedor no encontrado.', 'danger')
        return redirect(url_for('proveedores.listar_proveedores'))

    form = ProveedorForm(obj=proveedor)

    if form.validate_on_submit():
        try:
            # Verificar duplicado de NIT (solo si cambió)
            if form.nit.data != proveedor.nit:
                if db.session.scalar(select(Proveedor).where(Proveedor.nit == form.nit.data)):
                    flash('Ya existe otro proveedor con ese NIT.', 'danger')
                    return render_template(
                        'proveedores/formulario_proveedor.html',
                        form=form,
                        titulo='Editar Proveedor',
                        proveedor=proveedor,
                        modo='editar'
                    )

            # Verificar duplicado de Razón Social (solo si cambió)
            if form.razon_social.data != proveedor.razon_social:
                if db.session.scalar(select(Proveedor).where(Proveedor.razon_social == form.razon_social.data)):
                    flash('Ya existe otro proveedor con esa Razón Social.', 'danger')
                    return render_template(
                        'proveedores/formulario_proveedor.html',
                        form=form,
                        titulo='Editar Proveedor',
                        proveedor=proveedor,
                        modo='editar'
                    )

            # Actualizar datos
            proveedor.nit = form.nit.data.strip()
            proveedor.razon_social = form.razon_social.data.strip()
            proveedor.direccion = form.direccion.data.strip()
            proveedor.numero_contacto = form.numero_contacto.data.strip() if form.numero_contacto.data else None
            proveedor.persona_contacto = form.persona_contacto.data.strip() if form.persona_contacto.data else None

            db.session.commit()

            flash(f'Proveedor "{proveedor.razon_social}" actualizado exitosamente.', 'success')
            return redirect(url_for('proveedores.listar_proveedores'))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al actualizar proveedor: {e}")
            flash('Error de integridad: Verifique que el NIT o Razón Social no estén duplicados.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al actualizar proveedor: {e}")
            flash(f'Error inesperado al actualizar el proveedor: {str(e)}', 'danger')

    return render_template(
        'proveedores/formulario_proveedor.html',
        form=form,
        titulo='Editar Proveedor',
        proveedor=proveedor,
        modo='editar'
    )


# ============================================================================
# ELIMINAR PROVEEDOR
# ============================================================================
@proveedores_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('Admin')
def eliminar_proveedor(id):
    """
    Elimina un proveedor (solo si no tiene relaciones).
    """
    proveedor = db.session.get(Proveedor, id)
    if not proveedor:
        flash('Proveedor no encontrado.', 'danger')
        return redirect(url_for('proveedores.listar_proveedores'))

    try:
        nombre = proveedor.razon_social
        db.session.delete(proveedor)
        db.session.commit()

        flash(f'Proveedor "{nombre}" eliminado exitosamente.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash(
            'No se puede eliminar este proveedor porque está asociado a movimientos de entrega.',
            'danger'
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar proveedor: {e}")
        flash(f'Error inesperado al eliminar el proveedor: {str(e)}', 'danger')

    return redirect(url_for('proveedores.listar_proveedores'))


# ============================================================================
# IMPORTACIÓN MASIVA DE PROVEEDORES DESDE CSV
# ============================================================================

def detectar_encoding_csv(archivo_path):
    """
    Detecta la codificación del archivo CSV.
    Intenta múltiples encodings comunes en Windows y Excel.
    """
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']

    for encoding in encodings:
        try:
            with open(archivo_path, 'r', encoding=encoding) as f:
                f.read()
            current_app.logger.info(f"Archivo CSV decodificado con encoding: {encoding}")
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue

    current_app.logger.warning("No se pudo detectar encoding del CSV, usando utf-8 por defecto")
    return 'utf-8'


def detectar_delimitador_csv(archivo_path, encoding):
    """
    Detecta el delimitador del archivo CSV (coma, punto y coma o tabulador).
    """
    with open(archivo_path, 'r', encoding=encoding) as f:
        primera_linea = f.readline()

    if ';' in primera_linea:
        return ';'
    elif '\t' in primera_linea:
        return '\t'
    else:
        return ','


@proveedores_bp.route('/importar', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def importar_proveedores():
    """
    Importa proveedores desde un archivo CSV.

    Columnas esperadas en el CSV (exactas, tal como las escribiste):
    - Nombre Del Proveedor
    - NIT
    - Persona De Contacto
    - Teléfono
    - Dirección
    """
    if request.method == 'POST':
        # Validar que se subió un archivo
        if 'archivo_csv' not in request.files:
            flash('No se encontró el archivo CSV.', 'warning')
            return redirect(request.url)

        file = request.files['archivo_csv']

        if file.filename == '':
            flash('No seleccionaste ningún archivo.', 'warning')
            return redirect(request.url)

        if not file.filename.endswith('.csv'):
            flash('El archivo debe ser formato CSV (.csv)', 'danger')
            return redirect(request.url)

        # Guardar archivo temporalmente
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(f"import_proveedores_{file.filename}")
        filepath = os.path.join(upload_folder, filename)

        try:
            file.save(filepath)

            # Detectar encoding y delimitador
            encoding = detectar_encoding_csv(filepath)
            delimitador = detectar_delimitador_csv(filepath, encoding)

            current_app.logger.info(f"Procesando CSV con encoding={encoding}, delimitador={delimitador}")

            # Leer CSV
            with open(filepath, 'r', encoding=encoding) as f:
                contenido = f.read()

            lineas = contenido.splitlines()
            reader = csv.DictReader(lineas, delimiter=delimitador)

            # Normalizar nombres de columnas (eliminar espacios extras, convertir a minúsculas)
            reader.fieldnames = [campo.strip().lower() for campo in reader.fieldnames]

            # Mapeo EXACTO de columnas según lo que escribiste
            column_mapping = {
                'nombre del proveedor': 'razon_social',
                'nit': 'nit',
                'persona de contacto': 'persona_contacto',
                'teléfono': 'numero_contacto',
                'telefono': 'numero_contacto',  # Por si no tiene tilde
                'dirección': 'direccion',
                'direccion': 'direccion'  # Por si no tiene tilde
            }

            # Verificar que existan las columnas obligatorias
            columnas_requeridas = ['nombre del proveedor', 'nit']
            columnas_csv = reader.fieldnames

            columnas_faltantes = []
            for col_req in columnas_requeridas:
                if col_req not in columnas_csv:
                    columnas_faltantes.append(col_req)

            if columnas_faltantes:
                flash(
                    f'El archivo CSV debe contener las columnas obligatorias: {", ".join(columnas_faltantes)}',
                    'danger'
                )
                return redirect(request.url)

            # Procesar cada fila
            proveedores_creados = 0
            proveedores_omitidos = 0
            errores = []

            for idx, fila in enumerate(reader, start=2):  # Empezar en 2 por la cabecera
                try:
                    # Mapear columnas
                    nit = fila.get('nit', '').strip()
                    razon_social = fila.get('nombre del proveedor', '').strip()
                    direccion = fila.get('dirección') or fila.get('direccion', '').strip()
                    persona_contacto = fila.get('persona de contacto', '').strip() or None
                    numero_contacto = fila.get('teléfono') or fila.get('telefono', '').strip() or None

                    # Validar campos obligatorios
                    if not nit or not razon_social:
                        errores.append(f"Fila {idx}: Faltan datos obligatorios (NIT o Nombre)")
                        proveedores_omitidos += 1
                        continue

                    # Si no hay dirección, usar valor por defecto
                    if not direccion:
                        direccion = 'Sin dirección registrada'

                    # Verificar si ya existe el proveedor por NIT
                    proveedor_existente = db.session.scalar(
                        select(Proveedor).where(Proveedor.nit == nit)
                    )

                    if proveedor_existente:
                        errores.append(f"Fila {idx}: El NIT '{nit}' ya existe")
                        proveedores_omitidos += 1
                        continue

                    # Crear nuevo proveedor
                    nuevo_proveedor = Proveedor(
                        nit=nit,
                        razon_social=razon_social,
                        direccion=direccion,
                        persona_contacto=persona_contacto,
                        numero_contacto=numero_contacto
                    )

                    db.session.add(nuevo_proveedor)
                    proveedores_creados += 1

                except Exception as e:
                    errores.append(f"Fila {idx}: Error inesperado - {str(e)}")
                    proveedores_omitidos += 1
                    current_app.logger.error(f"Error al importar fila {idx}: {e}")

            # Commit de todos los proveedores válidos
            if proveedores_creados > 0:
                db.session.commit()
                flash(
                    f'Importación completada: {proveedores_creados} proveedor(es) creado(s).',
                    'success'
                )

            if proveedores_omitidos > 0:
                flash(
                    f'{proveedores_omitidos} fila(s) omitida(s). Ver detalles en los mensajes.',
                    'warning'
                )

            # Mostrar errores (máximo 10)
            if errores:
                errores_limitados = errores[:10]
                for error in errores_limitados:
                    flash(error, 'warning')
                if len(errores) > 10:
                    flash(f'... y {len(errores) - 10} error(es) más', 'info')

            if proveedores_creados == 0 and proveedores_omitidos == 0:
                flash('No se encontraron datos válidos para importar.', 'warning')

            return redirect(url_for('proveedores.listar_proveedores'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error crítico en importación CSV: {e}", exc_info=True)
            flash(f'Error al procesar el archivo: {str(e)}', 'danger')
            return redirect(request.url)
        finally:
            # Eliminar archivo temporal
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    current_app.logger.warning(f"No se pudo eliminar archivo temporal: {e}")

    # GET - Mostrar formulario de importación
    return render_template('proveedores/importar_proveedores.html')


# ============================================================================
# DESCARGAR PLANTILLA CSV
# ============================================================================
@proveedores_bp.route('/descargar-plantilla-csv')
@login_required
def descargar_plantilla_csv():
    """
    Descarga una plantilla CSV de ejemplo para importación de proveedores.
    """
    from flask import Response

    # Plantilla con nombres EXACTOS de columnas
    plantilla_csv = """Nombre Del Proveedor,NIT,Persona De Contacto,Teléfono,Dirección
Proveedor Ejemplo S.A.S.,900123456-7,Juan Pérez,3001234567,Calle 123 #45-67
Distribuidora Médica Ltda,800987654-3,María Gómez,3109876543,Carrera 45 #12-34
Equipos Hospitalarios S.A.,700456789-1,Carlos Rodríguez,3201234567,Avenida 68 #23-45"""

    return Response(
        plantilla_csv,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=plantilla_proveedores.csv',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================
@proveedores_bp.route('/api/lista')
@login_required
def api_lista_proveedores():
    """
    Endpoint API para obtener lista de proveedores.
    Retorna JSON con id, nombre y nit.
    Optimizado para ser usado en selectores dinámicos (ej. wizard de movimientos).

    Uso en la ruta que renderiza el wizard (ej. add_movimiento):
    -------------------------------------------------------------
    from app.models import Proveedor
    from sqlalchemy import select

    @movimientos_bp.route('/nuevo', methods=['GET', 'POST'])
    def add_movimiento():
        proveedores = db.session.scalars(select(Proveedor).order_by(Proveedor.razon_social)).all()
        return render_template('movimientos/add_movimiento.html', proveedores=proveedores)
    -------------------------------------------------------------
    """
    from flask import jsonify

    proveedores = db.session.execute(select(Proveedor.id, Proveedor.razon_social, Proveedor.nit).order_by(Proveedor.razon_social)).all()

    return jsonify([
        {
            'id': p.id,
            'nombre': p.razon_social,
            'nit': p.nit
        }
        for p in proveedores
    ])
