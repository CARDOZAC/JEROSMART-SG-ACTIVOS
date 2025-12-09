"""
Módulo para la generación de reportes contables y de gestión.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, current_app, make_response
import weasyprint
from sqlalchemy import select
from ..extensions import db
from ..models import Activo
from ..decorators import login_required, role_required

reportes_bp = Blueprint(
    "reportes", __name__, template_folder="templates", url_prefix="/reportes"
)


@reportes_bp.route("/")
@login_required
@role_required("Admin")
def index():
    """Página principal del módulo de reportes."""
    return render_template("reportes/index.html", active_page="reportes")


@reportes_bp.route("/general_activos")
@login_required
@role_required("Admin")
def reporte_general_activos():
    """Genera un reporte de todos los activos."""
    formato = request.args.get("formato", "html")

    stmt = select(Activo).order_by(Activo.nombre_activo)
    activos = db.session.execute(stmt).scalars().all()

    context = {
        "activos": activos,
        "generado": datetime.now(timezone.utc)
        .astimezone()
        .strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema",  # Placeholder
    }

    if formato == "pdf":
        html = render_template("pdf_templates/reporte_general_pdf.html", **context)
        pdf = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="Reporte_General_Activos_{datetime.now().strftime("%Y%m%d")}.pdf"'
        )
        return response

    elif formato == "xlsx":
        from openpyxl import Workbook
        from io import BytesIO

        wb = Workbook()
        ws = wb.active
        ws.title = "Activos"

        # Encabezados
        headers = [
            "Placa/Código",
            "Nombre del Activo",
            "Marca",
            "Modelo",
            "Serie",
            "Estado",
            "Ubicación",
        ]
        ws.append(headers)

        # Datos
        for activo in activos:
            ws.append(
                [
                    activo.placa_codigo_interno,
                    activo.nombre_activo,
                    activo.marca,
                    activo.modelo,
                    activo.serie,
                    activo.estado,
                    activo.ubicacion,
                ]
            )

        # Guardar en un buffer de memoria
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="Reporte_General_Activos_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        )
        return response

    return render_template(
        "reportes/reporte_general.html", **context, active_page="reportes"
    )


@reportes_bp.route("/depreciacion")
@login_required
@role_required("Admin")
def reporte_depreciacion():
    """
    Genera y muestra un reporte de depreciación para todos los activos propios.
    Permite la exportación a PDF y Excel.
    """
    formato = request.args.get("formato", "html")

    # 1. Obtener los activos relevantes para el reporte
    stmt = (
        select(Activo)
        .where(
            Activo.tipo_propiedad == "Propio",
            Activo.valor_comercial.isnot(None),
            Activo.valor_comercial > 0,
        )
        .order_by(Activo.nombre_activo)
    )
    activos = db.session.execute(stmt).scalars().all()

    # --- Lógica de negocio robusta (Estilo Gosling) ---
    if not activos and formato == "html":
        return render_template(
            "reportes/reporte_depreciacion.html",
            activos=[],
            totales={"valor_comercial": 0, "depreciacion": 0, "valor_libros": 0},
        )

    # 2. Calcular totales para el resumen
    total_valor_comercial = sum(a.valor_comercial for a in activos)
    total_depreciacion = sum(a.depreciacion_acumulada for a in activos)
    total_valor_libros = sum(a.valor_en_libros for a in activos)

    context = {
        "activos": activos,
        "totales": {
            "valor_comercial": total_valor_comercial,
            "depreciacion": total_depreciacion,
            "valor_libros": total_valor_libros,
        },
        "generado": datetime.now(timezone.utc)
        .astimezone()
        .strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema",  # Placeholder
    }

    if formato == "pdf":
        html = render_template(
            "pdf_templates/reporte_depreciacion_pdf.html", **context
        )
        pdf = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="Reporte_Depreciacion_{datetime.now().strftime("%Y%m%d")}.pdf"'
        )
        return response

    elif formato == "xlsx":
        from openpyxl import Workbook
        from io import BytesIO

        wb = Workbook()
        ws = wb.active
        ws.title = "Depreciación"

        headers = [
            "Placa/Código",
            "Nombre del Activo",
            "Valor Comercial",
            "Depreciación Acumulada",
            "Valor en Libros",
        ]
        ws.append(headers)

        for activo in activos:
            ws.append(
                [
                    activo.placa_codigo_interno,
                    activo.nombre_activo,
                    activo.valor_comercial,
                    activo.depreciacion_acumulada,
                    activo.valor_en_libros,
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="Reporte_Depreciacion_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        )
        return response

    return render_template(
        "reportes/reporte_depreciacion.html", **context, active_page="reportes"
    )


@reportes_bp.route("/movimientos")
@login_required
@role_required("Admin")
def reporte_movimientos():
    """Filtra y genera reportes de movimientos de activos."""
    formato = request.args.get("formato", "html")
    tipo_movimiento = request.args.get("tipo_movimiento", "")
    fecha_inicio_str = request.args.get("fecha_inicio", "")
    fecha_fin_str = request.args.get("fecha_fin", "")

    from ..models import Movimiento

    stmt = select(Movimiento).order_by(Movimiento.fecha.desc())

    conditions = []
    if tipo_movimiento:
        conditions.append(Movimiento.tipo_movimiento == tipo_movimiento)
    if fecha_inicio_str:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        conditions.append(Movimiento.fecha >= fecha_inicio)
    if fecha_fin_str:
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
        conditions.append(Movimiento.fecha <= fecha_fin)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    movimientos = db.session.execute(stmt).scalars().all()

    context = {
        "movimientos": movimientos,
        "generado": datetime.now(timezone.utc)
        .astimezone()
        .strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema",
        "filtros": {
            "tipo_movimiento": tipo_movimiento,
            "fecha_inicio": fecha_inicio_str,
            "fecha_fin": fecha_fin_str,
        },
    }

    if formato == "pdf":
        html = render_template("pdf_templates/reporte_movimientos_pdf.html", **context)
        pdf = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="Reporte_Movimientos_{datetime.now().strftime("%Y%m%d")}.pdf"'
        )
        return response

    elif formato == "xlsx":
        from openpyxl import Workbook
        from io import BytesIO

        wb = Workbook()
        ws = wb.active
        ws.title = "Movimientos"

        headers = [
            "ID",
            "Tipo",
            "Fecha",
            "Origen",
            "Destino",
            "Activos Involucrados",
        ]
        ws.append(headers)

        for movimiento in movimientos:
            ws.append(
                [
                    movimiento.id,
                    movimiento.tipo_movimiento,
                    movimiento.fecha.strftime("%d/%m/%Y"),
                    movimiento.origen,
                    movimiento.destino,
                    len(movimiento.activos),
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="Reporte_Movimientos_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        )
        return response

    return render_template(
        "reportes/reporte_movimientos.html", **context, active_page="reportes"
    )


@reportes_bp.route("/activos_ajenos")
@login_required
@role_required("Admin")
def reporte_activos_ajenos():
    """Genera un reporte de todos los activos ajenos."""
    formato = request.args.get("formato", "html")

    stmt = select(Activo).where(Activo.tipo_propiedad == "Ajeno").order_by(Activo.nombre_activo)
    activos = db.session.execute(stmt).scalars().all()

    context = {
        "activos": activos,
        "generado": datetime.now(timezone.utc)
        .astimezone()
        .strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema",
    }

    if formato == "pdf":
        html = render_template("pdf_templates/reporte_activos_ajenos_pdf.html", **context)
        pdf = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="Reporte_Activos_Ajenos_{datetime.now().strftime("%Y%m%d")}.pdf"'
        )
        return response

    elif formato == "xlsx":
        from openpyxl import Workbook
        from io import BytesIO

        wb = Workbook()
        ws = wb.active
        ws.title = "Activos Ajenos"

        headers = [
            "Placa/Código",
            "Nombre del Activo",
            "Propietario",
            "Condición de Tenencia",
            "Estado",
            "Ubicación",
        ]
        ws.append(headers)

        for activo in activos:
            ws.append(
                [
                    activo.placa_codigo_interno,
                    activo.nombre_activo,
                    activo.propietario_ajeno,
                    activo.condicion_tenencia,
                    activo.estado,
                    activo.ubicacion,
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="Reporte_Activos_Ajenos_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        )
        return response

    return render_template(
        "reportes/reporte_activos_ajenos.html", **context, active_page="reportes"
    )


@reportes_bp.route("/mantenimientos")
@login_required
@role_required("Admin")
def reporte_mantenimientos():
    """Filtra y genera reportes de mantenimientos de activos."""
    formato = request.args.get("formato", "html")
    clase_activo_id = request.args.get("clase_activo", "")

    from ..models import Mantenimiento

    stmt = select(Mantenimiento).order_by(Mantenimiento.fecha_mantenimiento.desc())

    if clase_activo_id:
        stmt = stmt.join(Activo).where(Activo.clase_id == clase_activo_id)

    mantenimientos = db.session.execute(stmt).scalars().all()

    context = {
        "mantenimientos": mantenimientos,
        "generado": datetime.now(timezone.utc)
        .astimezone()
        .strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema",
        "filtros": {
            "clase_activo": clase_activo_id,
        },
    }

    if formato == "pdf":
        html = render_template("pdf_templates/reporte_mantenimientos_pdf.html", **context)
        pdf = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'inline; filename="Reporte_Mantenimientos_{datetime.now().strftime("%Y%m%d")}.pdf"'
        )
        return response

    elif formato == "xlsx":
        from openpyxl import Workbook
        from io import BytesIO

        wb = Workbook()
        ws = wb.active
        ws.title = "Mantenimientos"

        headers = [
            "ID",
            "Activo",
            "Fecha",
            "Tipo",
            "Realizado Por",
            "Costo",
        ]
        ws.append(headers)

        for mantenimiento in mantenimientos:
            ws.append(
                [
                    mantenimiento.id,
                    mantenimiento.activo.nombre_activo,
                    mantenimiento.fecha_mantenimiento.strftime("%d/%m/%Y"),
                    mantenimiento.tipo_mantenimiento,
                    mantenimiento.realizado_por,
                    mantenimiento.costo,
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="Reporte_Mantenimientos_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        )
        return response

    return render_template(
        "reportes/reporte_mantenimientos.html", **context, active_page="reportes"
    )
