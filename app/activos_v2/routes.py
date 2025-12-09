# ==============================================================================
# RUTAS DEL MÓDULO ACTIVOS V2
# ==============================================================================

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from app.activos_v2 import activos_v2_bp
from app.models import (
    Activo,
    ClaseActivo,
    Funcionario,
    Mantenimiento,
    MantenimientoFoto,
    MantenimientoTipo,
    User,
    db,
    Proveedor,
    MovimientoActivo,
    Movimiento,
)
from app.activos_v2.forms import MantenimientoForm, ActivoEditForm
from app.activos_v2.utils import (
    save_uploaded_file,
    get_upload_path,
    format_currency,
    get_estado_badge_class,
    get_tipo_mantenimiento_badge_class,
)
from app.activos_v2.atributos_dinamicos import (
    get_atributos_por_clase,
    ATRIBUTOS_POR_CLASE,
)
from datetime import datetime
import os


# ==============================================================================
# RUTA PRINCIPAL: LISTADO CON FILTROS
# ==============================================================================
@activos_v2_bp.route("/listado")
@login_required
def listado():
    """
    Vista principal del listado de activos con filtros avanzados.
    Soporta paginación para manejar eficientemente 6000+ registros.
    """
    # Parámetros de paginación
    page = request.args.get("page", 1, type=int)
    per_page = 50

    # Parámetros de filtrado
    nombre = request.args.get("nombre", "").strip()
    placa = request.args.get("placa", "").strip()
    clase_id = request.args.get("clase_id", type=int)
    ubicacion_id = request.args.get("ubicacion_id", type=int)
    estado = request.args.get("estado", "").strip()

    # Query base con joins optimizados
    query = Activo.query.join(
        ClaseActivo, Activo.clase_id == ClaseActivo.id, isouter=True
    )

    # Aplicar filtros dinámicamente
    if nombre:
        query = query.filter(Activo.nombre_activo.ilike(f"%{nombre}%"))

    if placa:
        query = query.filter(Activo.placa_codigo_interno.ilike(f"%{placa}%"))

    if clase_id and clase_id > 0:
        query = query.filter(Activo.clase_id == clase_id)

    if ubicacion_id:  # ubicacion_id es ahora el texto de ubicación
        query = query.filter(Activo.ubicacion.ilike(f"%{ubicacion_id}%"))

    if estado:
        query = query.filter(Activo.estado == estado)

    # Ordenar por placa descendente (más recientes primero)
    query = query.order_by(Activo.id.desc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Cargar datos para los filtros
    clases = ClaseActivo.query.order_by(ClaseActivo.nombre_clase).all()

    # Obtener ubicaciones únicas desde los activos (como son String)
    ubicaciones_raw = (
        db.session.query(Activo.ubicacion)
        .distinct()
        .filter(Activo.ubicacion.isnot(None))
        .all()
    )
    ubicaciones = [{"nombre": ub[0]} for ub in ubicaciones_raw if ub[0]]

    estados = [
        "Operativo",
        "En reparación",
        "Dado de baja",
        "En mantenimiento",
        "Disponible",
    ]

    # Estadísticas rápidas
    total_activos = Activo.query.count()
    operativos = Activo.query.filter_by(estado="Operativo").count()

    return render_template(
        "activos_v2/listado.html",
        activos=pagination.items,
        pagination=pagination,
        clases=clases,
        ubicaciones=ubicaciones,
        estados=estados,
        total_activos=total_activos,
        operativos=operativos,
        # Mantener valores de filtros en el formulario
        filtros={
            "nombre": nombre,
            "placa": placa,
            "clase_id": clase_id,
            "ubicacion_id": ubicacion_id,
            "estado": estado,
        },
    )


# ==============================================================================
# VISTA DETALLADA DE ACTIVO
# ==============================================================================
@activos_v2_bp.route("/<int:id>/detalle")
@login_required
def ver_detalle(id):
    """
    Vista detallada de un activo con tabs:
    - Información general
    - Historial de mantenimientos
    - Historial de movimientos
    """
    activo = Activo.query.get_or_404(id)

    # Cargar mantenimientos ordenados por fecha descendente
    mantenimientos = (
        Mantenimiento.query.filter_by(activo_id=id)
        .order_by(Mantenimiento.fecha_mantenimiento.desc())
        .all()
    )

    # Cargar últimos movimientos
    # Movimiento no tiene activo_id directo, usa relación many-to-many a través de MovimientoActivo
    from app.models import Movimiento, MovimientoActivo

    movimientos = (
        Movimiento.query.join(
            MovimientoActivo, Movimiento.id == MovimientoActivo.movimiento_id
        )
        .filter(MovimientoActivo.activo_id == id)
        .order_by(Movimiento.fecha.desc())
        .limit(10)
        .all()
    )

    # Formulario de mantenimiento
    form = MantenimientoForm()

    return render_template(
        "activos_v2/ver_detalle.html",
        activo=activo,
        mantenimientos=mantenimientos,
        movimientos=movimientos,
        form=form,
        get_estado_badge_class=get_estado_badge_class,
        get_tipo_mantenimiento_badge_class=get_tipo_mantenimiento_badge_class,
    )


# ==============================================================================
# AGREGAR MANTENIMIENTO
# ==============================================================================
@activos_v2_bp.route("/<int:activo_id>/mantenimiento/nuevo", methods=["POST"])
@login_required
def agregar_mantenimiento(activo_id):
    """
    Registra un nuevo mantenimiento para un activo.
    Soporta upload múltiple de fotos.
    """
    activo = Activo.query.get_or_404(activo_id)
    form = MantenimientoForm()

    if form.validate_on_submit():
        try:
            # Buscar o crear el tipo de mantenimiento
            tipo_nombre = form.tipo_mantenimiento.data
            tipo = MantenimientoTipo.query.filter_by(nombre=tipo_nombre).first()

            if not tipo:
                tipo = MantenimientoTipo(nombre=tipo_nombre)
                db.session.add(tipo)
                db.session.flush()

            # Crear registro de mantenimiento con la estructura existente
            mantenimiento = Mantenimiento(
                activo_id=activo_id,
                tipo_id=tipo.id,
                fecha_mantenimiento=form.fecha_mantenimiento.data,
                observaciones=form.descripcion.data,  # Mapear descripción a observaciones
                usuario_id=current_user.id,
                estado="Completado",
            )

            # Agregar info adicional en atributos_reporte_json
            mantenimiento.atributos_reporte_json = {
                "tecnico_nombre": form.tecnico_nombre.data,
                "tecnico_empresa": form.tecnico_empresa.data,
                "costo": str(form.costo.data) if form.costo.data else None,
                "proximo_mantenimiento": (
                    form.proximo_mantenimiento.data.isoformat()
                    if form.proximo_mantenimiento.data
                    else None
                ),
                "observaciones_adicionales": form.observaciones.data,
            }

            db.session.add(mantenimiento)
            db.session.flush()  # Obtener el ID sin commitear

            # Guardar fotos si las hay
            fotos_guardadas = 0
            if form.fotos.data:
                upload_folder = get_upload_path("mantenimientos", mantenimiento.id)

                for foto in form.fotos.data:
                    if foto and foto.filename:
                        filepath, filename, file_size = save_uploaded_file(
                            foto, upload_folder
                        )

                        if filepath:
                            foto_obj = MantenimientoFoto(
                                mantenimiento_id=mantenimiento.id,
                                ruta_foto=filepath,  # Usar ruta_foto según el modelo existente
                                descripcion=filename,
                            )
                            db.session.add(foto_obj)
                            fotos_guardadas += 1

            db.session.commit()

            flash(
                f"Mantenimiento registrado exitosamente. {fotos_guardadas} fotos guardadas.",
                "success",
            )
            return redirect(
                url_for("activos_v2.ver_detalle", id=activo_id) + "#tab-mantenimientos"
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Error al guardar el mantenimiento: {str(e)}", "danger")
            return redirect(url_for("activos_v2.ver_detalle", id=activo_id))

    else:
        # Mostrar errores de validación
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "warning")

    return redirect(url_for("activos_v2.ver_detalle", id=activo_id))


# ==============================================================================
# EDITAR ACTIVO
# ==============================================================================
@activos_v2_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    """
    Formulario completo de edición sin wizard.
    """
    activo = Activo.query.get_or_404(id)
    form = ActivoEditForm(obj=activo)

    # Cargar opciones para SelectFields
    form.clase_id.choices = [(0, "-- Seleccione --")] + [
        (c.id, c.nombre_clase)
        for c in ClaseActivo.query.order_by(ClaseActivo.nombre_clase).all()
    ]
    form.proveedor_id.choices = [(0, "-- Seleccione --")] + [
        (p.id, p.razon_social)
        for p in Proveedor.query.order_by(Proveedor.razon_social).all()
    ]
    # El campo de funcionario se maneja con búsqueda dinámica (ver plantilla)

    if request.method == "POST" and form.validate_on_submit():
        try:
            # Actualizar campos básicos
            activo.nombre_activo = form.nombre_activo.data
            activo.placa_codigo_interno = form.placa_codigo_interno.data
            activo.clase_id = form.clase_id.data if form.clase_id.data > 0 else None
            activo.estado = form.estado.data
            activo.ubicacion = form.ubicacion.data
            activo.funcionario_id = (
                form.funcionario_id.data
                if form.funcionario_id.data and int(form.funcionario_id.data) > 0
                else None
            )
            activo.observaciones = form.observaciones.data

            # Actualizar campos de adquisición
            activo.created_at = (
                form.fecha_compra.data
            )  # Usamos created_at como fecha de compra
            activo.valor_comercial = form.valor_compra.data
            activo.proveedor_id = (
                form.proveedor_id.data
                if form.proveedor_id.data and int(form.proveedor_id.data) > 0
                else None
            )

            # Manejar subida de documentos
            upload_folder = get_upload_path("documentos_activos", activo.id)
            if form.orden_compra.data:
                activo.ruta_orden_compra, _, _ = save_uploaded_file(
                    form.orden_compra.data, upload_folder
                )
            if form.factura.data:
                activo.ruta_factura, _, _ = save_uploaded_file(
                    form.factura.data, upload_folder
                )
            if form.documento_soporte.data:
                activo.ruta_contrato_arriendo, _, _ = save_uploaded_file(
                    form.documento_soporte.data, upload_folder
                )

            # Guardar atributos dinámicos según clase
            if activo.clase_id:
                atributos_dinamicos = {}
                atributos_spec = get_atributos_por_clase(activo.clase_id)

                for attr_spec in atributos_spec:
                    attr_name = attr_spec["name"]
                    attr_value = request.form.get(f"attr_{attr_name}")

                    if attr_value:
                        atributos_dinamicos[attr_name] = attr_value
                activo.atributos_dinamicos_json = (
                    atributos_dinamicos if atributos_dinamicos else None
                )

            db.session.commit()
            flash("Activo actualizado correctamente", "success")
            return redirect(url_for("activos_v2.ver_detalle", id=id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {str(e)}", "danger")

    # Pre-rellenar el formulario con datos existentes en el GET
    if request.method == "GET":
        form.fecha_compra.data = activo.created_at
        form.valor_compra.data = activo.valor_comercial

        # Fetch the proveedor_id from the associated DetalleEntrega
        proveedor_id_from_movimiento = None
        # Find the earliest 'Entrega' movement for this activo
        # This assumes an activo has one primary 'Entrega' movement for its acquisition
        movimiento_activo_record = (
            db.session.query(MovimientoActivo)
            .filter_by(activo_id=activo.id)
            .join(Movimiento)
            .filter(Movimiento.tipo_movimiento == "Entrega")
            .order_by(Movimiento.fecha.asc())
            .first()
        )

        if (
            movimiento_activo_record
            and movimiento_activo_record.movimiento.detalle_entrega
        ):
            proveedor_id_from_movimiento = (
                movimiento_activo_record.movimiento.detalle_entrega.proveedor_id
            )

        form.proveedor_id.data = proveedor_id_from_movimiento

    # Obtener atributos actuales del activo para mostrar en el formulario
    atributos_actuales = (
        activo.atributos_dinamicos_json if activo.atributos_dinamicos_json else {}
    )

    return render_template(
        "activos_v2/editar.html",
        activo=activo,
        form=form,
        atributos_actuales=atributos_actuales,
    )


# ==============================================================================
# API: DATATABLES (Para AJAX)
# ==============================================================================
@activos_v2_bp.route("/api/datatable", methods=["POST"])
@login_required
def api_datatable():
    """
    Endpoint para DataTables con server-side processing.
    Optimizado para manejar 6000+ registros.
    """
    # Parámetros de DataTables
    draw = request.form.get("draw", type=int)
    start = request.form.get("start", type=int)
    length = request.form.get("length", type=int)
    search_value = request.form.get("search[value]", "")

    # Filtros adicionales
    nombre = request.form.get("nombre", "")
    placa = request.form.get("placa", "")
    clase_id = request.form.get("clase_id", type=int)
    ubicacion_id = request.form.get("ubicacion_id", type=int)
    estado = request.form.get("estado", "")

    # Query base
    query = Activo.query.join(
        ClaseActivo, Activo.clase_id == ClaseActivo.id, isouter=True
    )

    # Búsqueda global
    if search_value:
        query = query.filter(
            or_(
                Activo.nombre_activo.ilike(f"%{search_value}%"),
                Activo.placa_codigo_interno.ilike(f"%{search_value}%"),
                ClaseActivo.nombre_clase.ilike(f"%{search_value}%"),
                Activo.ubicacion.ilike(f"%{search_value}%"),
            )
        )

    # Filtros específicos
    if nombre:
        query = query.filter(Activo.nombre_activo.ilike(f"%{nombre}%"))
    if placa:
        query = query.filter(Activo.placa_codigo_interno.ilike(f"%{placa}%"))
    if clase_id:
        query = query.filter(Activo.clase_id == clase_id)
    if ubicacion_id:  # Es String, no FK
        query = query.filter(Activo.ubicacion.ilike(f"%{ubicacion_id}%"))
    if estado:
        query = query.filter(Activo.estado == estado)

    # Total de registros
    total_records = Activo.query.count()
    filtered_records = query.count()

    # Paginación
    activos = query.offset(start).limit(length).all()

    # Formatear datos
    data = []
    for activo in activos:
        data.append(
            {
                "placa_codigo_interno": activo.placa_codigo_interno or "S/N",
                "nombre_activo": activo.nombre_activo,
                "clase_nombre": activo.clase.nombre_clase if activo.clase else "N/A",
                "ubicacion_nombre": activo.ubicacion or "N/A",  # Es String, no objeto
                "estado": activo.estado or "N/A",
                "acciones": f"""
                <a href="{url_for('activos_v2.ver_detalle', id=activo.id)}" class="btn btn-sm btn-info">Ver</a>
                <a href="{url_for('activos_v2.editar', id=activo.id)}" class="btn btn-sm btn-warning">Editar</a>
            """,
            }
        )

    return jsonify(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )


# ==============================================================================
# API: ATRIBUTOS DINÁMICOS POR CLASE
# ==============================================================================
@activos_v2_bp.route("/api/clase/<int:clase_id>/atributos", methods=["GET"])
@login_required
def api_clase_atributos(clase_id):
    """
    Endpoint API para obtener los atributos dinámicos de una clase específica.
    Utilizado por Alpine.js para cargar campos dinámicamente cuando cambia la clase.
    """
    try:
        atributos = get_atributos_por_clase(clase_id)
        return jsonify(atributos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# API: BÚSQUEDA DE FUNCIONARIOS
# ==============================================================================
@activos_v2_bp.route("/api/funcionarios/search", methods=["GET"])
@login_required
def api_funcionarios_search():
    """
    Endpoint API para buscar funcionarios por nombre o cédula.
    Utilizado por Alpine.js para la búsqueda de responsables.
    """
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])

    search_term = f"%{q}%"

    # Buscar por nombre, apellido o cédula de forma robusta
    query = Funcionario.query.filter(
        or_(
            func.concat(Funcionario.nombres, " ", Funcionario.apellidos).ilike(
                search_term
            ),
            Funcionario.cedula.ilike(search_term),
        )
    ).limit(10)

    funcionarios = query.all()

    results = [
        {"id": f.id, "nombres": f.nombres, "apellidos": f.apellidos, "cedula": f.cedula}
        for f in funcionarios
    ]

    return jsonify(results)


# ==============================================================================
# ELIMINAR ACTIVO
# ==============================================================================
@activos_v2_bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar_activo(id):
    """
    Elimina un activo de la base de datos.
    """
    if not hasattr(current_user, "rol") or current_user.rol != "Admin":
        flash("No tienes permiso para realizar esta acción.", "danger")
        return redirect(url_for("activos_v2.listado"))

    activo = Activo.query.get_or_404(id)
    try:
        db.session.delete(activo)
        db.session.commit()
        flash("Activo eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el activo: {str(e)}", "danger")

    return redirect(url_for("activos_v2.listado"))
