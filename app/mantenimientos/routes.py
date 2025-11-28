from flask import render_template, request, redirect, url_for, flash, jsonify
from . import mantenimientos_bp
from ..decorators import login_required, role_required
from ..extensions import db
from ..models import Activo, HojaVidaEquipo, ClaseActivo, Mantenimiento, MantenimientoTipo
from .forms import MantenimientoForm
from flask_login import current_user
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

@mantenimientos_bp.route('/')
@login_required
def index():
    """
    Página principal del módulo de mantenimientos para activos no biomédicos.
    Este módulo gestiona: TICs, Equipos Electro-Industriales y Muebles y Enseres.
    """
    return render_template("mantenimientos/gestion_mantenimientos.html", active_page='mantenimientos')


# ==============================================================================
# RUTAS PARA HOJAS DE VIDA
# ==============================================================================

@mantenimientos_bp.route('/hojas_vida')
@login_required
def hojas_vida():
    """Lista todas las hojas de vida de equipos no biomédicos."""
    # Obtener hojas de vida de equipos de clases 2, 3, 4
    hojas = db.session.query(HojaVidaEquipo).join(Activo).filter(
        Activo.clase_id.in_([2, 3, 4])
    ).all()

    return render_template("mantenimientos/hojas_vida/lista_hojas_vida.html",
                         hojas=hojas,
                         active_page='mantenimientos')


@mantenimientos_bp.route('/hojas_vida/nueva', methods=['GET', 'POST'])
@login_required
def nueva_hoja_vida():
    """Crea una nueva hoja de vida para un equipo."""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            activo_id = request.form.get('activo_id')

            # Verificar que el activo existe y no tiene hoja de vida
            activo = Activo.query.get(activo_id)
            if not activo:
                flash('El activo no existe', 'error')
                return redirect(url_for('mantenimientos.nueva_hoja_vida'))

            if activo.hoja_vida_equipo:
                flash('Este activo ya tiene una hoja de vida registrada', 'warning')
                return redirect(url_for('mantenimientos.editar_hoja_vida', id=activo.hoja_vida_equipo.id))

            # Verificar que es un activo no biomédico (clase 2, 3, 4)
            if activo.clase_id not in [2, 3, 4]:
                flash('Solo se pueden crear hojas de vida para equipos Electro-Industriales, TICs y Muebles y Enseres', 'error')
                return redirect(url_for('mantenimientos.nueva_hoja_vida'))

            # Crear hoja de vida
            hoja_vida = HojaVidaEquipo(activo_id=activo_id)

            # Características Comerciales
            hoja_vida.proveedor_nombre = request.form.get('proveedor_nombre')
            if request.form.get('fecha_adquisicion'):
                hoja_vida.fecha_adquisicion = datetime.strptime(request.form.get('fecha_adquisicion'), '%Y-%m-%d')
            hoja_vida.costo_adquisicion = float(request.form.get('costo_adquisicion')) if request.form.get('costo_adquisicion') else None
            hoja_vida.numero_factura = request.form.get('numero_factura')
            hoja_vida.numero_orden_compra = request.form.get('numero_orden_compra')
            hoja_vida.garantia_meses = int(request.form.get('garantia_meses')) if request.form.get('garantia_meses') else None
            if request.form.get('fecha_vencimiento_garantia'):
                hoja_vida.fecha_vencimiento_garantia = datetime.strptime(request.form.get('fecha_vencimiento_garantia'), '%Y-%m-%d')
            hoja_vida.vida_util_anios = int(request.form.get('vida_util_anios')) if request.form.get('vida_util_anios') else None

            # Características Técnicas
            hoja_vida.voltaje = request.form.get('voltaje')
            hoja_vida.potencia = request.form.get('potencia')
            hoja_vida.corriente = request.form.get('corriente')
            hoja_vida.frecuencia = request.form.get('frecuencia')
            hoja_vida.dimensiones = request.form.get('dimensiones')
            hoja_vida.peso = request.form.get('peso')
            hoja_vida.color = request.form.get('color')
            hoja_vida.material = request.form.get('material')

            hoja_vida.manual_usuario = request.form.get('manual_usuario') == 'on'
            hoja_vida.manual_servicio = request.form.get('manual_servicio') == 'on'
            hoja_vida.manual_instalacion = request.form.get('manual_instalacion') == 'on'

            # Características Específicas (JSON)
            caracteristicas_especificas = {}
            # Según la clase del activo, capturar campos específicos
            if activo.clase_id == 3:  # TICs
                caracteristicas_especificas = {
                    'sistema_operativo': request.form.get('sistema_operativo'),
                    'procesador': request.form.get('procesador'),
                    'ram': request.form.get('ram'),
                    'disco': request.form.get('disco'),
                    'tipo_equipo': request.form.get('tipo_equipo_tic')
                }
            elif activo.clase_id == 2:  # Electro-Industrial
                caracteristicas_especificas = {
                    'capacidad': request.form.get('capacidad'),
                    'tipo_combustible': request.form.get('tipo_combustible'),
                    'tipo_motor': request.form.get('tipo_motor'),
                    'tipo_refrigerante': request.form.get('tipo_refrigerante')
                }
            elif activo.clase_id == 4:  # Muebles y Enseres
                caracteristicas_especificas = {
                    'tipo_mueble': request.form.get('tipo_mueble'),
                    'numero_cajones': request.form.get('numero_cajones'),
                    'acabado': request.form.get('acabado'),
                    'tapiceria': request.form.get('tapiceria')
                }

            hoja_vida.caracteristicas_especificas_json = caracteristicas_especificas

            # Observaciones
            hoja_vida.observaciones_tecnicas = request.form.get('observaciones_tecnicas')
            hoja_vida.condiciones_uso = request.form.get('condiciones_uso')
            hoja_vida.restricciones = request.form.get('restricciones')

            # Procesar fotos
            fotos_procesadas = procesar_fotos_hoja_vida(request.files, activo.placa_codigo_interno)
            hoja_vida.foto_url = fotos_procesadas.get('foto_1')
            hoja_vida.foto_2_url = fotos_procesadas.get('foto_2')
            hoja_vida.foto_3_url = fotos_procesadas.get('foto_3')

            # Auditoría
            hoja_vida.created_by = current_user.id
            hoja_vida.updated_by = current_user.id

            db.session.add(hoja_vida)
            db.session.commit()

            flash('Hoja de vida creada exitosamente', 'success')
            return redirect(url_for('mantenimientos.ver_hoja_vida', id=hoja_vida.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la hoja de vida: {str(e)}', 'error')
            return redirect(url_for('mantenimientos.nueva_hoja_vida'))

    # GET - Mostrar formulario
    # Obtener activos sin hoja de vida de clases 2, 3, 4
    activos = Activo.query.filter(
        Activo.clase_id.in_([2, 3, 4]),
        ~Activo.id.in_(db.session.query(HojaVidaEquipo.activo_id))
    ).all()

    return render_template("mantenimientos/hojas_vida/nueva_hoja_vida.html",
                         activos=activos,
                         active_page='mantenimientos')


@mantenimientos_bp.route('/hojas_vida/ver/<int:id>')
@login_required
def ver_hoja_vida(id):
    """Muestra los detalles de una hoja de vida."""
    hoja_vida = HojaVidaEquipo.query.get_or_404(id)
    return render_template("mantenimientos/hojas_vida/ver_hoja_vida.html",
                         hoja_vida=hoja_vida,
                         active_page='mantenimientos')


@mantenimientos_bp.route('/hojas_vida/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_hoja_vida(id):
    """Edita una hoja de vida existente."""
    hoja_vida = HojaVidaEquipo.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Actualizar campos (similar a nueva_hoja_vida)
            # ... código de actualización ...

            hoja_vida.updated_by = current_user.id
            hoja_vida.updated_at = datetime.utcnow()

            db.session.commit()
            flash('Hoja de vida actualizada exitosamente', 'success')
            return redirect(url_for('mantenimientos.ver_hoja_vida', id=hoja_vida.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la hoja de vida: {str(e)}', 'error')

    return render_template("mantenimientos/hojas_vida/editar_hoja_vida.html",
                         hoja_vida=hoja_vida,
                         active_page='mantenimientos')


# ==============================================================================
# RUTAS PARA MANTENIMIENTOS
# ==============================================================================

@mantenimientos_bp.route('/gestionar_mantenimientos')
@login_required
def gestionar_mantenimientos():
    """Lista todos los mantenimientos de equipos no biomédicos."""
    # Obtener mantenimientos de activos de clases 2, 3, 4
    mantenimientos = db.session.query(Mantenimiento).join(Activo).filter(
        Activo.clase_id.in_([2, 3, 4])
    ).order_by(Mantenimiento.fecha_mantenimiento.desc()).all()

    return render_template("mantenimientos/gestion/lista_mantenimientos.html",
                         mantenimientos=mantenimientos,
                         active_page='mantenimientos')


@mantenimientos_bp.route('/mantenimientos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_mantenimiento():
    """Página para crear un nuevo mantenimiento (funcionalidad en desarrollo)."""
    # Lógica para el formulario de creación irá aquí
    return render_template("mantenimientos/gestion/nuevo_mantenimiento.html", active_page='mantenimientos')




# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def procesar_fotos_hoja_vida(files, placa_activo):
    """
    Procesa las fotos subidas para una hoja de vida.
    Retorna un diccionario con las URLs de las fotos guardadas.
    """
    from flask import current_app

    fotos_urls = {}
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'hojas_vida_equipos')

    # Crear directorio si no existe
    os.makedirs(upload_folder, exist_ok=True)

    for i in range(1, 4):
        foto_key = f'foto_{i}'
        if foto_key in files:
            file = files[foto_key]
            if file and file.filename:
                # Generar nombre seguro para el archivo
                filename = secure_filename(f"{placa_activo}_foto_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                # Guardar ruta relativa
                fotos_urls[foto_key] = f'uploads/hojas_vida_equipos/{filename}'

    return fotos_urls
