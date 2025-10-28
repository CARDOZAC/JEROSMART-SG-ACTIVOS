import os
import json
import base64
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    session, current_app, make_response
)
from werkzeug.utils import secure_filename
from sqlalchemy import select
import weasyprint
from ..extensions import db
# Asumo que tus modelos están definidos y se pueden importar.
# Necesitaríamos crearlos si no existen.
from ..models import Mantenimiento, Activo, MantenimientoTipo, HojasDeVida, MantenimientoFoto, User

biomedicos_bp = Blueprint(
    "biomedicos",
    __name__,
    template_folder="templates",
    url_prefix="/biomedicos"  # Prefijo para todas las rutas de este blueprint
)

# --------------------------
# Configuración de rutas
# --------------------------
FORMATOS_PATH = os.path.join(os.path.dirname(__file__), "formatos.json")

# =====================================================================
# VISTAS PRINCIPALES (Renderizado de plantillas)
# =====================================================================

@biomedicos_bp.route('/')
def index():
    """Página principal del módulo biomédico que carga el componente React."""
    return render_template("gestion_biomedicos.html", active_page='gestion_biomedicos')

@biomedicos_bp.route("/mantenimientos")
def ver_mantenimientos():
    """Vista para ver la tabla de mantenimientos (puede ser reemplazada por React)."""
    # Versión con SQLAlchemy ORM
    stmt = (
        select(Mantenimiento)
        .join(Activo).join(MantenimientoTipo)
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
    )
    mantenimientos = db.session.execute(stmt).scalars().all()
    return render_template("biomedicos/ver_mantenimientos.html", mantenimientos=mantenimientos, active_page='gestion_biomedicos')

@biomedicos_bp.route("/hojas_vida")
def hojas_de_vida():
    """Vista para ver la tabla de hojas de vida (puede ser reemplazada por React)."""
    database = db.get_db()
    hojas = database.execute("""
        SELECT hv.id, a.nombre_activo, hv.ruta_pdf_fisica, hv.normativa_aplicable
        FROM hojas_de_vida hv
        JOIN activos a ON hv.activo_id = a.id
    """).fetchall()
    return render_template("biomedicos/ver_hojas_vida.html", hojas=hojas, active_page='gestion_biomedicos')

@biomedicos_bp.route('/wizard')
def wizard_mantenimiento_view():
    """Ruta que renderiza el asistente (wizard) HTML."""
    return render_template('wizard_mantenimiento.html', active_page='gestion_biomedicos')

# =====================================================================
# API ENDPOINTS (Para ser consumidos por React)
# =====================================================================

@biomedicos_bp.route("/api/mantenimientos", methods=['GET', 'POST'])
def api_mantenimientos():
    """API para obtener todos los mantenimientos o crear uno nuevo."""
    if request.method == 'GET':
        # Usando el ORM, las relaciones cargan los datos relacionados.
        mantenimientos = db.session.scalars(select(Mantenimiento).order_by(Mantenimiento.fecha_mantenimiento.desc())).all()
        # Creamos los diccionarios para la respuesta JSON
        mantenimientos_list = [
            {
                "id": m.id,
                "nombre_activo": m.activo.nombre_activo,
                "placa_codigo_interno": m.activo.placa_codigo_interno,
                "tipo_reporte": m.tipo.nombre,
                "fecha_mantenimiento": m.fecha_mantenimiento,
                "estado": m.estado
            } for m in mantenimientos
        ]
        return jsonify(mantenimientos_list)

    if request.method == 'POST':
        # Esta ruta ahora espera 'multipart/form-data' por las fotos
        try:
            data = request.form
            activo_id = data.get('activo_id')
            tipo_id = data.get('tipo_id')
            fecha_mantenimiento = data.get('fecha_mantenimiento')
            
            if not all([activo_id, tipo_id, fecha_mantenimiento]):
                return jsonify({"success": False, "message": "Faltan campos obligatorios."}), 400

            nuevo_mantenimiento = Mantenimiento(
                activo_id=activo_id,
                tipo_id=tipo_id,
                fecha_mantenimiento=fecha_mantenimiento,
                duracion_minutos=data.get('duracion_minutos'),
                observaciones=data.get('observaciones'),
                usuario_id=session.get('user_id', 1), # Idealmente usar `current_user.id` de Flask-Login
                estado=data.get('estado', 'Pendiente'),
                atributos_reporte_json=data.get('atributos_reporte_json', '{}')
            )
            db.session.add(nuevo_mantenimiento)
            db.session.flush() # Para obtener el ID antes del commit
            mantenimiento_id = nuevo_mantenimiento.id

            # Lógica para guardar fotos de evidencia
            fotos = request.files.getlist('fotos_evidencia')
            for foto in fotos:
                if foto and foto.filename:
                    filename = secure_filename(f"maint_{mantenimiento_id}_{foto.filename}")
                    filepath = os.path.join(current_app.config['MAINTENANCE_PHOTOS_FOLDER'], filename)
                    foto.save(filepath)
                    ruta_relativa = os.path.join('maintenance_photos', filename)
                    nueva_foto = MantenimientoFoto(
                        mantenimiento_id=mantenimiento_id,
                        ruta_foto=ruta_relativa
                    )
                    db.session.add(nueva_foto)

            db.session.commit()
            return jsonify({"success": True, "id": mantenimiento_id, "message": "Mantenimiento creado con éxito."}), 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear mantenimiento: {e}")
            return jsonify({"success": False, "message": str(e)}), 500


@biomedicos_bp.route("/api/mantenimientos/<int:mantenimiento_id>", methods=['DELETE'])
def api_delete_mantenimiento(mantenimiento_id):
    """API para eliminar un mantenimiento."""
    try:
        # Primero, borrar los archivos de fotos asociados del sistema de archivos
        fotos = database.execute(
            "SELECT ruta_foto FROM mantenimiento_fotos WHERE mantenimiento_id = ?",
            (mantenimiento_id,)
        ).fetchall()

        for foto in fotos:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], foto['ruta_foto']))
            except OSError as e:
                current_app.logger.warning(f"No se pudo borrar el archivo {foto['ruta_foto']}: {e}")

        # Con SQLAlchemy, obtenemos el objeto y lo borramos.
        # La configuración `cascade="all, delete-orphan"` en el modelo se encargará de borrar las fotos.
        mantenimiento = db.session.get(Mantenimiento, mantenimiento_id)

        if not mantenimiento:
            return jsonify({"success": False, "message": "Mantenimiento no encontrado."}), 404

        db.session.delete(mantenimiento)
        db.session.commit()
        return jsonify({"success": True, "message": "Mantenimiento eliminado con éxito."})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar mantenimiento {mantenimiento_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@biomedicos_bp.route("/api/activos-biomedicos")
def api_activos_biomedicos():
    """API para buscar activos de la clase 'Equipo Biomédico' (clase_id=1)."""
    query = request.args.get('q', '')
    search_term = f'%{query}%'
    
    # Asumimos que la clase 'Equipo Biomédico' tiene el id 1
    # Versión con SQLAlchemy
    stmt = (
        select(Activo.id, Activo.nombre_activo, Activo.placa_codigo_interno, Activo.serie, Activo.ubicacion)
        .where(Activo.clase_id == 1)
        .where( (Activo.nombre_activo.ilike(search_term)) | (Activo.placa_codigo_interno.ilike(search_term)) | (Activo.serie.ilike(search_term)) )
        .limit(10)
    )
    activos = db.session.execute(stmt).mappings().all()
    
    return jsonify([dict(row) for row in activos]) # .mappings() ya devuelve dict-like objects


@biomedicos_bp.route("/api/mantenimiento-tipos")
def api_mantenimiento_tipos():
    """API para obtener los tipos de reportes de mantenimiento."""
    # Versión con SQLAlchemy
    tipos = db.session.scalars(select(MantenimientoTipo).order_by(MantenimientoTipo.nombre)).all()
    return jsonify([{"id": t.id, "nombre": t.nombre} for t in tipos])


@biomedicos_bp.route('/api/formatos-mantenimiento', methods=['GET'])
def get_formatos_mantenimiento():
    """
    Lee el archivo formatos.json y lo devuelve. Esta es la fuente de verdad
    para los campos dinámicos del wizard en el frontend.
    """
    try:
        with open(FORMATOS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "El archivo de formatos (formatos.json) no fue encontrado."}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error al decodificar formatos.json. Verifique la sintaxis."}), 500
    except Exception as e:
        current_app.logger.error(f"Error cargando formatos.json: {e}")
        return jsonify({"error": str(e)}), 500

# =====================================================================
# API ENDPOINTS - HOJAS DE VIDA
# =====================================================================

@biomedicos_bp.route('/api/hojas-vida', methods=['GET', 'POST'])
def api_hojas_vida():
    """API para listar o crear Hojas de Vida."""
    if request.method == 'GET':
        # Con SQLAlchemy, podemos hacer un LEFT JOIN y construir el resultado
        stmt = (
            select(Activo, HojasDeVida)
            .outerjoin(HojasDeVida, Activo.id == HojasDeVida.activo_id)
            .where(Activo.clase_id == 1) # Solo equipos biomédicos
            .order_by(Activo.nombre_activo)
        )
        results = db.session.execute(stmt).all()
        hojas_list = [
            {"id": hv.id if hv else None, "activo_id": a.id, "normativa_aplicable": hv.normativa_aplicable if hv else None,
             "nombre_activo": a.nombre_activo, "placa_codigo_interno": a.placa_codigo_interno,
             "tiene_hoja_vida": 1 if hv else 0} for a, hv in results
        ]
        return jsonify(hojas_list)

    if request.method == 'POST':
        try:
            activo_id = request.form.get('activo_id')
            normativa = request.form.get('normativa_aplicable')
            if not activo_id:
                return jsonify({"success": False, "message": "Se requiere un activo."}), 400
            
            # Manejo de subida de archivos
            ruta_pdf = None
            pdf_file = request.files.get('hoja_vida_pdf')
            if pdf_file and pdf_file.filename:
                filename = secure_filename(f"hdv_{activo_id}_{pdf_file.filename}")
                filepath = os.path.join(current_app.config['HOJAS_DE_VIDA_FOLDER'], filename)
                pdf_file.save(filepath)
                ruta_pdf = os.path.join('hojas_de_vida', filename)

            ruta_foto = None
            foto_file = request.files.get('foto_activo')
            if foto_file and foto_file.filename:
                filename = secure_filename(f"foto_{activo_id}_{foto_file.filename}")
                filepath = os.path.join(current_app.config['HOJAS_DE_VIDA_FOLDER'], filename)
                foto_file.save(filepath)
                ruta_foto = os.path.join('hojas_de_vida', filename)

            nueva_hdv = HojasDeVida(
                activo_id=activo_id,
                normativa_aplicable=normativa,
                ruta_pdf_fisica=ruta_pdf,
                ruta_foto_activo=ruta_foto
            )
            db.session.add(nueva_hdv)
            db.session.commit()
            return jsonify({"success": True, "message": "Hoja de Vida creada con éxito."}), 201

        except exc.IntegrityError: # Excepción de SQLAlchemy para violaciones de integridad
            db.session.rollback()
            return jsonify({"success": False, "message": "Este activo ya tiene una Hoja de Vida."}), 409
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear Hoja de Vida: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

@biomedicos_bp.route('/api/hojas-vida/<int:hdv_id>', methods=['DELETE'])
def api_delete_hoja_vida(hdv_id):
    """API para eliminar una Hoja de Vida."""
    try:
        hdv = db.session.get(HojasDeVida, hdv_id)
        if not hdv:
            return jsonify({"success": False, "message": "Hoja de Vida no encontrada."}), 404

        # Borrar archivos asociados
        for ruta in [hdv['ruta_pdf_fisica'], hdv['ruta_foto_activo']]:
            if ruta:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], ruta))
                except OSError as e:
                    current_app.logger.warning(f"No se pudo borrar el archivo {ruta}: {e}")

        db.session.delete(hdv)
        db.session.commit()
        return jsonify({"success": True, "message": "Hoja de Vida eliminada con éxito."})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar Hoja de Vida {hdv_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


def get_file_base64(ruta_relativa):
    """Función helper para convertir un archivo a base64 para el PDF."""
    if not ruta_relativa:
        return None
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], ruta_relativa)
        with open(full_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except (FileNotFoundError, TypeError):
        return None

@biomedicos_bp.route('/api/hojas-vida/<int:hdv_id>/pdf')
def api_generar_pdf_consolidado(hdv_id):
    """
    Genera un PDF consolidado para una Hoja de Vida, incluyendo
    datos del activo, mantenimientos y todas las evidencias.
    """
    # 1. Obtener datos de la Hoja de Vida y del Activo
    # Con el ORM, si la relación está bien definida, al obtener la hoja de vida,
    # podemos acceder al activo directamente.
    hoja_de_vida = db.session.get(HojasDeVida, hdv_id)

    if not hoja_de_vida:
        return render_template('pdf_templates/pdf_error.html', message="Hoja de Vida no encontrada."), 404

    activo = hoja_de_vida.activo # Accedemos al activo a través de la relación

    # 2. Obtener todos los mantenimientos asociados al activo
    # El activo debería tener una relación `mantenimientos`
    mantenimientos = sorted(activo.mantenimientos, key=lambda m: m.fecha_mantenimiento, reverse=True)

    # 3. Para cada mantenimiento, obtener sus fotos y convertirlas a base64
    mantenimientos_con_fotos = []
    for mant in mantenimientos:
        # Creamos un diccionario a partir del objeto para pasarlo a la plantilla
        mant_dict = {
            "id": mant.id, "fecha_mantenimiento": mant.fecha_mantenimiento,
            "observaciones": mant.observaciones, "estado": mant.estado,
            "tipo_reporte": mant.tipo.nombre, "usuario_registra": mant.usuario.email,
            "atributos_reporte_json": mant.atributos_reporte_json,
            # ... otros campos que necesites ...
        }
        fotos_base64 = []
        # Accedemos a las fotos a través de la relación `fotos` del mantenimiento
        for foto in mant.fotos:
            b64 = get_file_base64(foto.ruta_foto)
            if b64:
                fotos_base64.append(b64)
        mant_dict['fotos_evidencia_b64'] = fotos_base64
        mantenimientos_con_fotos.append(mant_dict)

    # 4. Preparar datos para la plantilla
    data_for_template = {
        "hoja_de_vida": hoja_de_vida, # Pasamos el objeto directamente
        "activo": activo, # Pasamos el objeto activo también
        "mantenimientos": mantenimientos_con_fotos,
        "foto_activo_b64": get_file_base64(hoja_de_vida.ruta_foto_activo),
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 5. Renderizar el HTML y generar el PDF
    try:
        html = render_template('pdf_templates/hoja_vida_consolidada.html', **data_for_template)
        
        # WeasyPrint no puede acceder directamente a los archivos del sistema por seguridad.
        # Por eso usamos base64 para las imágenes. Para el PDF físico, lo adjuntaremos.
        # (La adjunción de PDFs es una característica avanzada, por ahora lo omitimos y nos centramos en la visualización)
        
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="HdV_{activo.placa_codigo_interno}.pdf"'
        return response

    except Exception as e:
        current_app.logger.error(f"Error generando PDF consolidado para HDV {hdv_id}: {e}")
        return render_template('pdf_templates/pdf_error.html', message=str(e)), 500
