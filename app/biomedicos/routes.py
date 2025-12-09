import os
import json
import hashlib
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    flash,
    session,
    current_app,
    make_response,
    redirect,
    url_for,
    send_file,
    send_from_directory,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from sqlalchemy import select, or_, and_
import weasyprint
from ..extensions import db
from app.models import (
    Activo,
    MantenimientoTipo,
    HojaVidaBiomedico,
    MantenimientoFoto,
    Mantenimiento,
    DocumentoAdjunto,
    MantenimientoDocumento,
)
from .context_builders import (
    build_hoja_vida_pdf_context,
    build_mantenimiento_pdf_context,
)
from .forms import CargarHistoricoBiomedicoForm
from . import biomedicos_bp


def _convert_to_date(date_str):
    """
    Convierte una cadena de fecha a objeto date.
    Lanza ValueError si el formato es inválido para que el error sea manejado explícitamente.
    """
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            current_app.logger.error(f"Formato de fecha inválido: {date_str}")
            raise ValueError(
                f"Formato de fecha inválido '{date_str}'. Use el formato YYYY-MM-DD."
            ) from e
    return None


# =====================================================================
# VISTAS PRINCIPALES (Renderizado de plantillas)
# =====================================================================


@biomedicos_bp.route("/")
def index():
    """Página principal del módulo biomédico con el historial de mantenimientos."""
    return render_template(
        "gestion_biomedicos.html", active_page="historial_mantenimientos"
    )


@biomedicos_bp.route("/mantenimientos")
def mantenimientos():
    """Página de gestión de mantenimientos de equipos biomédicos."""
    # Estados para mantenimientos pendientes y en proceso
    estados_pendientes = ["Programado", "En Proceso"]
    # Estados para mantenimientos históricos
    estados_historicos = ["Completado", "Cancelado"]

    # Consulta para mantenimientos pendientes
    mantenimientos_pendientes = db.session.scalars(
        select(Mantenimiento)
        .join(Mantenimiento.activo)
        .where(Activo.clase_id == 1, Mantenimiento.estado.in_(estados_pendientes))
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
    ).all()

    # Consulta para mantenimientos históricos
    mantenimientos_historicos = db.session.scalars(
        select(Mantenimiento)
        .join(Mantenimiento.activo)
        .where(Activo.clase_id == 1, Mantenimiento.estado.in_(estados_historicos))
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
    ).all()

    return render_template(
        "biomedicos/mantenimientos.html",
        active_page="mantenimientos",
        mantenimientos_pendientes=mantenimientos_pendientes,
        mantenimientos_historicos=mantenimientos_historicos,
    )


@biomedicos_bp.route("/mantenimiento/wizard")
def wizard_mantenimiento():
    """Wizard para crear nuevo mantenimiento."""
    return render_template(
        "biomedicos/mantenimientos/wizard_mantenimiento.html",
        active_page="mantenimientos",
    )


@biomedicos_bp.route("/cargar_historico", methods=["GET", "POST"])
def cargar_historico_biomedico():
    """Carga un PDF de un mantenimiento histórico para un equipo biomédico."""
    form = CargarHistoricoBiomedicoForm()

    if form.validate_on_submit():
        try:
            # 1. Obtener o crear el tipo de mantenimiento 'Histórico'
            tipo_historico = MantenimientoTipo.query.filter_by(
                nombre="Histórico"
            ).first()
            if not tipo_historico:
                tipo_historico = MantenimientoTipo(
                    nombre="Histórico",
                    descripcion="Mantenimiento cargado desde un documento histórico.",
                )
                db.session.add(tipo_historico)
                db.session.flush()

            # 2. Crear el registro de mantenimiento
            mantenimiento = Mantenimiento(
                activo_id=form.activo_id.data.id,
                tipo_id=tipo_historico.id,
                fecha_mantenimiento=form.fecha_mantenimiento.data,
                estado="Completado",
                observaciones=form.observaciones.data
                or "Mantenimiento histórico biomédico cargado desde PDF.",
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.session.add(mantenimiento)
            db.session.flush()

            # 3. Validar y guardar el archivo PDF
            archivo = form.documento.data

            # --- Validación de contenido de archivo ---
            import magic

            archivo.seek(0)
            mime_type = magic.from_buffer(archivo.read(2048), mime=True)
            archivo.seek(0)

            if mime_type != "application/pdf":
                flash(
                    f"El contenido del archivo no es un PDF válido (detectado: {mime_type}).",
                    "error",
                )
                # Recargar el formulario para que el usuario pueda corregir
                return render_template(
                    "biomedicos/cargar_historico.html",
                    form=form,
                    active_page="mantenimientos",
                )

            extension = archivo.filename.rsplit(".", 1)[-1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            placa = mantenimiento.activo.placa_codigo_interno or "SIN_PLACA"
            nombre_seguro = secure_filename(
                f"mant_bio_hist_{mantenimiento.id}_{placa}_{timestamp}.{extension}"
            )

            upload_folder = os.path.join(
                current_app.root_path, "static", "uploads", "mantenimientos_documentos"
            )
            os.makedirs(upload_folder, exist_ok=True)

            ruta_completa = os.path.join(upload_folder, nombre_seguro)
            archivo.save(ruta_completa)
            tamano = os.path.getsize(ruta_completa)

            # 4. Crear el registro del documento
            documento = MantenimientoDocumento(
                mantenimiento_id=mantenimiento.id,
                nombre_archivo=archivo.filename,
                ruta_archivo=f"uploads/mantenimientos_documentos/{nombre_seguro}",
                tipo_documento="pdf",
                tamano_archivo=tamano,
                fecha_documento=form.fecha_mantenimiento.data,
                descripcion="Documento de mantenimiento histórico biomédico.",
                uploaded_by=current_user.id,
            )
            db.session.add(documento)
            db.session.commit()

            flash(
                f'Mantenimiento histórico biomédico para "{form.activo_id.data.nombre_activo}" cargado exitosamente.',
                "success",
            )
            return redirect(url_for("biomedicos.mantenimientos"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al cargar el mantenimiento histórico: {str(e)}", "error")

    return render_template(
        "biomedicos/cargar_historico.html", form=form, active_page="mantenimientos"
    )


@biomedicos_bp.route("/mantenimiento/detalle/<int:mantenimiento_id>")
def detalle_mantenimiento(mantenimiento_id):
    """Vista de detalle de un mantenimiento."""
    # Buscar el mantenimiento con eager loading
    mantenimiento = db.session.scalar(
        select(Mantenimiento)
        .options(
            db.joinedload(Mantenimiento.activo).joinedload(Activo.clase),
            db.joinedload(Mantenimiento.tipo),
        )
        .where(Mantenimiento.id == mantenimiento_id)
    )

    if not mantenimiento:
        flash("Mantenimiento no encontrado", "error")
        return redirect(url_for("biomedicos.mantenimientos"))

    # Usar el context builder para preparar los datos
    context = build_mantenimiento_pdf_context(mantenimiento)

    # Renderizar la plantilla con el contexto preparado
    return render_template(
        "biomedicos/mantenimientos/detalle_mantenimiento.html",
        active_page="mantenimientos",
        mantenimiento=mantenimiento,
        activo=context["activo"],
        reporte_tecnico=context["reporte_tecnico"],
        accesorios=context["accesorios"],
        firma_tecnico=context["firma_tecnico"],
        firma_responsable=context["firma_responsable"],
    )


@biomedicos_bp.route("/mantenimiento/editar/<int:mantenimiento_id>")
def editar_mantenimiento(mantenimiento_id):
    """Editar mantenimiento existente (reutiliza el wizard en modo edición)."""
    # Buscar el mantenimiento con eager loading
    mantenimiento = db.session.scalar(
        select(Mantenimiento)
        .options(
            db.joinedload(Mantenimiento.activo).joinedload(Activo.clase),
            db.joinedload(Mantenimiento.tipo),
        )
        .where(Mantenimiento.id == mantenimiento_id)
    )

    if not mantenimiento:
        flash("Mantenimiento no encontrado", "error")
        return redirect(url_for("biomedicos.mantenimientos"))

    # Parsear el reporte técnico JSON
    import json

    reporte_tecnico = {}
    if mantenimiento.atributos_reporte_json:
        try:
            reporte_tecnico = json.loads(mantenimiento.atributos_reporte_json)
        except (json.JSONDecodeError, TypeError):
            current_app.logger.warning(
                f"Error al parsear JSON del mantenimiento {mantenimiento_id}"
            )
            reporte_tecnico = {}

    # Serializar datos del mantenimiento para JavaScript
    mantenimiento_data = {
        "id": mantenimiento.id,
        "activo_id": mantenimiento.activo_id,
        "activo_placa": mantenimiento.activo.placa_codigo_interno,
        "activo_nombre": mantenimiento.activo.nombre_activo,
        "tipo_mantenimiento_id": mantenimiento.tipo_mantenimiento_id,
        "tipo_nombre": (
            mantenimiento.tipo.nombre.lower() if mantenimiento.tipo else "preventivo"
        ),
        "fecha_mantenimiento": (
            mantenimiento.fecha_mantenimiento.strftime("%Y-%m-%d")
            if mantenimiento.fecha_mantenimiento
            else ""
        ),
        "duracion_minutos": mantenimiento.duracion_minutos or "",
        "estado": mantenimiento.estado or "Programado",
        "observaciones": mantenimiento.observaciones or "",
        # Reporte técnico
        "reporte_tecnico": reporte_tecnico,
    }

    # Pasar al wizard con los datos serializados
    return render_template(
        "biomedicos/mantenimientos/wizard_mantenimiento.html",
        active_page="mantenimientos",
        modo_edicion=True,
        mantenimiento_data=mantenimiento_data,
    )


@biomedicos_bp.route("/reportes")
def reportes():
    """Página de reportes de mantenimientos."""
    return render_template("biomedicos/reportes.html", active_page="reportes")


@biomedicos_bp.route("/hojas-vida")
def ver_hojas_vida():
    """Vista principal de gestión de hojas de vida."""
    return render_template(
        "biomedicos/hojas_vida/ver_hojas_vida.html", active_page="hojas_vida"
    )


@biomedicos_bp.route("/hoja-vida/crear-wizard/<int:activo_id>")
def crear_hoja_de_vida_wizard(activo_id):
    """Muestra el wizard para crear una nueva hoja de vida de equipo biomédico."""
    return render_template(
        "crear_hoja_de_vida_wizard.html",
        active_page="crear_hoja_de_vida",
        activo_id=activo_id,
    )


@biomedicos_bp.route("/hoja-vida/wizard")
def wizard_hoja_vida():
    """Wizard para crear nueva hoja de vida (sin activo preseleccionado)."""
    return render_template(
        "biomedicos/hojas_vida/wizard_hoja_vida.html", active_page="crear_hoja_de_vida"
    )


@biomedicos_bp.route("/hoja-vida/detalle/<int:activo_id>")
def detalle_hoja_vida(activo_id):
    """Vista de detalle de una hoja de vida existente."""
    # Buscar el activo
    activo = db.session.get(Activo, activo_id)
    if not activo:
        flash("Activo no encontrado", "error")
        return redirect(url_for("biomedicos.ver_hojas_vida"))

    # Buscar la hoja de vida
    hoja_vida = db.session.scalar(
        select(HojaVidaBiomedico)
        .options(
            db.joinedload(HojaVidaBiomedico.documentos),
            db.joinedload(HojaVidaBiomedico.mantenimientos),
        )
        .where(HojaVidaBiomedico.activo_id == activo_id)
    )

    if not hoja_vida:
        flash("Este activo no tiene hoja de vida", "warning")
        return redirect(url_for("biomedicos.wizard_hoja_vida"))

    return render_template(
        "biomedicos/hojas_vida/detalle_hoja_vida.html",
        active_page="hojas_vida",
        activo=activo,
        hoja_vida=hoja_vida,
    )


@biomedicos_bp.route("/hoja-vida/editar/<int:activo_id>")
def editar_hoja_vida(activo_id):
    """Editar hoja de vida existente (reutiliza el wizard en modo edición)."""
    # Buscar el activo
    activo = db.session.get(Activo, activo_id)
    if not activo:
        flash("Activo no encontrado", "error")
        return redirect(url_for("biomedicos.ver_hojas_vida"))

    # Buscar la hoja de vida con eager loading
    hoja_vida = db.session.scalar(
        select(HojaVidaBiomedico)
        .options(
            db.joinedload(HojaVidaBiomedico.documentos),
            db.joinedload(HojaVidaBiomedico.mantenimientos),
        )
        .where(HojaVidaBiomedico.activo_id == activo_id)
    )

    if not hoja_vida:
        flash("Este activo no tiene hoja de vida para editar", "warning")
        return redirect(url_for("biomedicos.wizard_hoja_vida"))

    # Serializar datos de la hoja de vida para JavaScript
    hoja_vida_data = {
        "activo_id": activo_id,
        "permiso_comercializacion": hoja_vida.permiso_comercializacion or "",
        "n_factura": hoja_vida.n_factura or "",
        "n_orden_compra": hoja_vida.n_orden_compra or "",
        "fecha_fabricacion": (
            hoja_vida.fecha_fabricacion.strftime("%Y-%m-%d")
            if hoja_vida.fecha_fabricacion
            else ""
        ),
        "fecha_instalacion": (
            hoja_vida.fecha_instalacion.strftime("%Y-%m-%d")
            if hoja_vida.fecha_instalacion
            else ""
        ),
        "distribuidor": hoja_vida.distribuidor or "",
        "forma_adquisicion": hoja_vida.forma_adquisicion or "",
        "telefono": hoja_vida.telefono or "",
        "correo_electronico": hoja_vida.correo_electronico or "",
        "fecha_ingreso": (
            hoja_vida.fecha_ingreso.strftime("%Y-%m-%d")
            if hoja_vida.fecha_ingreso
            else ""
        ),
        "vencimiento_garantia": (
            hoja_vida.vencimiento_garantia.strftime("%Y-%m-%d")
            if hoja_vida.vencimiento_garantia
            else ""
        ),
        "costo": str(hoja_vida.costo) if hoja_vida.costo else "",
        "vida_util_anios": (
            str(hoja_vida.vida_util_anios) if hoja_vida.vida_util_anios else ""
        ),
        "voltaje": hoja_vida.voltaje or "",
        "frecuencia": hoja_vida.frecuencia or "",
        "dimensiones": hoja_vida.dimensiones or "",
        "corriente": hoja_vida.corriente or "",
        "potencia": hoja_vida.potencia or "",
        "peso": hoja_vida.peso or "",
        "equipo_fijo_movil": hoja_vida.equipo_fijo_movil or "",
        "humedad_relativa": hoja_vida.humedad_relativa or "",
        "temperatura_trabajo": hoja_vida.temperatura_trabajo or "",
        "manual_usuario": hoja_vida.manual_usuario,
        "manual_servicio": hoja_vida.manual_servicio,
        "clasificacion_riesgo": hoja_vida.clasificacion_riesgo or "",
        "clasificacion_biomedica": hoja_vida.clasificacion_biomedica or "",
        "periodicidad_mantenimiento": hoja_vida.periodicidad_mantenimiento or "",
        "requiere_calibracion": hoja_vida.requiere_calibracion,
        "periodicidad_metrologia": hoja_vida.periodicidad_metrologia or "",
    }

    return render_template(
        "biomedicos/hojas_vida/editar_hoja_vida.html",
        active_page="hojas_vida",
        activo=activo,
        hoja_vida=hoja_vida,
        hoja_vida_data=hoja_vida_data,
    )


@biomedicos_bp.route("/api/documento/<int:doc_id>/descargar")
def descargar_documento(doc_id):
    """Descarga un documento adjunto."""
    documento = db.session.get(DocumentoAdjunto, doc_id)

    if not documento:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    try:
        # Construir ruta completa del archivo
        ruta_completa = os.path.join(
            current_app.root_path, "..", documento.ruta_archivo
        )

        if not os.path.exists(ruta_completa):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Archivo no encontrado en el servidor",
                    }
                ),
                404,
            )

        return send_file(
            ruta_completa,
            as_attachment=True,
            download_name=documento.nombre_archivo_original,
            mimetype=documento.mime_type or "application/pdf",
        )
    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error al descargar: {str(e)}"}),
            500,
        )


# =====================================================================
# API ENDPOINTS (Para ser consumidos por React)
# =====================================================================


@biomedicos_bp.route("/api/mantenimientos", methods=["GET", "POST"])
def api_mantenimientos():
    """API para obtener todos los mantenimientos o crear uno nuevo."""
    if request.method == "GET":
        # Consulta usando SQLAlchemy ORM con carga anticipada (eager loading)
        stmt = (
            select(Mantenimiento)
            .options(
                db.joinedload(Mantenimiento.activo), db.joinedload(Mantenimiento.tipo)
            )
            .order_by(Mantenimiento.fecha_mantenimiento.desc())
        )
        mantenimientos = db.session.execute(stmt).scalars().all()

        # Usar relaciones para acceder a datos relacionados
        mantenimientos_list = [
            {
                "id": m.id,
                "nombre_activo": m.activo.nombre_activo,
                "placa_codigo_interno": m.activo.placa_codigo_interno,
                "tipo_reporte": m.tipo.nombre,
                "fecha_mantenimiento": m.fecha_mantenimiento,
                "estado": m.estado,
            }
            for m in mantenimientos
        ]
        return jsonify(mantenimientos_list)

    if request.method == "POST":
        try:
            data = request.form
            mantenimiento_id_edit = data.get(
                "mantenimiento_id"
            )  # Si existe, es edición
            activo_id = data.get("activo_id")
            tipo_id = data.get("tipo_id")
            fecha_mantenimiento = data.get("fecha_mantenimiento")

            if not all([activo_id, tipo_id, fecha_mantenimiento]):
                return (
                    jsonify(
                        {"success": False, "message": "Faltan campos obligatorios."}
                    ),
                    400,
                )

            # Determinar si es creación o actualización
            if mantenimiento_id_edit:
                # MODO EDICIÓN: Actualizar mantenimiento existente
                mantenimiento = db.session.get(
                    Mantenimiento, int(mantenimiento_id_edit)
                )
                if not mantenimiento:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": "Mantenimiento no encontrado.",
                            }
                        ),
                        404,
                    )

                # Actualizar campos
                mantenimiento.activo_id = activo_id
                mantenimiento.tipo_mantenimiento_id = tipo_id
                mantenimiento.fecha_mantenimiento = datetime.strptime(
                    fecha_mantenimiento, "%Y-%m-%d"
                ).date()
                mantenimiento.duracion_minutos = data.get("duracion_minutos")
                mantenimiento.observaciones = data.get("observaciones")
                mantenimiento.estado = data.get("estado", mantenimiento.estado)
                mantenimiento.atributos_reporte_json = data.get(
                    "atributos_reporte_json", "{}"
                )

                mantenimiento_id = mantenimiento.id
                mensaje = "Mantenimiento actualizado con éxito."

            else:
                # MODO CREACIÓN: Crear nuevo mantenimiento
                nuevo_mantenimiento = Mantenimiento(
                    activo_id=activo_id,
                    tipo_mantenimiento_id=tipo_id,
                    fecha_mantenimiento=datetime.strptime(
                        fecha_mantenimiento, "%Y-%m-%d"
                    ).date(),
                    duracion_minutos=data.get("duracion_minutos"),
                    observaciones=data.get("observaciones"),
                    usuario_id=session.get("user_id", 1),
                    estado=data.get("estado", "Programado"),
                    atributos_reporte_json=data.get("atributos_reporte_json", "{}"),
                )

                # Añadir a la sesión
                db.session.add(nuevo_mantenimiento)
                db.session.flush()  # Para obtener el ID antes del commit
                mantenimiento_id = nuevo_mantenimiento.id
                mensaje = "Mantenimiento creado con éxito."

            # Guardar fotos de evidencia (solo en creación, por ahora)
            if not mantenimiento_id_edit:
                fotos = request.files.getlist("fotos_evidencia")
                for foto in fotos:
                    if foto and foto.filename:
                        # --- Validación de contenido de archivo ---
                        import magic

                        allowed_mimes = ["image/jpeg", "image/png", "image/gif"]

                        foto.seek(0)
                        mime_type = magic.from_buffer(foto.read(2048), mime=True)
                        foto.seek(0)

                        if mime_type not in allowed_mimes:
                            # Esto es un endpoint de API, así que se lanza un error que se capturará
                            # y se devolverá como JSON.
                            raise ValueError(
                                f"El archivo '{foto.filename}' no es una imagen válida (detectado: {mime_type})."
                            )
                        # --- Fin de la validación ---

                        filename = secure_filename(
                            f"maint_{mantenimiento_id}_{foto.filename}"
                        )
                        filepath = os.path.join(
                            current_app.config["MAINTENANCE_PHOTOS_FOLDER"], filename
                        )
                        foto.save(filepath)
                        ruta_relativa = os.path.join("maintenance_photos", filename)

                        # Crear instancia de foto
                        nueva_foto = MantenimientoFoto(
                            mantenimiento_id=mantenimiento_id, ruta_foto=ruta_relativa
                        )
                        db.session.add(nueva_foto)

            # Confirmar transacción
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "mantenimiento_id": mantenimiento_id,
                    "message": mensaje,
                }
            ), (200 if mantenimiento_id_edit else 201)

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error al guardar mantenimiento: {e}", exc_info=True
            )
            return jsonify({"success": False, "message": str(e)}), 500


@biomedicos_bp.route(
    "/api/mantenimientos/<int:mantenimiento_id>", methods=["GET", "PUT"]
)
def api_update_mantenimiento(mantenimiento_id):
    """API para obtener o editar un registro de mantenimiento existente."""
    mantenimiento = db.session.get(Mantenimiento, mantenimiento_id)

    if not mantenimiento:
        return (
            jsonify({"success": False, "message": "Mantenimiento no encontrado."}),
            404,
        )

    if request.method == "GET":
        # Serializar datos para el formulario de edición
        mantenimiento_data = {
            "id": mantenimiento.id,
            "activo_id": mantenimiento.activo_id,
            "nombre_activo": mantenimiento.activo.nombre_activo,
            "placa_codigo_interno": mantenimiento.activo.placa_codigo_interno,
            "tipo_id": mantenimiento.tipo_id,
            "fecha_mantenimiento": (
                mantenimiento.fecha_mantenimiento.strftime("%Y-%m-%d")
                if mantenimiento.fecha_mantenimiento
                else None
            ),
            "duracion_minutos": mantenimiento.duracion_minutos,
            "observaciones": mantenimiento.observaciones,
            "estado": mantenimiento.estado,
            "atributos_reporte_json": mantenimiento.atributos_reporte_json,
        }
        return jsonify(mantenimiento_data)

    if request.method == "PUT":
        try:
            data = request.form

            # Actualizar campos del mantenimiento desde el formulario
            mantenimiento.tipo_id = data.get("tipo_id", mantenimiento.tipo_id)

            fecha_str = data.get("fecha_mantenimiento")
            if fecha_str:
                mantenimiento.fecha_mantenimiento = datetime.strptime(
                    fecha_str, "%Y-%m-%d"
                ).date()

            mantenimiento.observaciones = data.get(
                "observaciones", mantenimiento.observaciones
            )
            mantenimiento.estado = data.get("estado", mantenimiento.estado)

            db.session.commit()
            return jsonify(
                {"success": True, "message": "Mantenimiento actualizado con éxito."}
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error al actualizar mantenimiento {mantenimiento_id}: {e}"
            )
            return jsonify({"success": False, "message": str(e)}), 500


@biomedicos_bp.route("/api/mantenimientos/<int:mantenimiento_id>", methods=["DELETE"])
def api_delete_mantenimiento(mantenimiento_id):
    """API para eliminar un mantenimiento."""
    try:
        mantenimiento = db.session.get(Mantenimiento, mantenimiento_id)

        if not mantenimiento:
            return (
                jsonify({"success": False, "message": "Mantenimiento no encontrado."}),
                404,
            )

        # Borrar archivos físicos antes de eliminar el registro
        for foto in mantenimiento.fotos:
            try:
                filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], foto.ruta_foto
                )
                if os.path.exists(filepath):
                    os.remove(filepath)
            except OSError as e:
                current_app.logger.warning(
                    f"No se pudo borrar el archivo {foto.ruta_foto}: {e}"
                )

        # Eliminar de la sesión (cascade se encargará de las fotos)
        db.session.delete(mantenimiento)
        db.session.commit()
        return jsonify(
            {"success": True, "message": "Mantenimiento eliminado con éxito."}
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error al eliminar mantenimiento {mantenimiento_id}: {e}"
        )
        return jsonify({"success": False, "message": str(e)}), 500


@biomedicos_bp.route("/api/activos-biomedicos")
def api_activos_biomedicos():
    """API para buscar activos de la clase 'Equipo Biomédico'."""
    query = request.args.get("q", "")
    search_term = f"%{query}%"

    # Consulta usando SQLAlchemy ORM
    stmt = (
        select(Activo)
        .where(Activo.clase_id == 1)  # Asumimos que clase_id=1 es Equipo Biomédico
        .where(
            or_(
                Activo.nombre_activo.ilike(search_term),
                Activo.placa_codigo_interno.ilike(search_term),
                Activo.serie.ilike(search_term),
            )
        )
        .limit(10)
    )
    activos = db.session.execute(stmt).scalars().all()

    # Construir lista de resultados
    activos_list = [
        {
            "id": a.id,
            "nombre_activo": a.nombre_activo,
            "placa_codigo_interno": a.placa_codigo_interno,
            "serie": a.serie,
            "ubicacion": a.ubicacion,
        }
        for a in activos
    ]

    return jsonify(activos_list)


@biomedicos_bp.route("/api/mantenimiento-tipos")
def api_mantenimiento_tipos():
    """API para obtener los tipos de reportes de mantenimiento."""
    stmt = select(MantenimientoTipo).order_by(MantenimientoTipo.nombre)
    tipos = db.session.execute(stmt).scalars().all()

    tipos_list = [{"id": t.id, "nombre": t.nombre} for t in tipos]
    return jsonify(tipos_list)


@biomedicos_bp.route("/api/reporte-formatos")
def api_reporte_formatos():
    """
    API para obtener los formatos de reporte de mantenimiento desde formatos.json.
    Esto permite que los formatos sean gestionados en el backend.
    """
    try:
        formatos_path = os.path.join(os.path.dirname(__file__), "formatos.json")
        with open(formatos_path, "r", encoding="utf-8") as f:
            formatos_data = json.load(f)
        return jsonify(formatos_data)
    except FileNotFoundError:
        return jsonify({"error": "El archivo de formatos no fue encontrado."}), 404
    except Exception as e:
        return jsonify({"error": f"Error al leer los formatos: {str(e)}"}), 500


# =====================================================================
# API ENDPOINTS - REPORTES
# =====================================================================


@biomedicos_bp.route("/api/reportes/mantenimientos", methods=["GET"])
def api_reporte_mantenimientos_por_fecha():
    """
    Devuelve un JSON con los mantenimientos en un rango de fechas.
    Acepta parámetros ?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD.
    """
    fecha_inicio_str = request.args.get("fecha_inicio")
    fecha_fin_str = request.args.get("fecha_fin")

    stmt = (
        select(Mantenimiento)
        .options(db.joinedload(Mantenimiento.activo), db.joinedload(Mantenimiento.tipo))
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
    )

    # Aplicar filtros de fecha si se proporcionan
    if fecha_inicio_str:
        stmt = stmt.where(Mantenimiento.fecha_mantenimiento >= fecha_inicio_str)
    if fecha_fin_str:
        stmt = stmt.where(Mantenimiento.fecha_mantenimiento <= fecha_fin_str)

    mantenimientos = db.session.execute(stmt).scalars().all()

    reporte_list = [
        {
            "id": m.id,
            "nombre_activo": m.activo.nombre_activo,
            "placa_codigo_interno": m.activo.placa_codigo_interno,
            "tipo_reporte": m.tipo.nombre,
            "fecha_mantenimiento": m.fecha_mantenimiento,
            "estado": m.estado,
            "responsable": m.usuario.email if m.usuario else "N/A",
        }
        for m in mantenimientos
    ]

    return jsonify(reporte_list)


# =====================================================================
# API ENDPOINTS - HOJAS DE VIDA
# =====================================================================


@biomedicos_bp.route("/api/hojas-vida", methods=["GET", "POST"])
def api_hojas_vida():
    """API para listar o crear Hojas de Vida."""
    if request.method == "GET":
        # Obtener parámetros de filtro
        busqueda = request.args.get("q", "").strip()
        ubicacion = request.args.get("ubicacion", "").strip()
        estado = request.args.get("estado", "").strip()

        # Usamos eager loading para cargar la hoja de vida relacionada
        stmt = (
            select(Activo)
            .options(db.joinedload(Activo.hoja_vida_biomedico))
            .where(Activo.clase_id == 1)  # clase_id=1 es Equipo Biomédico
        )

        # Aplicar filtros
        if busqueda:
            search_pattern = f"%{busqueda}%"
            stmt = stmt.where(
                or_(
                    Activo.nombre_activo.ilike(search_pattern),
                    Activo.placa_codigo_interno.ilike(search_pattern),
                )
            )

        if ubicacion:
            stmt = stmt.where(Activo.ubicacion == ubicacion)

        # Filtro por estado de hoja de vida
        if estado == "1":
            # Solo activos CON hoja de vida
            stmt = stmt.join(
                HojaVidaBiomedico, Activo.id == HojaVidaBiomedico.activo_id
            )
        elif estado == "0":
            # Solo activos SIN hoja de vida
            stmt = stmt.outerjoin(
                HojaVidaBiomedico, Activo.id == HojaVidaBiomedico.activo_id
            )
            stmt = stmt.where(HojaVidaBiomedico.id == None)

        stmt = stmt.order_by(Activo.nombre_activo)

        activos = db.session.execute(stmt).scalars().unique().all()

        hojas_list = []
        for activo in activos:
            hv = activo.hoja_vida_biomedico
            hojas_list.append(
                {
                    "activo_id": activo.id,
                    "id": activo.id,  # Alias para compatibilidad
                    "nombre_activo": activo.nombre_activo,
                    "placa_codigo_interno": activo.placa_codigo_interno,
                    "ubicacion": activo.ubicacion,
                    "marca": activo.marca,
                    "modelo": activo.modelo,
                    "tiene_hoja_vida": 1 if hv else 0,
                }
            )

        return jsonify(hojas_list)

    if request.method == "POST":
        try:
            data = request.form
            activo_id = data.get("activo_id")

            if not activo_id:
                return (
                    jsonify({"success": False, "message": "Se requiere un activo."}),
                    400,
                )

            # Verificar si ya existe una hoja de vida para este activo
            if db.session.scalar(
                select(HojaVidaBiomedico).where(
                    HojaVidaBiomedico.activo_id == activo_id
                )
            ):
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Este activo ya tiene una Hoja de Vida.",
                        }
                    ),
                    409,
                )

            # Preparar datos para el constructor, convirtiendo booleanos explícitamente
            hdv_data = {
                k: (v if v else None)
                for k, v in data.items()
                if hasattr(HojaVidaBiomedico, k)
                and k
                not in [
                    "activo_id",
                    "manual_usuario",
                    "manual_servicio",
                    "requiere_calibracion",
                ]
            }

            # Conversión de strings a booleans para los campos específicos
            hdv_data["manual_usuario"] = (
                str(data.get("manual_usuario")).lower() == "true"
            )
            hdv_data["manual_servicio"] = (
                str(data.get("manual_servicio")).lower() == "true"
            )
            hdv_data["requiere_calibracion"] = (
                str(data.get("requiere_calibracion")).lower() == "true"
            )

            nueva_hdv = HojaVidaBiomedico(activo_id=activo_id, **hdv_data)

            # Añadir a la sesión y confirmar
            db.session.add(nueva_hdv)
            db.session.commit()
            return (
                jsonify(
                    {
                        "success": True,
                        "id": nueva_hdv.id,
                        "message": "Hoja de Vida creada con éxito.",
                    }
                ),
                201,
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear Hoja de Vida: {e}")
            return jsonify({"success": False, "message": str(e)}), 500


@biomedicos_bp.route(
    "/api/hojas-vida/<int:activo_id>", methods=["GET", "PUT", "DELETE"]
)
def api_manage_hoja_vida(activo_id):
    """API para eliminar una Hoja de Vida."""
    hdv = db.session.scalar(
        select(HojaVidaBiomedico).where(HojaVidaBiomedico.activo_id == activo_id)
    )

    if request.method == "DELETE":
        try:
            if not hdv:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Hoja de Vida no encontrada para este activo.",
                        }
                    ),
                    404,
                )

            # Eliminar de la sesión (cascade se encargará de documentos y mantenimientos)
            db.session.delete(hdv)
            db.session.commit()
            return jsonify(
                {"success": True, "message": "Hoja de Vida eliminada con éxito."}
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error al eliminar Hoja de Vida para activo {activo_id}: {e}"
            )
            return jsonify({"success": False, "message": str(e)}), 500

    if request.method == "GET":
        if not hdv:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Hoja de Vida no encontrada para este activo.",
                    }
                ),
                404,
            )

        # Serializar datos de la hoja de vida
        hdv_data = {
            "id": hdv.id,
            "activo_id": hdv.activo_id,
            "permiso_comercializacion": hdv.permiso_comercializacion,
            "n_factura": hdv.n_factura,
            "n_orden_compra": hdv.n_orden_compra,
            "fecha_fabricacion": (
                hdv.fecha_fabricacion.strftime("%Y-%m-%d")
                if hdv.fecha_fabricacion
                else None
            ),
            "fecha_instalacion": (
                hdv.fecha_instalacion.strftime("%Y-%m-%d")
                if hdv.fecha_instalacion
                else None
            ),
            "distribuidor": hdv.distribuidor,
            "forma_adquisicion": hdv.forma_adquisicion,
            "telefono": hdv.telefono,
            "correo_electronico": hdv.correo_electronico,
            "fecha_ingreso": (
                hdv.fecha_ingreso.strftime("%Y-%m-%d") if hdv.fecha_ingreso else None
            ),
            "vencimiento_garantia": (
                hdv.vencimiento_garantia.strftime("%Y-%m-%d")
                if hdv.vencimiento_garantia
                else None
            ),
            "costo": hdv.costo,
            "vida_util_anios": hdv.vida_util_anios,
            "voltaje": hdv.voltaje,
            "frecuencia": hdv.frecuencia,
            "dimensiones": hdv.dimensiones,
            "corriente": hdv.corriente,
            "potencia": hdv.potencia,
            "peso": hdv.peso,
            "equipo_fijo_movil": hdv.equipo_fijo_movil,
            "humedad_relativa": hdv.humedad_relativa,
            "temperatura_trabajo": hdv.temperatura_trabajo,
            "manual_usuario": hdv.manual_usuario,
            "manual_servicio": hdv.manual_servicio,
            "clasificacion_riesgo": hdv.clasificacion_riesgo,
            "clasificacion_biomedica": hdv.clasificacion_biomedica,
            "periodicidad_mantenimiento": hdv.periodicidad_mantenimiento,
            "requiere_calibracion": hdv.requiere_calibracion,
            "periodicidad_metrologia": hdv.periodicidad_metrologia,
            "documentos": [
                {"tipo": doc.tipo_documento, "ruta": doc.ruta_archivo}
                for doc in hdv.documentos
            ],
            "foto_activo": hdv.activo.ruta_foto_activo if hdv.activo else None,
        }
        return jsonify(hdv_data)

    if request.method == "PUT":
        if not hdv:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Hoja de Vida no encontrada para este activo.",
                    }
                ),
                404,
            )

        try:
            data = request.form
            # Actualizar campos existentes
            for key, value in data.items():
                if hasattr(hdv, key):
                    if "fecha" in key or "vencimiento" in key:
                        setattr(hdv, key, _convert_to_date(value))
                    elif key in ["costo", "vida_util_anios"]:
                        # Manejar conversión a número
                        try:
                            num_value = float(value) if "." in value else int(value)
                            setattr(hdv, key, num_value)
                        except (ValueError, TypeError):
                            setattr(hdv, key, None)
                    elif key in [
                        "manual_usuario",
                        "manual_servicio",
                        "requiere_calibracion",
                    ]:
                        setattr(hdv, key, str(value).lower() == "true")
                    else:
                        setattr(hdv, key, value if value else None)

            # Procesar archivos nuevos si fueron subidos
            files_to_process = {
                "foto_activo": ("foto_activo", "HOJAS_DE_VIDA_FOLDER"),
                "pdf_factura": ("factura", "HOJAS_DE_VIDA_FOLDER"),
                "pdf_invima": ("invima", "HOJAS_DE_VIDA_FOLDER"),
                "pdf_importacion": ("importacion", "HOJAS_DE_VIDA_FOLDER"),
                "pdf_manual_usuario": ("manual_usuario", "HOJAS_DE_VIDA_FOLDER"),
                "pdf_manual_servicio": ("manual_servicio", "HOJAS_DE_VIDA_FOLDER"),
            }

            for form_field, (doc_type, config_key) in files_to_process.items():
                file = request.files.get(form_field)
                if file and file.filename:
                    # --- Validación de contenido de archivo ---
                    import magic

                    is_image = doc_type == "foto_activo"
                    allowed_mimes = (
                        ["image/jpeg", "image/png", "image/gif"]
                        if is_image
                        else ["application/pdf"]
                    )

                    file.seek(0)
                    mime_type = magic.from_buffer(file.read(2048), mime=True)
                    file.seek(0)

                    if mime_type not in allowed_mimes:
                        expected_type = (
                            "una imagen (JPG, PNG, GIF)" if is_image else "un PDF"
                        )
                        raise ValueError(
                            f"El archivo para '{doc_type}' no es {expected_type} (detectado: {mime_type})."
                        )
                    # --- Fin de la validación ---

                    # Borrar documento anterior si existe
                    if doc_type != "foto_activo":
                        doc_anterior = db.session.scalar(
                            select(DocumentoAdjunto)
                            .where(DocumentoAdjunto.hoja_vida_id == hdv.id)
                            .where(DocumentoAdjunto.tipo_documento == doc_type)
                        )
                        if doc_anterior:
                            # Intentar borrar archivo físico
                            try:
                                ruta_antigua = os.path.join(
                                    current_app.root_path,
                                    "..",
                                    doc_anterior.ruta_archivo,
                                )
                                if os.path.exists(ruta_antigua):
                                    os.remove(ruta_antigua)
                            except OSError as e:
                                current_app.logger.warning(
                                    f"No se pudo borrar archivo antiguo: {e}"
                                )

                            db.session.delete(doc_anterior)

                    # Leer tamaño del archivo antes de guardarlo
                    file.seek(0, 2)  # Mover al final
                    file_size = file.tell()
                    file.seek(0)  # Regresar al inicio

                    # Guardar nuevo archivo
                    filename = secure_filename(
                        f"hdv_{hdv.id}_{doc_type}_{file.filename}"
                    )
                    subfolder = current_app.config[config_key]
                    os.makedirs(subfolder, exist_ok=True)
                    filepath = os.path.join(subfolder, filename)
                    file.save(filepath)

                    relative_path = os.path.join(os.path.basename(subfolder), filename)

                    if doc_type == "foto_activo":
                        # Actualizar foto del activo
                        hdv.activo.ruta_foto_activo = relative_path
                    else:
                        # Crear nuevo documento adjunto
                        doc_adjunto = DocumentoAdjunto(
                            hoja_vida_id=hdv.id,
                            tipo_documento=doc_type,
                            nombre_archivo_original=file.filename,
                            ruta_archivo=relative_path,
                            mime_type=file.content_type,
                            tamano_bytes=file_size,
                        )
                        db.session.add(doc_adjunto)

            db.session.commit()
            current_app.logger.info(
                f"Hoja de Vida actualizada exitosamente para activo_id {activo_id}"
            )
            return jsonify(
                {"success": True, "message": "Hoja de Vida actualizada con éxito."}
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error al actualizar Hoja de Vida para activo {activo_id}: {e}"
            )
            return jsonify({"success": False, "message": str(e)}), 500

    return jsonify({"message": "Método no soportado."}), 405


@biomedicos_bp.route("/api/hojas-vida/pdf/<int:activo_id>")
def api_generar_pdf_consolidado(activo_id):
    """
    Genera un PDF consolidado para una Hoja de Vida, incluyendo
    datos del activo, mantenimientos y todas las evidencias.
    Busca la hoja de vida a través del activo_id.
    """
    hdv = db.session.scalar(
        select(HojaVidaBiomedico).where(HojaVidaBiomedico.activo_id == activo_id)
    )

    if not hdv:
        return (
            render_template(
                "pdf_templates/pdf_error.html", message="Hoja de Vida no encontrada."
            ),
            404,
        )

    try:
        # 1. Construir el contexto usando el builder.
        # Toda la lógica compleja ahora vive en un solo lugar.
        context = build_hoja_vida_pdf_context(hdv)

        # 2. Renderizar la plantilla "tonta" con el contexto preparado.
        html = render_template("pdf_templates/hoja_vida_consolidada.html", **context)

        # 3. Generar el PDF.
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()

        # 4. Enviar la respuesta.
        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="HdV_{hdv.activo.placa_codigo_interno}.pdf"'
        )
        return response

    except Exception as e:
        current_app.logger.error(
            f"Error generando PDF consolidado para activo {activo_id}: {e}"
        )
        return render_template("pdf_templates/pdf_error.html", message=str(e)), 500


@biomedicos_bp.route("/api/mantenimientos/pdf/<int:mantenimiento_id>")
def api_generar_pdf_mantenimiento(mantenimiento_id):
    """
    Genera un PDF del mantenimiento según su tipo (preventivo, correctivo, calibración).
    Siguiendo el principio de Gosling: código limpio, modular y robusto.
    """
    # Buscar el mantenimiento con eager loading
    mantenimiento = db.session.scalar(
        select(Mantenimiento)
        .options(db.joinedload(Mantenimiento.activo), db.joinedload(Mantenimiento.tipo))
        .where(Mantenimiento.id == mantenimiento_id)
    )

    if not mantenimiento:
        return (
            render_template(
                "pdf_templates/pdf_error.html", message="Mantenimiento no encontrado."
            ),
            404,
        )

    try:
        # 1. Construir el contexto usando el builder modular
        context = build_mantenimiento_pdf_context(mantenimiento)

        # 2. Determinar el template según el tipo de mantenimiento
        tipo_nombre = (
            mantenimiento.tipo.nombre.lower() if mantenimiento.tipo else "preventivo"
        )

        # Mapeo de tipos a templates
        template_map = {
            "preventivo": "pdf_templates/mantenimiento_preventivo.html",
            "correctivo": "pdf_templates/mantenimiento_correctivo.html",
            "calibracion": "pdf_templates/mantenimiento_calibracion.html",
            "calibración": "pdf_templates/mantenimiento_calibracion.html",
        }

        template_name = template_map.get(
            tipo_nombre, "pdf_templates/mantenimiento_preventivo.html"
        )

        # 3. Renderizar la plantilla con el contexto preparado
        html = render_template(template_name, **context)

        # 4. Generar el PDF
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()

        # 5. Enviar la respuesta
        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="Mantenimiento_{mantenimiento.id}_{mantenimiento.activo.placa_codigo_interno}.pdf"'
        )
        return response

    except Exception as e:
        current_app.logger.error(
            f"Error generando PDF de mantenimiento {mantenimiento_id}: {e}",
            exc_info=True,
        )
        return render_template("pdf_templates/pdf_error.html", message=str(e)), 500


# =====================================================================
# API ENDPOINTS - WIZARD HOJA DE VIDA
# =====================================================================


@biomedicos_bp.route("/api/wizard/hoja-vida/start", methods=["POST"])
def wizard_hdv_start():
    """
    Paso inicial del wizard. Recibe el activo_id, lo valida y
    limpia/inicializa los datos del wizard en la sesión.
    """
    data = request.get_json()
    activo_id = data.get("activo_id")

    if not activo_id:
        return (
            jsonify(
                {"success": False, "message": "Se requiere seleccionar un activo."}
            ),
            400,
        )

    # Validar que el activo exista y no tenga ya una hoja de vida
    activo = db.session.get(Activo, activo_id)
    if not activo:
        return (
            jsonify({"success": False, "message": "El activo seleccionado no existe."}),
            404,
        )

    if activo.hoja_vida_biomedico:
        return (
            jsonify(
                {"success": False, "message": "Este activo ya tiene una Hoja de Vida."}
            ),
            409,
        )

    # Inicializar datos del wizard en la sesión
    session["wizard_hdv_data"] = {"activo_id": activo_id}
    session.modified = True

    return jsonify({"success": True, "message": "Wizard iniciado correctamente."})


@biomedicos_bp.route("/api/wizard/hoja-vida/step", methods=["POST"])
def wizard_hdv_step():
    """
    Guarda los datos de un paso intermedio del wizard en la sesión.
    """
    if "wizard_hdv_data" not in session:
        return (
            jsonify({"success": False, "message": "El wizard no ha sido iniciado."}),
            400,
        )

    step_data = request.get_json()
    if not step_data:
        return jsonify({"success": False, "message": "No se recibieron datos."}), 400

    # Actualizar los datos del wizard en la sesión
    session["wizard_hdv_data"].update(step_data)
    session.modified = True

    return jsonify({"success": True, "message": "Paso guardado."})


@biomedicos_bp.route("/api/wizard/hoja-vida/finish", methods=["POST"])
def wizard_hdv_finish():
    """
    Paso final. Recopila todos los datos de la sesión, crea la Hoja de Vida
    y los documentos adjuntos, y limpia la sesión.
    """
    if "wizard_hdv_data" not in session:
        current_app.logger.warning("Intento de submit de wizard sin datos en sesión.")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "No hay datos de Hoja de Vida en la sesión.",
                }
            ),
            400,
        )

    form_data = request.form
    session_data = session.get("wizard_hdv_data", {})
    activo_id = session_data.get("activo_id")

    if not activo_id:
        current_app.logger.error(
            "activo_id no encontrado en los datos del wizard de Hoja de Vida."
        )
        session.pop("wizard_hdv_data", None)
        session.modified = True
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Faltan datos críticos para crear la Hoja de Vida (activo_id).",
                }
            ),
            400,
        )

    try:
        activo = db.session.get(Activo, activo_id)
        if not activo:
            current_app.logger.warning(
                f"Intento de crear HDV para activo_id {activo_id} que no existe."
            )
            return (
                jsonify(
                    {"success": False, "message": "El activo seleccionado no existe."}
                ),
                404,
            )

        if activo.hoja_vida_biomedico:
            current_app.logger.warning(
                f"Intento de crear HDV para activo_id {activo_id} que ya tiene una."
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Este activo ya tiene una Hoja de Vida.",
                    }
                ),
                409,
            )

        # Combinar datos de sesión y del formulario final
        all_data = {**session_data, **form_data}

        hdv_data = {
            "activo_id": activo_id,
            "permiso_comercializacion": all_data.get("permiso_comercializacion"),
            "n_factura": all_data.get("n_factura"),
            "n_orden_compra": all_data.get("n_orden_compra"),
            "fecha_fabricacion": _convert_to_date(all_data.get("fecha_fabricacion")),
            "fecha_instalacion": _convert_to_date(all_data.get("fecha_instalacion")),
            "distribuidor": all_data.get("distribuidor"),
            "forma_adquisicion": all_data.get("forma_adquisicion"),
            "telefono": all_data.get("telefono"),
            "correo_electronico": all_data.get("correo_electronico"),
            "fecha_ingreso": _convert_to_date(all_data.get("fecha_ingreso")),
            "vencimiento_garantia": _convert_to_date(
                all_data.get("vencimiento_garantia")
            ),
            "costo": (
                float(all_data.get("costo"))
                if all_data.get("costo")
                and all_data.get("costo").replace(".", "", 1).isdigit()
                else None
            ),
            "vida_util_anios": (
                int(all_data.get("vida_util_anios"))
                if all_data.get("vida_util_anios")
                and all_data.get("vida_util_anios").isdigit()
                else None
            ),
            "voltaje": all_data.get("voltaje"),
            "frecuencia": all_data.get("frecuencia"),
            "dimensiones": all_data.get("dimensiones"),
            "corriente": all_data.get("corriente"),
            "potencia": all_data.get("potencia"),
            "peso": all_data.get("peso"),
            "equipo_fijo_movil": all_data.get("equipo_fijo_movil"),
            "humedad_relativa": all_data.get("humedad_relativa"),
            "temperatura_trabajo": all_data.get("temperatura_trabajo"),
            "manual_usuario": str(all_data.get("manual_usuario")).lower() == "true",
            "manual_servicio": str(all_data.get("manual_servicio")).lower() == "true",
            "clasificacion_riesgo": all_data.get("clasificacion_riesgo"),
            "clasificacion_biomedica": all_data.get("clasificacion_biomedica"),
            "periodicidad_mantenimiento": all_data.get("periodicidad_mantenimiento"),
            "requiere_calibracion": str(all_data.get("requiere_calibracion")).lower()
            == "true",
            "periodicidad_metrologia": all_data.get("periodicidad_metrologia"),
        }

        nueva_hdv = HojaVidaBiomedico(**hdv_data)
        db.session.add(nueva_hdv)
        db.session.flush()  # Para obtener el ID de la nueva hoja de vida

        # Manejo de archivos adjuntos
        files_to_process = {
            "foto_activo": ("foto_activo", "HOJAS_DE_VIDA_FOLDER"),
            "pdf_factura": ("factura", "HOJAS_DE_VIDA_FOLDER"),
            "pdf_invima": ("invima", "HOJAS_DE_VIDA_FOLDER"),
            "pdf_importacion": ("importacion", "HOJAS_DE_VIDA_FOLDER"),
            "pdf_manual_usuario": ("manual_usuario", "HOJAS_DE_VIDA_FOLDER"),
            "pdf_manual_servicio": ("manual_servicio", "HOJAS_DE_VIDA_FOLDER"),
        }

        for form_field, (doc_type, config_key) in files_to_process.items():
            file = request.files.get(form_field)
            if file and file.filename:
                # --- Validación de contenido de archivo ---
                import magic

                is_image = doc_type == "foto_activo"
                allowed_mimes = (
                    ["image/jpeg", "image/png", "image/gif"]
                    if is_image
                    else ["application/pdf"]
                )

                file.seek(0)
                mime_type = magic.from_buffer(file.read(2048), mime=True)
                file.seek(0)

                if mime_type not in allowed_mimes:
                    expected_type = (
                        "una imagen (JPG, PNG, GIF)" if is_image else "un PDF"
                    )
                    raise ValueError(
                        f"El archivo para '{doc_type}' no es {expected_type} (detectado: {mime_type})."
                    )
                # --- Fin de la validación ---

                filename = secure_filename(
                    f"hdv_{nueva_hdv.id}_{doc_type}_{file.filename}"
                )
                subfolder = current_app.config[config_key]
                os.makedirs(subfolder, exist_ok=True)
                filepath = os.path.join(subfolder, filename)
                file.save(filepath)

                relative_path = os.path.join(os.path.basename(subfolder), filename)

                if doc_type == "foto_activo":
                    activo.ruta_foto_activo = relative_path
                else:
                    doc_adjunto = DocumentoAdjunto(
                        hoja_vida_id=nueva_hdv.id,
                        tipo_documento=doc_type,
                        ruta_archivo=relative_path,
                        # Adicional: guardar metadata del archivo
                        nombre_archivo_original=file.filename,
                        mime_type=file.content_type,
                        tamano_bytes=os.path.getsize(filepath),
                    )
                    db.session.add(doc_adjunto)

        db.session.commit()

        current_app.logger.info(
            f"Hoja de Vida creada exitosamente para activo_id {activo_id} (ID: {nueva_hdv.id})."
        )
        flash(f"Hoja de Vida para {activo.nombre_activo} creada con éxito.", "success")

        return (
            jsonify(
                {
                    "success": True,
                    "id": nueva_hdv.id,
                    "message": "Hoja de Vida creada exitosamente.",
                }
            ),
            201,
        )

    except db.exc.IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error de integridad al crear HDV para activo_id {activo_id}: {e}"
        )
        return (
            jsonify(
                {"success": False, "message": "Este activo ya tiene una Hoja de Vida."}
            ),
            409,
        )
    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error de validación de datos al crear HDV para activo_id {activo_id}: {e}"
        )
        return (
            jsonify(
                {"success": False, "message": f"Error de validación de datos: {e}"}
            ),
            400,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error inesperado al crear Hoja de Vida para activo_id {activo_id}: {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error inesperado al crear Hoja de Vida: {str(e)}",
                }
            ),
            500,
        )
    finally:
        session.pop("wizard_hdv_data", None)
        session.modified = True


# =====================================================================
# ENDPOINT PARA CARGA TEMPORAL DE DOCUMENTOS
# =====================================================================


@biomedicos_bp.route("/api/hojas-vida/upload-temp", methods=["POST"])
def upload_temp_file():
    """
    Endpoint para subir archivos PDF temporalmente durante el wizard.
    Los archivos se guardan en una carpeta temporal con un checksum SHA256.
    """
    try:
        if "file" not in request.files:
            return (
                jsonify({"success": False, "message": "No se recibió ningún archivo"}),
                400,
            )

        file = request.files["file"]
        categoria = request.form.get("categoria", "general")

        if file.filename == "":
            return (
                jsonify({"success": False, "message": "Nombre de archivo vacío"}),
                400,
            )

        if not file.filename.lower().endswith(".pdf"):
            return (
                jsonify({"success": False, "message": "Solo se permiten archivos PDF"}),
                400,
            )

        # Validar tipo MIME real para mitigar carga de archivos maliciosos renombrados
        import magic

        file.seek(0)
        mime_type = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)

        if mime_type != "application/pdf":
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "El contenido del archivo no corresponde a un PDF válido.",
                    }
                ),
                400,
            )

        # Crear carpeta temporal si no existe
        temp_folder = os.path.join(
            current_app.config.get("UPLOAD_FOLDER", "uploads"), "temp"
        )
        os.makedirs(temp_folder, exist_ok=True)

        # Generar nombre de archivo seguro
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(temp_folder, temp_filename)

        # Guardar archivo
        file.save(filepath)

        # Calcular checksum SHA256
        with open(filepath, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        current_app.logger.info(
            f"Archivo temporal guardado: {temp_filename} (SHA256: {file_hash})"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "filename": temp_filename,
                    "filepath": filepath,
                    "checksum": file_hash,
                    "message": "Archivo cargado exitosamente",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error al subir archivo temporal: {e}", exc_info=True)
        return (
            jsonify({"success": False, "message": f"Error al subir archivo: {str(e)}"}),
            500,
        )


# =====================================================================
# GESTIÓN DE DOCUMENTOS ESCANEADOS DE MANTENIMIENTOS
# =====================================================================


@biomedicos_bp.route(
    "/mantenimientos/<int:mantenimiento_id>/documentos/subir", methods=["GET", "POST"]
)
def subir_documento_mantenimiento(mantenimiento_id):
    """Sube un documento escaneado a un mantenimiento biomédico."""
    mantenimiento = db.session.get(Mantenimiento, mantenimiento_id)
    if not mantenimiento:
        flash("Mantenimiento no encontrado", "error")
        return redirect(url_for("biomedicos.mantenimientos"))

    if request.method == "POST":
        # Validar archivo
        if "archivo" not in request.files:
            flash("No se seleccionó ningún archivo", "error")
            return redirect(request.url)

        archivo = request.files["archivo"]
        if archivo.filename == "":
            flash("No se seleccionó ningún archivo", "error")
            return redirect(request.url)

        # Validar contenido y extensión del archivo
        import magic

        MIME_TYPE_MAP = {
            "pdf": ["application/pdf"],
            "jpg": ["image/jpeg"],
            "jpeg": ["image/jpeg"],
            "png": ["image/png"],
            "gif": ["image/gif"],
            "xlsx": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ],
            "xls": ["application/vnd.ms-excel", "application/x-cfb"],
            "docx": [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ],
            "doc": ["application/msword", "application/x-cfb"],
        }
        extension = (
            archivo.filename.rsplit(".", 1)[1].lower()
            if "." in archivo.filename
            else ""
        )
        allowed_mimes = MIME_TYPE_MAP.get(extension)

        if not allowed_mimes:
            flash(
                f'Formato de archivo con extensión ".{extension}" no es soportado.',
                "error",
            )
            return redirect(request.url)

        # Validar tipo MIME real
        archivo.seek(0)
        mime_type = magic.from_buffer(archivo.read(2048), mime=True)
        archivo.seek(0)

        if mime_type not in allowed_mimes:
            flash(
                f"El contenido del archivo no corresponde a un archivo .{extension} válido (detectado: {mime_type}).",
                "error",
            )
            return redirect(request.url)

        # Crear directorio si no existe
        upload_dir = os.path.join(
            current_app.static_folder, "uploads", "mantenimientos_documentos"
        )
        os.makedirs(upload_dir, exist_ok=True)

        # Generar nombre de archivo seguro
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        placa = mantenimiento.activo.placa_codigo_interno.replace("/", "_").replace(
            "\\", "_"
        )
        nombre_seguro = secure_filename(
            f"mant_{mantenimiento_id}_{placa}_{timestamp}.{extension}"
        )
        ruta_completa = os.path.join(upload_dir, nombre_seguro)

        # Guardar archivo
        archivo.save(ruta_completa)

        # Obtener tamaño del archivo
        tamano_bytes = os.path.getsize(ruta_completa)

        # Determinar tipo de documento
        tipo_doc = (
            "pdf"
            if extension == "pdf"
            else (
                "imagen"
                if extension in {"jpg", "jpeg", "png", "gif"}
                else (
                    "excel"
                    if extension in {"xlsx", "xls"}
                    else "word" if extension in {"doc", "docx"} else "otro"
                )
            )
        )

        # Parsear fecha del documento
        fecha_documento = None
        if request.form.get("fecha_documento"):
            try:
                fecha_documento = datetime.strptime(
                    request.form.get("fecha_documento"), "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        # Crear registro en BD
        documento = MantenimientoDocumento(
            mantenimiento_id=mantenimiento_id,
            nombre_archivo=archivo.filename,
            ruta_archivo=f"uploads/mantenimientos_documentos/{nombre_seguro}",
            tipo_documento=tipo_doc,
            tamano_archivo=tamano_bytes,
            fecha_documento=fecha_documento,
            tecnico_responsable=request.form.get("tecnico_responsable"),
            descripcion=request.form.get("descripcion"),
            uploaded_by=current_user.id if current_user.is_authenticated else None,
        )

        db.session.add(documento)
        db.session.commit()

        flash(f'Documento "{archivo.filename}" subido exitosamente', "success")
        return redirect(
            url_for(
                "biomedicos.detalle_mantenimiento", mantenimiento_id=mantenimiento_id
            )
        )

    # GET: Mostrar formulario
    return render_template(
        "mantenimientos/documentos/subir_documento.html", mantenimiento=mantenimiento
    )


@biomedicos_bp.route("/mantenimientos/documentos/<int:doc_id>/ver")
def ver_documento_mantenimiento(doc_id):
    """Visualiza un documento en el navegador."""
    documento = db.session.get(MantenimientoDocumento, doc_id)
    if not documento:
        flash("Documento no encontrado", "error")
        return redirect(url_for("biomedicos.mantenimientos"))

    return render_template(
        "mantenimientos/documentos/visor_pdf.html", documento=documento
    )


@biomedicos_bp.route("/mantenimientos/documentos/<int:doc_id>/descargar")
def descargar_documento_mantenimiento(doc_id):
    """Descarga un documento."""
    documento = db.session.get(MantenimientoDocumento, doc_id)
    if not documento:
        flash("Documento no encontrado", "error")
        return redirect(url_for("biomedicos.mantenimientos"))

    # Extraer directorio y nombre de archivo
    directorio = os.path.dirname(documento.ruta_archivo)
    nombre_archivo = os.path.basename(documento.ruta_archivo)
    ruta_completa = os.path.join(current_app.static_folder, directorio)

    return send_from_directory(
        ruta_completa,
        nombre_archivo,
        as_attachment=True,
        download_name=documento.nombre_archivo,
    )


@biomedicos_bp.route(
    "/mantenimientos/documentos/<int:doc_id>/eliminar", methods=["POST"]
)
def eliminar_documento_mantenimiento(doc_id):
    """Elimina un documento (solo administradores)."""
    documento = db.session.get(MantenimientoDocumento, doc_id)
    if not documento:
        flash("Documento no encontrado", "error")
        return redirect(url_for("biomedicos.mantenimientos"))

    # Verificar permisos (solo admin)
    if not current_user.is_authenticated or current_user.role != "admin":
        flash("No tiene permisos para eliminar documentos", "error")
        return redirect(
            url_for(
                "biomedicos.detalle_mantenimiento",
                mantenimiento_id=documento.mantenimiento_id,
            )
        )

    mantenimiento_id = documento.mantenimiento_id

    # Eliminar archivo físico
    try:
        ruta_completa = os.path.join(current_app.static_folder, documento.ruta_archivo)
        if os.path.exists(ruta_completa):
            os.remove(ruta_completa)
    except Exception as e:
        current_app.logger.error(f"Error al eliminar archivo físico: {e}")

    # Eliminar registro de BD
    db.session.delete(documento)
    db.session.commit()

    flash("Documento eliminado exitosamente", "success")
    return redirect(
        url_for("biomedicos.detalle_mantenimiento", mantenimiento_id=mantenimiento_id)
    )
