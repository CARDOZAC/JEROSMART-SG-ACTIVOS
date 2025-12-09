from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    make_response,
    send_from_directory,
    current_app,
)
from . import mantenimientos_bp
from ..decorators import login_required, role_required
from ..extensions import db
from ..models import (
    Activo,
    HojaVidaEquipo,
    ClaseActivo,
    Mantenimiento,
    MantenimientoTipo,
    MantenimientoDocumento,
)
from .forms import MantenimientoForm, CargarHistoricoForm
from flask_login import current_user
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename
import io
from weasyprint import HTML
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


@mantenimientos_bp.route("/")
@login_required
def index():
    """
    Página principal del módulo de mantenimientos para activos no biomédicos.
    Este módulo gestiona: TICs, Equipos Electro-Industriales y Muebles y Enseres.
    """
    return render_template(
        "mantenimientos/gestion_mantenimientos.html", active_page="mantenimientos"
    )


# ==============================================================================
# RUTAS PARA HOJAS DE VIDA
# ==============================================================================


@mantenimientos_bp.route("/hojas_vida")
@login_required
def hojas_vida():
    """Lista todas las hojas de vida de equipos no biomédicos."""
    # Obtener hojas de vida de equipos de clases 2, 3, 4
    hojas = (
        db.session.query(HojaVidaEquipo)
        .join(Activo)
        .filter(Activo.clase_id.in_([2, 3, 4]))
        .all()
    )

    return render_template(
        "mantenimientos/hojas_vida/lista_hojas_vida.html",
        hojas=hojas,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/hojas_vida/nueva", methods=["GET", "POST"])
@login_required
def nueva_hoja_vida():
    """Crea una nueva hoja de vida para un equipo."""
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            activo_id = request.form.get("activo_id")

            # Verificar que el activo existe y no tiene hoja de vida
            activo = Activo.query.get(activo_id)
            if not activo:
                flash("El activo no existe", "error")
                return redirect(url_for("mantenimientos.nueva_hoja_vida"))

            if activo.hoja_vida_equipo:
                flash("Este activo ya tiene una hoja de vida registrada", "warning")
                return redirect(
                    url_for(
                        "mantenimientos.editar_hoja_vida", id=activo.hoja_vida_equipo.id
                    )
                )

            # Verificar que es un activo no biomédico (clase 2, 3, 4)
            if activo.clase_id not in [2, 3, 4]:
                flash(
                    "Solo se pueden crear hojas de vida para equipos Electro-Industriales, TICs y Muebles y Enseres",
                    "error",
                )
                return redirect(url_for("mantenimientos.nueva_hoja_vida"))

            # Crear hoja de vida
            hoja_vida = HojaVidaEquipo(activo_id=activo_id)

            # Características Comerciales
            hoja_vida.proveedor_nombre = request.form.get("proveedor_nombre")
            if request.form.get("fecha_adquisicion"):
                hoja_vida.fecha_adquisicion = datetime.strptime(
                    request.form.get("fecha_adquisicion"), "%Y-%m-%d"
                )
            hoja_vida.costo_adquisicion = (
                float(request.form.get("costo_adquisicion"))
                if request.form.get("costo_adquisicion")
                else None
            )
            hoja_vida.numero_factura = request.form.get("numero_factura")
            hoja_vida.numero_orden_compra = request.form.get("numero_orden_compra")
            hoja_vida.garantia_meses = (
                int(request.form.get("garantia_meses"))
                if request.form.get("garantia_meses")
                else None
            )
            if request.form.get("fecha_vencimiento_garantia"):
                hoja_vida.fecha_vencimiento_garantia = datetime.strptime(
                    request.form.get("fecha_vencimiento_garantia"), "%Y-%m-%d"
                )
            hoja_vida.vida_util_anios = (
                int(request.form.get("vida_util_anios"))
                if request.form.get("vida_util_anios")
                else None
            )

            # Características Técnicas
            hoja_vida.voltaje = request.form.get("voltaje")
            hoja_vida.potencia = request.form.get("potencia")
            hoja_vida.corriente = request.form.get("corriente")
            hoja_vida.frecuencia = request.form.get("frecuencia")
            hoja_vida.dimensiones = request.form.get("dimensiones")
            hoja_vida.peso = request.form.get("peso")
            hoja_vida.color = request.form.get("color")
            hoja_vida.material = request.form.get("material")

            hoja_vida.manual_usuario = request.form.get("manual_usuario") == "on"
            hoja_vida.manual_servicio = request.form.get("manual_servicio") == "on"
            hoja_vida.manual_instalacion = (
                request.form.get("manual_instalacion") == "on"
            )

            # Características Específicas (JSON)
            caracteristicas_especificas = {}
            # Según la clase del activo, capturar campos específicos
            if activo.clase_id == 3:  # TICs
                caracteristicas_especificas = {
                    "sistema_operativo": request.form.get("sistema_operativo"),
                    "procesador": request.form.get("procesador"),
                    "ram": request.form.get("ram"),
                    "disco": request.form.get("disco"),
                    "tipo_equipo": request.form.get("tipo_equipo_tic"),
                }
            elif activo.clase_id == 2:  # Electro-Industrial
                caracteristicas_especificas = {
                    "capacidad": request.form.get("capacidad"),
                    "tipo_combustible": request.form.get("tipo_combustible"),
                    "tipo_motor": request.form.get("tipo_motor"),
                    "tipo_refrigerante": request.form.get("tipo_refrigerante"),
                }
            elif activo.clase_id == 4:  # Muebles y Enseres
                caracteristicas_especificas = {
                    "tipo_mueble": request.form.get("tipo_mueble"),
                    "numero_cajones": request.form.get("numero_cajones"),
                    "acabado": request.form.get("acabado"),
                    "tapiceria": request.form.get("tapiceria"),
                }

            hoja_vida.caracteristicas_especificas_json = caracteristicas_especificas

            # Observaciones
            hoja_vida.observaciones_tecnicas = request.form.get(
                "observaciones_tecnicas"
            )
            hoja_vida.condiciones_uso = request.form.get("condiciones_uso")
            hoja_vida.restricciones = request.form.get("restricciones")

            # Procesar fotos
            fotos_procesadas = procesar_fotos_hoja_vida(
                request.files, activo.placa_codigo_interno
            )
            hoja_vida.foto_url = fotos_procesadas.get("foto_1")
            hoja_vida.foto_2_url = fotos_procesadas.get("foto_2")
            hoja_vida.foto_3_url = fotos_procesadas.get("foto_3")

            # Auditoría
            hoja_vida.created_by = current_user.id
            hoja_vida.updated_by = current_user.id

            db.session.add(hoja_vida)
            db.session.commit()

            flash("Hoja de vida creada exitosamente", "success")
            return redirect(url_for("mantenimientos.ver_hoja_vida", id=hoja_vida.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear la hoja de vida: {str(e)}", "error")
            return redirect(url_for("mantenimientos.nueva_hoja_vida"))

    # GET - Mostrar formulario
    # Obtener activos sin hoja de vida de clases 2, 3, 4
    activos = Activo.query.filter(
        Activo.clase_id.in_([2, 3, 4]),
        ~Activo.id.in_(db.session.query(HojaVidaEquipo.activo_id)),
    ).all()

    return render_template(
        "mantenimientos/hojas_vida/nueva_hoja_vida.html",
        activos=activos,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/hojas_vida/ver/<int:id>")
@login_required
def ver_hoja_vida(id):
    """Muestra los detalles de una hoja de vida."""
    hoja_vida = HojaVidaEquipo.query.get_or_404(id)
    return render_template(
        "mantenimientos/hojas_vida/ver_hoja_vida.html",
        hoja_vida=hoja_vida,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/hojas_vida/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_hoja_vida(id):
    """Edita una hoja de vida existente."""
    hoja_vida = HojaVidaEquipo.query.get_or_404(id)

    if request.method == "POST":
        try:
            # Actualizar campos (similar a nueva_hoja_vida)
            # ... código de actualización ...

            hoja_vida.updated_by = current_user.id
            hoja_vida.updated_at = datetime.utcnow()

            db.session.commit()
            flash("Hoja de vida actualizada exitosamente", "success")
            return redirect(url_for("mantenimientos.ver_hoja_vida", id=hoja_vida.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar la hoja de vida: {str(e)}", "error")

    return render_template(
        "mantenimientos/hojas_vida/editar_hoja_vida.html",
        hoja_vida=hoja_vida,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/hojas_vida/eliminar/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def eliminar_hoja_vida(id):
    """Elimina una hoja de vida (solo administradores)."""
    hoja_vida = HojaVidaEquipo.query.get_or_404(id)

    try:
        nombre_activo = hoja_vida.activo.nombre_activo
        db.session.delete(hoja_vida)
        db.session.commit()

        flash(
            f"Hoja de vida del activo {nombre_activo} eliminada exitosamente", "success"
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la hoja de vida: {str(e)}", "error")

    return redirect(url_for("mantenimientos.hojas_vida"))


# ==============================================================================
# RUTAS PARA MANTENIMIENTOS
# ==============================================================================


@mantenimientos_bp.route("/gestionar_mantenimientos")
@login_required
def gestionar_mantenimientos():
    """Lista todos los mantenimientos de equipos no biomédicos."""
    # Estados para mantenimientos pendientes y en proceso
    estados_pendientes = ["Pendiente", "En Proceso"]
    # Estados para mantenimientos históricos
    estados_historicos = ["Completado", "Cancelado"]

    # Consulta para mantenimientos pendientes (clases 2, 3, 4)
    mantenimientos_pendientes = db.session.scalars(
        db.select(Mantenimiento)
        .join(Activo)
        .filter(
            Activo.clase_id.in_([2, 3, 4]), Mantenimiento.estado.in_(estados_pendientes)
        )
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
    ).all()

    # Consulta para mantenimientos históricos (clases 2, 3, 4)
    mantenimientos_historicos = db.session.scalars(
        db.select(Mantenimiento)
        .join(Activo)
        .filter(
            Activo.clase_id.in_([2, 3, 4]), Mantenimiento.estado.in_(estados_historicos)
        )
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
    ).all()

    return render_template(
        "mantenimientos/gestion/lista_mantenimientos.html",
        mantenimientos_pendientes=mantenimientos_pendientes,
        mantenimientos_historicos=mantenimientos_historicos,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/mantenimientos/cargar_historico", methods=["GET", "POST"])
@login_required
def cargar_historico():
    """Carga un PDF de un mantenimiento histórico."""
    form = CargarHistoricoForm()

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
                or "Mantenimiento histórico cargado desde PDF.",
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.session.add(mantenimiento)
            db.session.flush()

            # 3. Guardar el archivo PDF
            archivo = form.documento.data
            extension = archivo.filename.rsplit(".", 1)[-1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            placa = mantenimiento.activo.placa_codigo_interno or "SIN_PLACA"
            nombre_seguro = secure_filename(
                f"mant_hist_{mantenimiento.id}_{placa}_{timestamp}.{extension}"
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
                descripcion="Documento de mantenimiento histórico.",
                uploaded_by=current_user.id,
            )
            db.session.add(documento)
            db.session.commit()

            flash(
                f'Mantenimiento histórico para "{form.activo_id.data.nombre_activo}" cargado exitosamente.',
                "success",
            )
            return redirect(url_for("mantenimientos.gestionar_mantenimientos"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al cargar el mantenimiento histórico: {str(e)}", "error")

    return render_template(
        "mantenimientos/gestion/cargar_historico.html",
        form=form,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/mantenimientos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_mantenimiento():
    """Crea un nuevo registro de mantenimiento para activos no biomédicos."""
    form = MantenimientoForm()

    if form.validate_on_submit():
        try:
            # Crear nuevo mantenimiento
            mantenimiento = Mantenimiento(
                activo_id=form.activo_id.data.id,
                tipo_id=form.tipo_id.data.id,
                fecha_mantenimiento=form.fecha_mantenimiento.data,
                estado=form.estado.data,
                observaciones=form.observaciones.data,
                created_by=current_user.id,
                updated_by=current_user.id,
            )

            db.session.add(mantenimiento)
            db.session.commit()

            flash(
                f"Mantenimiento registrado exitosamente para {form.activo_id.data.nombre_activo}",
                "success",
            )
            return redirect(
                url_for("mantenimientos.ver_mantenimiento", id=mantenimiento.id)
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar el mantenimiento: {str(e)}", "error")
            return redirect(url_for("mantenimientos.nuevo_mantenimiento"))

    return render_template(
        "mantenimientos/gestion/nuevo_mantenimiento.html",
        form=form,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/mantenimientos/ver/<int:id>")
@login_required
def ver_mantenimiento(id):
    """Muestra los detalles de un mantenimiento."""
    mantenimiento = Mantenimiento.query.get_or_404(id)

    # Verificar que el mantenimiento es de un activo no biomédico
    if mantenimiento.activo.clase_id not in [2, 3, 4]:
        flash(
            "Este mantenimiento pertenece a un equipo biomédico y debe gestionarse en el módulo de Biomédicos.",
            "warning",
        )
        return redirect(url_for("mantenimientos.gestionar_mantenimientos"))

    return render_template(
        "mantenimientos/gestion/ver_mantenimiento.html",
        mantenimiento=mantenimiento,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/mantenimientos/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_mantenimiento(id):
    """Edita un mantenimiento existente."""
    mantenimiento = Mantenimiento.query.get_or_404(id)

    # Verificar que el mantenimiento es de un activo no biomédico
    if mantenimiento.activo.clase_id not in [2, 3, 4]:
        flash(
            "Este mantenimiento pertenece a un equipo biomédico y debe gestionarse en el módulo de Biomédicos.",
            "warning",
        )
        return redirect(url_for("mantenimientos.gestionar_mantenimientos"))

    form = MantenimientoForm(obj=mantenimiento)

    if form.validate_on_submit():
        try:
            mantenimiento.activo_id = form.activo_id.data.id
            mantenimiento.tipo_id = form.tipo_id.data.id
            mantenimiento.fecha_mantenimiento = form.fecha_mantenimiento.data
            mantenimiento.estado = form.estado.data
            mantenimiento.observaciones = form.observaciones.data
            mantenimiento.updated_by = current_user.id
            mantenimiento.updated_at = datetime.utcnow()

            db.session.commit()

            flash("Mantenimiento actualizado exitosamente", "success")
            return redirect(
                url_for("mantenimientos.ver_mantenimiento", id=mantenimiento.id)
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el mantenimiento: {str(e)}", "error")

    return render_template(
        "mantenimientos/gestion/editar_mantenimiento.html",
        form=form,
        mantenimiento=mantenimiento,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/mantenimientos/eliminar/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def eliminar_mantenimiento(id):
    """Elimina un mantenimiento (solo administradores)."""
    mantenimiento = Mantenimiento.query.get_or_404(id)

    try:
        nombre_activo = mantenimiento.activo.nombre_activo
        db.session.delete(mantenimiento)
        db.session.commit()

        flash(
            f"Mantenimiento del activo {nombre_activo} eliminado exitosamente",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el mantenimiento: {str(e)}", "error")

    return redirect(url_for("mantenimientos.gestionar_mantenimientos"))


# ==============================================================================
# RUTAS DE REPORTES Y EXPORTACIÓN
# ==============================================================================


@mantenimientos_bp.route("/mantenimientos/pdf/<int:id>")
@login_required
def exportar_mantenimiento_pdf(id):
    """Genera PDF de un mantenimiento individual"""
    mantenimiento = Mantenimiento.query.get_or_404(id)

    html_string = render_template(
        "mantenimientos/reportes/mantenimiento_pdf.html",
        mantenimiento=mantenimiento,
        fecha_generacion=datetime.now(),
    )

    # Generar PDF
    pdf_file = HTML(string=html_string).write_pdf()

    response = make_response(pdf_file)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'inline; filename=mantenimiento_{id}_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

    return response


@mantenimientos_bp.route("/mantenimientos/excel")
@login_required
def exportar_mantenimientos_excel():
    """Exporta listado de mantenimientos a Excel"""

    # Obtener mantenimientos
    mantenimientos = (
        db.session.query(Mantenimiento)
        .join(Activo)
        .filter(Activo.clase_id.in_([2, 3, 4]))
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
        .all()
    )

    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mantenimientos"

    # Estilos
    header_fill = PatternFill(
        start_color="4472C4", end_color="4472C4", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF", size=12)
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Encabezados
    headers = [
        "ID",
        "Activo",
        "Placa",
        "Categoría",
        "Tipo Mantenimiento",
        "Fecha",
        "Estado",
        "Observaciones",
        "Registrado Por",
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    # Datos
    for row_num, mant in enumerate(mantenimientos, 2):
        ws.cell(row=row_num, column=1, value=mant.id).border = border
        ws.cell(row=row_num, column=2, value=mant.activo.nombre_activo).border = border
        ws.cell(
            row=row_num, column=3, value=mant.activo.placa_codigo_interno
        ).border = border
        ws.cell(row=row_num, column=4, value=mant.activo.clase.nombre).border = border
        ws.cell(row=row_num, column=5, value=mant.tipo.nombre).border = border
        ws.cell(
            row=row_num,
            column=6,
            value=(
                mant.fecha_mantenimiento.strftime("%d/%m/%Y")
                if mant.fecha_mantenimiento
                else "N/A"
            ),
        ).border = border
        ws.cell(row=row_num, column=7, value=mant.estado).border = border
        ws.cell(row=row_num, column=8, value=mant.observaciones or "").border = border
        ws.cell(
            row=row_num,
            column=9,
            value=mant.creator.username if mant.creator else "N/A",
        ).border = border

    # Ajustar anchos de columna
    column_widths = [8, 35, 15, 25, 20, 15, 15, 50, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    # Guardar en memoria
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    response = make_response(excel_file.read())
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename=mantenimientos_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

    return response


@mantenimientos_bp.route("/mantenimientos/reporte-consolidado-pdf")
@login_required
def exportar_reporte_consolidado_pdf():
    """Genera reporte consolidado de mantenimientos en PDF"""

    # Obtener mantenimientos
    mantenimientos = (
        db.session.query(Mantenimiento)
        .join(Activo)
        .filter(Activo.clase_id.in_([2, 3, 4]))
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
        .limit(100)
        .all()
    )

    # Estadísticas
    total = len(mantenimientos)
    pendientes = len([m for m in mantenimientos if m.estado == "Pendiente"])
    en_proceso = len([m for m in mantenimientos if m.estado == "En Proceso"])
    completados = len([m for m in mantenimientos if m.estado == "Completado"])

    html_string = render_template(
        "mantenimientos/reportes/consolidado_pdf.html",
        mantenimientos=mantenimientos,
        total=total,
        pendientes=pendientes,
        en_proceso=en_proceso,
        completados=completados,
        fecha_generacion=datetime.now(),
    )

    # Generar PDF
    pdf_file = HTML(string=html_string).write_pdf()

    response = make_response(pdf_file)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'inline; filename=reporte_mantenimientos_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

    return response


# ==============================================================================
# RUTAS DE ALERTAS Y NOTIFICACIONES
# ==============================================================================


@mantenimientos_bp.route("/api/alertas-proximos-mantenimientos")
@login_required
def obtener_alertas_mantenimientos():
    """
    API endpoint que retorna los mantenimientos próximos a vencer.
    Retorna mantenimientos pendientes programados para los próximos 15 días.
    """
    hoy = datetime.now().date()
    fecha_limite = hoy + timedelta(days=15)

    # Obtener mantenimientos pendientes próximos
    mantenimientos_proximos = (
        db.session.query(Mantenimiento)
        .join(Activo)
        .filter(
            Activo.clase_id.in_([2, 3, 4]),
            Mantenimiento.estado.in_(["Pendiente", "En Proceso"]),
            Mantenimiento.fecha_mantenimiento >= hoy,
            Mantenimiento.fecha_mantenimiento <= fecha_limite,
        )
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
        .all()
    )

    # Obtener mantenimientos vencidos (fecha pasada y aún pendientes)
    mantenimientos_vencidos = (
        db.session.query(Mantenimiento)
        .join(Activo)
        .filter(
            Activo.clase_id.in_([2, 3, 4]),
            Mantenimiento.estado.in_(["Pendiente", "En Proceso"]),
            Mantenimiento.fecha_mantenimiento < hoy,
        )
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
        .all()
    )

    # Formatear respuesta
    alertas = {
        "vencidos": [],
        "proximos": [],
        "total_vencidos": len(mantenimientos_vencidos),
        "total_proximos": len(mantenimientos_proximos),
    }

    for m in mantenimientos_vencidos:
        dias_vencido = (hoy - m.fecha_mantenimiento).days
        alertas["vencidos"].append(
            {
                "id": m.id,
                "activo": m.activo.nombre_activo,
                "placa": m.activo.placa_codigo_interno,
                "tipo": m.tipo.nombre,
                "fecha": m.fecha_mantenimiento.strftime("%d/%m/%Y"),
                "dias_vencido": dias_vencido,
                "estado": m.estado,
                "url": url_for("mantenimientos.ver_mantenimiento", id=m.id),
            }
        )

    for m in mantenimientos_proximos:
        dias_restantes = (m.fecha_mantenimiento - hoy).days
        alertas["proximos"].append(
            {
                "id": m.id,
                "activo": m.activo.nombre_activo,
                "placa": m.activo.placa_codigo_interno,
                "tipo": m.tipo.nombre,
                "fecha": m.fecha_mantenimiento.strftime("%d/%m/%Y"),
                "dias_restantes": dias_restantes,
                "estado": m.estado,
                "prioridad": (
                    "alta"
                    if dias_restantes <= 3
                    else "media" if dias_restantes <= 7 else "normal"
                ),
                "url": url_for("mantenimientos.ver_mantenimiento", id=m.id),
            }
        )

    return jsonify(alertas)


@mantenimientos_bp.route("/alertas-mantenimientos")
@login_required
def alertas_mantenimientos():
    """Vista de alertas de mantenimientos próximos y vencidos."""
    hoy = datetime.now().date()
    fecha_limite = hoy + timedelta(days=15)

    # Obtener mantenimientos vencidos
    mantenimientos_vencidos = (
        db.session.query(Mantenimiento)
        .join(Activo)
        .filter(
            Activo.clase_id.in_([2, 3, 4]),
            Mantenimiento.estado.in_(["Pendiente", "En Proceso"]),
            Mantenimiento.fecha_mantenimiento < hoy,
        )
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
        .all()
    )

    # Obtener mantenimientos próximos (15 días)
    mantenimientos_proximos = (
        db.session.query(Mantenimiento)
        .join(Activo)
        .filter(
            Activo.clase_id.in_([2, 3, 4]),
            Mantenimiento.estado.in_(["Pendiente", "En Proceso"]),
            Mantenimiento.fecha_mantenimiento >= hoy,
            Mantenimiento.fecha_mantenimiento <= fecha_limite,
        )
        .order_by(Mantenimiento.fecha_mantenimiento.asc())
        .all()
    )

    return render_template(
        "mantenimientos/alertas/alertas_mantenimientos.html",
        mantenimientos_vencidos=mantenimientos_vencidos,
        mantenimientos_proximos=mantenimientos_proximos,
        hoy=hoy,
        active_page="mantenimientos",
    )


# ==============================================================================
# RUTAS DE GESTIÓN DE DOCUMENTOS ESCANEADOS
# ==============================================================================


@mantenimientos_bp.route(
    "/mantenimientos/<int:mantenimiento_id>/documentos/subir", methods=["GET", "POST"]
)
@login_required
def subir_documento(mantenimiento_id):
    """Sube un documento escaneado a un mantenimiento."""
    mantenimiento = Mantenimiento.query.get_or_404(mantenimiento_id)

    if request.method == "POST":
        try:
            # Validar que se subió un archivo
            if "archivo" not in request.files:
                flash("No se seleccionó ningún archivo", "error")
                return redirect(request.url)

            archivo = request.files["archivo"]

            if archivo.filename == "":
                flash("No se seleccionó ningún archivo", "error")
                return redirect(request.url)

            # Validar extensión
            extensiones_permitidas = {
                "pdf",
                "jpg",
                "jpeg",
                "png",
                "gif",
                "xlsx",
                "xls",
                "doc",
                "docx",
            }
            extension = archivo.filename.rsplit(".", 1)[-1].lower()

            if extension not in extensiones_permitidas:
                flash(
                    f'Tipo de archivo no permitido. Extensiones válidas: {", ".join(extensiones_permitidas)}',
                    "error",
                )
                return redirect(request.url)

            # Determinar tipo de documento
            tipo_documento = "otro"
            if extension == "pdf":
                tipo_documento = "pdf"
            elif extension in {"jpg", "jpeg", "png", "gif"}:
                tipo_documento = "imagen"
            elif extension in {"xlsx", "xls"}:
                tipo_documento = "excel"
            elif extension in {"doc", "docx"}:
                tipo_documento = "word"

            # Generar nombre de archivo seguro
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            placa = mantenimiento.activo.placa_codigo_interno
            nombre_seguro = secure_filename(
                f"mant_{mantenimiento_id}_{placa}_{timestamp}.{extension}"
            )

            # Crear directorio si no existe
            from flask import current_app

            upload_folder = os.path.join(
                current_app.root_path, "static", "uploads", "mantenimientos_documentos"
            )
            os.makedirs(upload_folder, exist_ok=True)

            # Guardar archivo
            ruta_completa = os.path.join(upload_folder, nombre_seguro)
            archivo.save(ruta_completa)

            # Obtener tamaño del archivo
            tamano = os.path.getsize(ruta_completa)

            # Crear registro en BD
            documento = MantenimientoDocumento(
                mantenimiento_id=mantenimiento_id,
                nombre_archivo=archivo.filename,
                ruta_archivo=f"uploads/mantenimientos_documentos/{nombre_seguro}",
                tipo_documento=tipo_documento,
                tamano_archivo=tamano,
                fecha_documento=(
                    datetime.strptime(
                        request.form.get("fecha_documento"), "%Y-%m-%d"
                    ).date()
                    if request.form.get("fecha_documento")
                    else None
                ),
                tecnico_responsable=request.form.get("tecnico_responsable"),
                descripcion=request.form.get("descripcion"),
                uploaded_by=current_user.id,
            )

            db.session.add(documento)
            db.session.commit()

            flash(f'Documento "{archivo.filename}" subido exitosamente', "success")
            return redirect(
                url_for("mantenimientos.ver_mantenimiento", id=mantenimiento_id)
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Error al subir el documento: {str(e)}", "error")
            return redirect(request.url)

    # GET - Mostrar formulario
    return render_template(
        "mantenimientos/documentos/subir_documento.html",
        mantenimiento=mantenimiento,
        active_page="mantenimientos",
    )


@mantenimientos_bp.route("/mantenimientos/documentos/<int:doc_id>/ver")
@login_required
def ver_documento(doc_id):
    """Muestra un documento en el navegador."""
    documento = MantenimientoDocumento.query.get_or_404(doc_id)

    from flask import current_app

    directory = os.path.join(current_app.root_path, "static")

    return send_from_directory(directory, documento.ruta_archivo, as_attachment=False)


@mantenimientos_bp.route("/mantenimientos/documentos/<int:doc_id>/descargar")
@login_required
def descargar_documento(doc_id):
    """Descarga un documento."""
    documento = MantenimientoDocumento.query.get_or_404(doc_id)

    from flask import current_app

    directory = os.path.join(current_app.root_path, "static")

    return send_from_directory(
        directory,
        documento.ruta_archivo,
        as_attachment=True,
        download_name=documento.nombre_archivo,
    )


@mantenimientos_bp.route(
    "/mantenimientos/documentos/<int:doc_id>/eliminar", methods=["POST"]
)
@login_required
@role_required("admin")
def eliminar_documento(doc_id):
    """Elimina un documento (solo administradores)."""
    documento = MantenimientoDocumento.query.get_or_404(doc_id)
    mantenimiento_id = documento.mantenimiento_id

    try:
        # Eliminar archivo físico
        from flask import current_app

        ruta_completa = os.path.join(
            current_app.root_path, "static", documento.ruta_archivo
        )

        if os.path.exists(ruta_completa):
            os.remove(ruta_completa)

        # Eliminar registro de BD
        db.session.delete(documento)
        db.session.commit()

        flash("Documento eliminado exitosamente", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el documento: {str(e)}", "error")

    return redirect(url_for("mantenimientos.ver_mantenimiento", id=mantenimiento_id))


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
    upload_folder = os.path.join(
        current_app.root_path, "static", "uploads", "hojas_vida_equipos"
    )

    # Crear directorio si no existe
    os.makedirs(upload_folder, exist_ok=True)

    for i in range(1, 4):
        foto_key = f"foto_{i}"
        if foto_key in files:
            file = files[foto_key]
            if file and file.filename:
                # Generar nombre seguro para el archivo
                filename = secure_filename(
                    f"{placa_activo}_foto_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}"
                )
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                # Guardar ruta relativa
                fotos_urls[foto_key] = f"uploads/hojas_vida_equipos/{filename}"

    return fotos_urls
