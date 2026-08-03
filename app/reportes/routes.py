"""
Módulo para la generación de reportes contables y de gestión.
Incluye reportes de depreciación y comodatos.
"""
from datetime import datetime, timezone, date, timedelta
from flask import (
    Blueprint, render_template, request, current_app, make_response, jsonify
)
import weasyprint
from sqlalchemy import select, func, and_, or_
from ..extensions import db
from ..models import Activo, Movimiento, MovimientoActivo, DetalleComodato, Proveedor, ClaseActivo
from ..decorators import login_required
from ..permissions import require_permission
import io
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

reportes_bp = Blueprint(
    'reportes',
    __name__,
    template_folder='templates',
    url_prefix='/reportes'
)

@reportes_bp.route('/')
@login_required
@require_permission('ver_reportes', redirigir_a='main.index')
def index():
    """Página principal del módulo de reportes."""
    # --- Consulta para el gráfico de activos por clase ---
    # Objetivo: Contar cuántos activos hay en cada clase para visualización.
    # Se usa un LEFT JOIN para asegurar que incluso clases sin activos aparezcan (con conteo 0).
    activos_por_clase_query = (
        db.session.query(
            ClaseActivo.nombre_clase,
            func.count(Activo.id)
        )
        .outerjoin(Activo, ClaseActivo.id == Activo.clase_id)
        .group_by(ClaseActivo.nombre_clase)
        .order_by(ClaseActivo.nombre_clase)
        .all()
    )
    
    # Formatear los datos para que sean consumibles por Chart.js (y `tojson`)
    # Se crea un diccionario con dos listas: una para las etiquetas y otra para los datos.
    activos_por_clase_data = {
        'labels': [row[0] for row in activos_por_clase_query],
        'data': [row[1] for row in activos_por_clase_query]
    }

    # --- Consulta para el gráfico de movimientos por tipo ---
    movimientos_por_tipo_query = (
        db.session.query(
            Movimiento.tipo_movimiento,
            func.count(Movimiento.id)
        )
        .group_by(Movimiento.tipo_movimiento)
        .order_by(Movimiento.tipo_movimiento)
        .all()
    )

    movimientos_por_tipo_data = {
        'labels': [row[0] for row in movimientos_por_tipo_query],
        'data': [row[1] for row in movimientos_por_tipo_query]
    }


    return render_template(
        'reportes/index.html',
        active_page='reportes',
        activos_por_clase=activos_por_clase_data,
        movimientos_por_tipo=movimientos_por_tipo_data
    )

@reportes_bp.route('/depreciacion', methods=['GET', 'POST'])
@login_required
@require_permission('ver_reportes', redirigir_a='main.index')
def reporte_depreciacion():
    """
    Genera y muestra un reporte de depreciación para todos los activos propios.
    Permite la exportación a PDF.
    """
    # 1. Obtener los activos relevantes para el reporte
    stmt = (
        select(Activo)
        .where(
            Activo.tipo_propiedad == 'Propio',
            Activo.valor_comercial.isnot(None),
            Activo.valor_comercial > 0
        )
        .order_by(Activo.nombre_activo)
    )
    activos = db.session.execute(stmt).scalars().all()

    # --- Lógica de negocio robusta (Estilo Gosling) ---
    # Si no hay activos que cumplan con los criterios, no se puede generar el reporte.
    # En lugar de fallar o mostrar una página vacía, informamos al usuario.
    if not activos:
        return render_template(
            'reportes/reporte_depreciacion.html',
            activos=[],
            totales={"valor_comercial": 0, "depreciacion": 0, "valor_libros": 0}
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
            "valor_libros": total_valor_libros
        },
        "generado": datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M:%S %Z"),
        "usuario": "Administrador del Sistema" # Placeholder
    }

    # 3. Si la solicitud es para generar un PDF
    if request.method == 'POST' and request.form.get('action') == 'generate_pdf':
        try:
            # Renderizar la plantilla específica para PDF
            html = render_template('pdf_templates/reporte_depreciacion_pdf.html', **context)
            
            # Generar el PDF con WeasyPrint
            pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()

            # Crear y devolver la respuesta PDF
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="Reporte_Depreciacion_{datetime.now().strftime("%Y%m%d")}.pdf"'
            return response

        except Exception as e:
            current_app.logger.error(f"Error generando PDF de depreciación: {e}")
            return "Error al generar el PDF.", 500

    # 4. Por defecto (GET), mostrar el reporte en HTML
    return render_template(
        'reportes/reporte_depreciacion.html',
        **context,
        active_page='reportes'
    )


# ==============================================================================
# REPORTES DE COMODATOS
# ==============================================================================

@reportes_bp.route('/comodatos/dashboard')
@login_required
def dashboard_comodatos():
    """
    Dashboard principal de comodatos con métricas y alertas.

    Métricas incluidas:
    - Total de comodatos activos
    - Comodatos próximos a vencer (30 días)
    - Comodatos vencidos
    - Valor total en comodato
    - Distribución por comodante
    """
    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=30)

    # Consulta de comodatos con su movimiento asociado.
    # NOTA: no incluir aquí `count(DISTINCT ...) OVER ()`: MySQL 8 no admite
    # DISTINCT dentro de una función de ventana (error 1235) y la página fallaba
    # con un 500. El total se calcula al recorrer los resultados.
    stmt = (
        select(
            DetalleComodato,
            Movimiento.fecha.label('fecha_movimiento'),
            Movimiento.id.label('movimiento_id')
        )
        .join(Movimiento, DetalleComodato.movimiento_id == Movimiento.id)
        .where(Movimiento.tipo_movimiento == 'Comodato')
    )

    comodatos = db.session.execute(stmt).all()

    # Calcular métricas
    total_comodatos = 0
    comodatos_vigentes = 0
    comodatos_proximos_vencer = 0
    comodatos_vencidos = 0
    valor_total = 0.0

    comodatos_por_estado = {}
    comodatos_por_comodante = {}
    alertas = []

    for row in comodatos:
        comodato = row.DetalleComodato
        total_comodatos += 1

        # Calcular estado
        if comodato.fecha_fin < hoy:
            comodatos_vencidos += 1
            estado = 'Vencido'
            alertas.append({
                'tipo': 'danger',
                'mensaje': f'Comodato {comodato.numero_contrato} VENCIDO desde {comodato.fecha_fin.strftime("%d/%m/%Y")}',
                'comodato_id': row.movimiento_id,
                'dias': (hoy - comodato.fecha_fin).days
            })
        elif comodato.fecha_fin <= fecha_alerta:
            comodatos_proximos_vencer += 1
            estado = 'Próximo a vencer'
            dias_restantes = (comodato.fecha_fin - hoy).days
            alertas.append({
                'tipo': 'warning',
                'mensaje': f'Comodato {comodato.numero_contrato} vence en {dias_restantes} días ({comodato.fecha_fin.strftime("%d/%m/%Y")})',
                'comodato_id': row.movimiento_id,
                'dias': dias_restantes
            })
        else:
            comodatos_vigentes += 1
            estado = 'Vigente'

        # Contadores por estado
        comodatos_por_estado[estado] = comodatos_por_estado.get(estado, 0) + 1

        # Contadores por comodante
        comodante = comodato.comodante_nombre
        if comodante not in comodatos_por_comodante:
            comodatos_por_comodante[comodante] = {'count': 0, 'valor': 0}
        comodatos_por_comodante[comodante]['count'] += 1

        # Sumar valor
        if comodato.valor_comercial_referencial:
            valor_total += comodato.valor_comercial_referencial
            comodatos_por_comodante[comodante]['valor'] += comodato.valor_comercial_referencial

    # Ordenar alertas por urgencia (días restantes)
    alertas.sort(key=lambda x: x['dias'])

    # Top 5 comodantes
    top_comodantes = sorted(
        comodatos_por_comodante.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:5]

    metricas = {
        'total': total_comodatos,
        'vigentes': comodatos_vigentes,
        'proximos_vencer': comodatos_proximos_vencer,
        'vencidos': comodatos_vencidos,
        'valor_total': valor_total,
        'por_estado': comodatos_por_estado,
        'top_comodantes': top_comodantes
    }

    return render_template(
        'reportes/dashboard_comodatos.html',
        metricas=metricas,
        alertas=alertas[:10],  # Mostrar solo las 10 más urgentes
        active_page='reportes'
    )


@reportes_bp.route('/comodatos/listado')
@login_required
def listado_comodatos():
    """
    Listado completo de comodatos con filtros avanzados.

    Filtros disponibles:
    - Estado: Vigente, Próximo a vencer, Vencido, Todos
    - Comodante: Filtro por proveedor
    - Fecha desde/hasta
    - Búsqueda por número de contrato
    """
    # Obtener parámetros de filtro
    filtro_estado = request.args.get('estado', 'todos')
    filtro_comodante = request.args.get('comodante', '')
    filtro_fecha_desde = request.args.get('fecha_desde', '')
    filtro_fecha_hasta = request.args.get('fecha_hasta', '')
    filtro_busqueda = request.args.get('q', '')

    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=30)

    # Construir query base
    stmt = (
        select(
            DetalleComodato,
            Movimiento.fecha.label('fecha_movimiento'),
            Movimiento.id.label('movimiento_id'),
            Proveedor.razon_social.label('proveedor_nombre')
        )
        .join(Movimiento, DetalleComodato.movimiento_id == Movimiento.id)
        .outerjoin(Proveedor, DetalleComodato.proveedor_id == Proveedor.id)
        .where(Movimiento.tipo_movimiento == 'Comodato')
    )

    # Aplicar filtros
    if filtro_busqueda:
        stmt = stmt.where(
            or_(
                DetalleComodato.numero_contrato.ilike(f'%{filtro_busqueda}%'),
                DetalleComodato.comodante_nombre.ilike(f'%{filtro_busqueda}%')
            )
        )

    if filtro_comodante:
        stmt = stmt.where(DetalleComodato.comodante_nombre.ilike(f'%{filtro_comodante}%'))

    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            stmt = stmt.where(DetalleComodato.fecha_inicio >= fecha_desde)
        except ValueError:
            pass

    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date()
            stmt = stmt.where(DetalleComodato.fecha_fin <= fecha_hasta)
        except ValueError:
            pass

    # Ordenar por fecha de fin (más próximos primero)
    stmt = stmt.order_by(DetalleComodato.fecha_fin.asc())

    # Ejecutar query
    resultados = db.session.execute(stmt).all()

    # Procesar resultados y aplicar filtro de estado
    comodatos_procesados = []
    for row in resultados:
        comodato = row.DetalleComodato

        # Determinar estado y clase CSS
        if comodato.fecha_fin < hoy:
            estado = 'Vencido'
            clase_estado = 'danger'
            dias = (hoy - comodato.fecha_fin).days
            mensaje_dias = f'Vencido hace {dias} días'
        elif comodato.fecha_fin <= fecha_alerta:
            estado = 'Próximo a vencer'
            clase_estado = 'warning'
            dias = (comodato.fecha_fin - hoy).days
            mensaje_dias = f'Vence en {dias} días'
        else:
            estado = 'Vigente'
            clase_estado = 'success'
            dias = (comodato.fecha_fin - hoy).days
            mensaje_dias = f'{dias} días restantes'

        # Aplicar filtro de estado
        if filtro_estado != 'todos':
            if filtro_estado == 'vigente' and estado != 'Vigente':
                continue
            elif filtro_estado == 'proximo' and estado != 'Próximo a vencer':
                continue
            elif filtro_estado == 'vencido' and estado != 'Vencido':
                continue

        comodatos_procesados.append({
            'comodato': comodato,
            'movimiento_id': row.movimiento_id,
            'fecha_movimiento': row.fecha_movimiento,
            'proveedor_nombre': row.proveedor_nombre,
            'estado': estado,
            'clase_estado': clase_estado,
            'dias': dias,
            'mensaje_dias': mensaje_dias
        })

    # Obtener lista de comodantes para el filtro
    comodantes = db.session.execute(
        select(DetalleComodato.comodante_nombre)
        .distinct()
        .order_by(DetalleComodato.comodante_nombre)
    ).scalars().all()

    return render_template(
        'reportes/listado_comodatos.html',
        comodatos=comodatos_procesados,
        comodantes=comodantes,
        filtros={
            'estado': filtro_estado,
            'comodante': filtro_comodante,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
            'q': filtro_busqueda
        },
        active_page='reportes'
    )


@reportes_bp.route('/comodatos/exportar/excel')
@login_required
def exportar_comodatos_excel():
    """
    Exporta el listado de comodatos a formato Excel (.xlsx).

    Incluye:
    - Hoja 1: Listado completo con todos los campos
    - Hoja 2: Resumen por comodante
    - Hoja 3: Alertas de vencimiento
    """
    if not EXCEL_AVAILABLE:
        return "Excel no está disponible. Instale openpyxl: pip install openpyxl", 500

    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=30)

    # Obtener datos
    stmt = (
        select(
            DetalleComodato,
            Movimiento.fecha.label('fecha_movimiento'),
            Movimiento.id.label('movimiento_id')
        )
        .join(Movimiento, DetalleComodato.movimiento_id == Movimiento.id)
        .where(Movimiento.tipo_movimiento == 'Comodato')
        .order_by(DetalleComodato.fecha_fin.asc())
    )

    resultados = db.session.execute(stmt).all()

    # Crear workbook
    wb = Workbook()

    # === HOJA 1: Listado Completo ===
    ws1 = wb.active
    ws1.title = "Comodatos"

    # Estilos
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Encabezados
    headers = [
        'N° Contrato', 'Estado', 'Comodante', 'NIT Comodante',
        'Fecha Inicio', 'Fecha Fin', 'Plazo (meses)', 'Días Restantes',
        'Ubicación', 'Responsable Interno', 'Valor Referencial',
        'Mantenimiento', 'Seguros', 'Renovación Auto'
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Datos
    row_num = 2
    comodatos_por_comodante = {}
    alertas = []

    for row in resultados:
        comodato = row.DetalleComodato

        # Calcular estado y días
        if comodato.fecha_fin < hoy:
            estado = 'VENCIDO'
            dias = -(hoy - comodato.fecha_fin).days
            fill_color = "FF0000"  # Rojo
        elif comodato.fecha_fin <= fecha_alerta:
            estado = 'PRÓXIMO A VENCER'
            dias = (comodato.fecha_fin - hoy).days
            fill_color = "FFA500"  # Naranja
            alertas.append((comodato.numero_contrato, comodato.comodante_nombre, dias))
        else:
            estado = 'VIGENTE'
            dias = (comodato.fecha_fin - hoy).days
            fill_color = "00FF00"  # Verde

        # Contador por comodante
        comodante = comodato.comodante_nombre
        if comodante not in comodatos_por_comodante:
            comodatos_por_comodante[comodante] = {'count': 0, 'valor': 0}
        comodatos_por_comodante[comodante]['count'] += 1
        if comodato.valor_comercial_referencial:
            comodatos_por_comodante[comodante]['valor'] += comodato.valor_comercial_referencial

        # Escribir fila
        data_row = [
            comodato.numero_contrato,
            estado,
            comodato.comodante_nombre,
            comodato.comodante_nit,
            comodato.fecha_inicio.strftime('%d/%m/%Y') if comodato.fecha_inicio else '',
            comodato.fecha_fin.strftime('%d/%m/%Y') if comodato.fecha_fin else '',
            comodato.plazo_meses or '',
            dias,
            comodato.ubicacion_bien,
            comodato.responsable_interno_nombre,
            comodato.valor_comercial_referencial or 0,
            comodato.mantenimiento_cargo or '',
            comodato.seguros_cargo or '',
            'Sí' if comodato.renovacion_automatica else 'No'
        ]

        for col_num, value in enumerate(data_row, 1):
            cell = ws1.cell(row=row_num, column=col_num, value=value)
            cell.border = border

            # Color de fondo para estado
            if col_num == 2:  # Columna Estado
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                if estado == 'VENCIDO':
                    cell.font = Font(color="FFFFFF", bold=True)

        row_num += 1

    # Ajustar anchos de columna
    for col in ws1.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            # str() en ambos lados: antes se medía con str(...) pero se asignaba
            # len(cell.value), que falla en celdas numéricas y dejaba el ancho sin
            # ajustar porque el bare except se tragaba el TypeError.
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = min(max_length + 2, 50)
        ws1.column_dimensions[column].width = adjusted_width

    # === HOJA 2: Resumen por Comodante ===
    ws2 = wb.create_sheet("Resumen por Comodante")

    ws2.cell(1, 1, "Comodante").fill = header_fill
    ws2.cell(1, 1).font = header_font
    ws2.cell(1, 2, "Cantidad").fill = header_fill
    ws2.cell(1, 2).font = header_font
    ws2.cell(1, 3, "Valor Total").fill = header_fill
    ws2.cell(1, 3).font = header_font

    row_num = 2
    for comodante, datos in sorted(comodatos_por_comodante.items(), key=lambda x: x[1]['count'], reverse=True):
        ws2.cell(row_num, 1, comodante)
        ws2.cell(row_num, 2, datos['count'])
        ws2.cell(row_num, 3, datos['valor'])
        row_num += 1

    # === HOJA 3: Alertas ===
    ws3 = wb.create_sheet("Alertas de Vencimiento")

    ws3.cell(1, 1, "N° Contrato").fill = header_fill
    ws3.cell(1, 1).font = header_font
    ws3.cell(1, 2, "Comodante").fill = header_fill
    ws3.cell(1, 2).font = header_font
    ws3.cell(1, 3, "Días Restantes").fill = header_fill
    ws3.cell(1, 3).font = header_font

    alertas.sort(key=lambda x: x[2])  # Ordenar por días

    row_num = 2
    for contrato, comodante, dias in alertas:
        ws3.cell(row_num, 1, contrato)
        ws3.cell(row_num, 2, comodante)
        ws3.cell(row_num, 3, dias)
        row_num += 1

    # Guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # Crear respuesta
    response = make_response(output.read())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=Comodatos_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'

    return response


@reportes_bp.route('/comodatos/exportar/pdf')
@login_required
def exportar_comodatos_pdf():
    """
    Exporta el listado de comodatos a formato PDF.
    Incluye alertas de vencimiento destacadas.
    """
    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=30)

    # Obtener datos
    stmt = (
        select(
            DetalleComodato,
            Movimiento.fecha.label('fecha_movimiento'),
            Movimiento.id.label('movimiento_id')
        )
        .join(Movimiento, DetalleComodato.movimiento_id == Movimiento.id)
        .where(Movimiento.tipo_movimiento == 'Comodato')
        .order_by(DetalleComodato.fecha_fin.asc())
    )

    resultados = db.session.execute(stmt).all()

    # La plantilla itera `comodatos_data` con objetos DetalleComodato (usa sus
    # propiedades esta_vencido, dias_para_vencimiento, etc.) y espera además
    # `metricas` y `alertas`. Antes se pasaban `comodatos`/`total`, nombres que
    # la plantilla no conoce, y el PDF fallaba con UndefinedError: 'metricas'.
    comodatos_data = []
    alertas = []
    vigentes = proximos = vencidos = 0
    valor_total = 0.0

    for row in resultados:
        comodato = row.DetalleComodato
        comodatos_data.append(comodato)

        if comodato.valor_comercial_referencial:
            valor_total += comodato.valor_comercial_referencial

        if comodato.fecha_fin < hoy:
            vencidos += 1
            dias = (hoy - comodato.fecha_fin).days
            alertas.append({
                'tipo': 'vencido',
                'numero_contrato': comodato.numero_contrato,
                'comodante': comodato.comodante_nombre,
                'fecha_vencimiento': comodato.fecha_fin.strftime('%d/%m/%Y'),
                'dias_restantes': -dias,
                'mensaje': f'Vencido hace {dias} días'
            })
        elif comodato.fecha_fin <= fecha_alerta:
            proximos += 1
            dias = (comodato.fecha_fin - hoy).days
            alertas.append({
                'tipo': 'proximo',
                'numero_contrato': comodato.numero_contrato,
                'comodante': comodato.comodante_nombre,
                'fecha_vencimiento': comodato.fecha_fin.strftime('%d/%m/%Y'),
                'dias_restantes': dias,
                'mensaje': f'Vence en {dias} días'
            })
        else:
            vigentes += 1

    alertas.sort(key=lambda a: a['dias_restantes'])

    context = {
        'comodatos_data': comodatos_data,
        'alertas': alertas,
        'metricas': {
            'total_comodatos': len(comodatos_data),
            'comodatos_vigentes': vigentes,
            'comodatos_proximos_vencer': proximos,
            'comodatos_vencidos': vencidos,
            'valor_total': valor_total,
        },
        'fecha_generacion': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }

    # Renderizar template PDF
    html = render_template('reportes/comodatos_pdf.html', **context)

    # Generar PDF
    pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Comodatos_{datetime.now().strftime("%Y%m%d")}.pdf'

    return response


@reportes_bp.route('/comodatos/api/alertas')
@login_required
def api_alertas_comodatos():
    """
    API endpoint para obtener alertas de comodatos próximos a vencer.
    Útil para notificaciones en tiempo real.

    Returns:
        JSON con lista de alertas
    """
    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=30)

    stmt = (
        select(DetalleComodato, Movimiento.id.label('movimiento_id'))
        .join(Movimiento, DetalleComodato.movimiento_id == Movimiento.id)
        .where(
            and_(
                Movimiento.tipo_movimiento == 'Comodato',
                DetalleComodato.fecha_fin <= fecha_alerta
            )
        )
        .order_by(DetalleComodato.fecha_fin.asc())
    )

    resultados = db.session.execute(stmt).all()

    alertas = []
    for row in resultados:
        comodato = row.DetalleComodato
        dias = (comodato.fecha_fin - hoy).days

        if dias < 0:
            tipo = 'vencido'
            urgencia = 'alta'
            mensaje = f'VENCIDO hace {abs(dias)} días'
        elif dias <= 7:
            tipo = 'urgente'
            urgencia = 'alta'
            mensaje = f'Vence en {dias} días'
        elif dias <= 30:
            tipo = 'proximo'
            urgencia = 'media'
            mensaje = f'Vence en {dias} días'
        else:
            continue

        alertas.append({
            'id': row.movimiento_id,
            'tipo': tipo,
            'urgencia': urgencia,
            'numero_contrato': comodato.numero_contrato,
            'comodante': comodato.comodante_nombre,
            'fecha_fin': comodato.fecha_fin.strftime('%d/%m/%Y'),
            'dias_restantes': dias,
            'mensaje': mensaje,
            'responsable': comodato.responsable_interno_nombre
        })

    return jsonify({
        'total': len(alertas),
        'alertas': alertas
    })


# ==============================================================================
# REPORTES DE MOVIMIENTOS
# ==============================================================================

@reportes_bp.route('/movimientos/dashboard')
@login_required
def dashboard_movimientos():
    """
    Dashboard de movimientos con métricas y filtros por clase de activo.

    Métricas incluidas:
    - Total de movimientos por tipo
    - Movimientos por clase de activo (TICs, Mobiliario, Electroindustrial)
    - Movimientos por período
    - Estado de aprobaciones
    """
    # Obtener parámetros de filtro
    filtro_clase = request.args.get('clase', '')
    filtro_tipo_movimiento = request.args.get('tipo_movimiento', '')
    filtro_fecha_desde = request.args.get('fecha_desde', '')
    filtro_fecha_hasta = request.args.get('fecha_hasta', '')

    # Construir query base con joins
    stmt = (
        select(
            Movimiento,
            ClaseActivo.nombre_clase.label('clase_nombre')
        )
        .join(Movimiento.activos)  # movimiento_activos
        .join(MovimientoActivo.activo)  # activo
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
        .distinct()
    )

    # Aplicar filtros
    conditions = []

    if filtro_clase:
        conditions.append(ClaseActivo.nombre_clase.ilike(f'%{filtro_clase}%'))

    if filtro_tipo_movimiento:
        conditions.append(Movimiento.tipo_movimiento == filtro_tipo_movimiento)

    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d')
            conditions.append(Movimiento.fecha >= fecha_desde)
        except ValueError:
            pass

    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d')
            from datetime import timedelta
            fecha_hasta = fecha_hasta + timedelta(days=1)
            conditions.append(Movimiento.fecha < fecha_hasta)
        except ValueError:
            pass

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Movimiento.fecha.desc())

    # Ejecutar query
    resultados = db.session.execute(stmt).all()

    # Procesar resultados
    movimientos_data = []
    for row in resultados:
        movimiento, clase_nombre = row
        movimientos_data.append({
            'movimiento': movimiento,
            'clase_nombre': clase_nombre or 'Sin clase'
        })

    # Calcular métricas
    total_movimientos = len(movimientos_data)

    # Movimientos por tipo
    movimientos_por_tipo = {}
    for item in movimientos_data:
        tipo = item['movimiento'].tipo_movimiento
        movimientos_por_tipo[tipo] = movimientos_por_tipo.get(tipo, 0) + 1

    # Movimientos por clase
    movimientos_por_clase = {}
    for item in movimientos_data:
        clase = item['clase_nombre']
        movimientos_por_clase[clase] = movimientos_por_clase.get(clase, 0) + 1

    # Movimientos por estado de aprobación
    movimientos_por_estado = {
        'Pendiente': 0,
        'Aprobado': 0,
        'Rechazado': 0
    }
    for item in movimientos_data:
        estado = item['movimiento'].estado_aprobacion
        if estado in movimientos_por_estado:
            movimientos_por_estado[estado] += 1

    # Obtener lista de clases para filtro
    clases_activo = db.session.execute(
        select(ClaseActivo.nombre_clase)
        .distinct()
        .order_by(ClaseActivo.nombre_clase)
    ).scalars().all()

    # Obtener tipos de movimiento para filtro
    tipos_movimiento = db.session.execute(
        select(Movimiento.tipo_movimiento)
        .distinct()
        .order_by(Movimiento.tipo_movimiento)
    ).scalars().all()

    metricas = {
        'total': total_movimientos,
        'por_tipo': movimientos_por_tipo,
        'por_clase': movimientos_por_clase,
        'por_estado': movimientos_por_estado
    }

    return render_template(
        'reportes/dashboard_movimientos.html',
        movimientos=movimientos_data[:50],  # Mostrar primeros 50
        metricas=metricas,
        clases_activo=clases_activo,
        tipos_movimiento=tipos_movimiento,
        filtros={
            'clase': filtro_clase,
            'tipo_movimiento': filtro_tipo_movimiento,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta
        },
        active_page='reportes'
    )


@reportes_bp.route('/movimientos/exportar/excel')
@login_required
def exportar_movimientos_excel():
    """
    Exporta movimientos a Excel con filtros por clase de activo.
    """
    if not EXCEL_AVAILABLE:
        return "Excel no está disponible. Instale openpyxl: pip install openpyxl", 500

    # Obtener parámetros de filtro
    filtro_clase = request.args.get('clase', '')
    filtro_tipo_movimiento = request.args.get('tipo_movimiento', '')
    filtro_fecha_desde = request.args.get('fecha_desde', '')
    filtro_fecha_hasta = request.args.get('fecha_hasta', '')

    # Construir query
    stmt = (
        select(
            Movimiento,
            ClaseActivo.nombre_clase.label('clase_nombre'),
            Activo.nombre_activo.label('activo_nombre'),
            Activo.placa_codigo_interno.label('activo_placa')
        )
        .join(Movimiento.activos)
        .join(MovimientoActivo.activo)
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
    )

    # Aplicar filtros (mismo código que dashboard)
    conditions = []
    if filtro_clase:
        conditions.append(ClaseActivo.nombre_clase.ilike(f'%{filtro_clase}%'))
    if filtro_tipo_movimiento:
        conditions.append(Movimiento.tipo_movimiento == filtro_tipo_movimiento)
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d')
            conditions.append(Movimiento.fecha >= fecha_desde)
        except ValueError:
            pass
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d')
            from datetime import timedelta
            fecha_hasta = fecha_hasta + timedelta(days=1)
            conditions.append(Movimiento.fecha < fecha_hasta)
        except ValueError:
            pass

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Movimiento.fecha.desc())
    resultados = db.session.execute(stmt).all()

    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"

    # Estilos
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Encabezados
    headers = [
        'ID Movimiento', 'Tipo Movimiento', 'Fecha', 'Placa Activo',
        'Nombre Activo', 'Clase Activo', 'Estado Aprobación', 'Observaciones'
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Datos
    row_num = 2
    for row in resultados:
        movimiento, clase_nombre, activo_nombre, activo_placa = row

        data_row = [
            movimiento.id,
            movimiento.tipo_movimiento,
            movimiento.fecha.strftime('%d/%m/%Y %H:%M') if movimiento.fecha else '',
            activo_placa or '',
            activo_nombre or '',
            clase_nombre or 'Sin clase',
            movimiento.estado_aprobacion,
            movimiento.observaciones_generales or ''
        ]

        for col_num, value in enumerate(data_row, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = border

        row_num += 1

    # Ajustar anchos
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            # str() en ambos lados: antes se medía con str(...) pero se asignaba
            # len(cell.value), que falla en celdas numéricas y dejaba el ancho sin
            # ajustar porque el bare except se tragaba el TypeError.
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    # Guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # Crear respuesta
    response = make_response(output.read())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=Movimientos_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'

    return response


# ==============================================================================
# REPORTES DE MANTENIMIENTOS
# ==============================================================================

@reportes_bp.route('/mantenimientos/dashboard')
@login_required
def dashboard_mantenimientos():
    """
    Dashboard de mantenimientos con métricas y filtros por clase de activo.

    Métricas incluidas:
    - Total de mantenimientos por tipo
    - Mantenimientos por clase de activo (TICs, Mobiliario, Electroindustrial)
    - Mantenimientos por período
    - Estado de mantenimientos
    """
    from ..models import Mantenimiento, MantenimientoTipo

    # Obtener parámetros de filtro
    filtro_clase = request.args.get('clase', '')
    filtro_tipo_mantenimiento = request.args.get('tipo_mantenimiento', '')
    filtro_estado = request.args.get('estado', '')
    filtro_fecha_desde = request.args.get('fecha_desde', '')
    filtro_fecha_hasta = request.args.get('fecha_hasta', '')

    # Construir query base
    stmt = (
        select(
            Mantenimiento,
            MantenimientoTipo.nombre.label('tipo_nombre'),
            ClaseActivo.nombre_clase.label('clase_nombre'),
            Activo.nombre_activo.label('activo_nombre'),
            Activo.placa_codigo_interno.label('activo_placa')
        )
        .join(MantenimientoTipo, Mantenimiento.tipo_id == MantenimientoTipo.id)
        .join(Activo, Mantenimiento.activo_id == Activo.id)
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
    )

    # Aplicar filtros
    conditions = []

    if filtro_clase:
        conditions.append(ClaseActivo.nombre_clase.ilike(f'%{filtro_clase}%'))

    if filtro_tipo_mantenimiento:
        try:
            tipo_id = int(filtro_tipo_mantenimiento)
            conditions.append(Mantenimiento.tipo_id == tipo_id)
        except ValueError:
            pass

    if filtro_estado:
        conditions.append(Mantenimiento.estado == filtro_estado)

    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d')
            conditions.append(Mantenimiento.fecha_mantenimiento >= fecha_desde)
        except ValueError:
            pass

    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d')
            from datetime import timedelta
            fecha_hasta = fecha_hasta + timedelta(days=1)
            conditions.append(Mantenimiento.fecha_mantenimiento < fecha_hasta)
        except ValueError:
            pass

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Mantenimiento.fecha_mantenimiento.desc())

    # Ejecutar query
    resultados = db.session.execute(stmt).all()

    # Procesar resultados
    mantenimientos_data = []
    for row in resultados:
        mantenimiento, tipo_nombre, clase_nombre, activo_nombre, activo_placa = row
        mantenimientos_data.append({
            'mantenimiento': mantenimiento,
            'tipo_nombre': tipo_nombre,
            'clase_nombre': clase_nombre or 'Sin clase',
            'activo_nombre': activo_nombre,
            'activo_placa': activo_placa
        })

    # Calcular métricas
    total_mantenimientos = len(mantenimientos_data)

    # Mantenimientos por tipo
    mantenimientos_por_tipo = {}
    for item in mantenimientos_data:
        tipo = item['tipo_nombre']
        mantenimientos_por_tipo[tipo] = mantenimientos_por_tipo.get(tipo, 0) + 1

    # Mantenimientos por clase
    mantenimientos_por_clase = {}
    for item in mantenimientos_data:
        clase = item['clase_nombre']
        mantenimientos_por_clase[clase] = mantenimientos_por_clase.get(clase, 0) + 1

    # Mantenimientos por estado
    mantenimientos_por_estado = {}
    for item in mantenimientos_data:
        estado = item['mantenimiento'].estado
        mantenimientos_por_estado[estado] = mantenimientos_por_estado.get(estado, 0) + 1

    # Obtener listas para filtros
    clases_activo = db.session.execute(
        select(ClaseActivo.nombre_clase)
        .distinct()
        .order_by(ClaseActivo.nombre_clase)
    ).scalars().all()

    tipos_mantenimiento = db.session.execute(
        select(MantenimientoTipo)
        .order_by(MantenimientoTipo.nombre)
    ).scalars().all()

    estados = ['Pendiente', 'Completado', 'En Proceso', 'Cancelado']

    metricas = {
        'total': total_mantenimientos,
        'por_tipo': mantenimientos_por_tipo,
        'por_clase': mantenimientos_por_clase,
        'por_estado': mantenimientos_por_estado
    }

    return render_template(
        'reportes/dashboard_mantenimientos.html',
        mantenimientos=mantenimientos_data[:50],  # Mostrar primeros 50
        metricas=metricas,
        clases_activo=clases_activo,
        tipos_mantenimiento=tipos_mantenimiento,
        estados=estados,
        filtros={
            'clase': filtro_clase,
            'tipo_mantenimiento': filtro_tipo_mantenimiento,
            'estado': filtro_estado,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta
        },
        active_page='reportes'
    )


@reportes_bp.route('/mantenimientos/exportar/excel')
@login_required
def exportar_mantenimientos_excel():
    """
    Exporta mantenimientos a Excel con filtros por clase de activo.
    """
    from ..models import Mantenimiento, MantenimientoTipo

    if not EXCEL_AVAILABLE:
        return "Excel no está disponible. Instale openpyxl: pip install openpyxl", 500

    # Obtener parámetros de filtro
    filtro_clase = request.args.get('clase', '')
    filtro_tipo_mantenimiento = request.args.get('tipo_mantenimiento', '')
    filtro_estado = request.args.get('estado', '')
    filtro_fecha_desde = request.args.get('fecha_desde', '')
    filtro_fecha_hasta = request.args.get('fecha_hasta', '')

    # Construir query (mismo que dashboard)
    stmt = (
        select(
            Mantenimiento,
            MantenimientoTipo.nombre.label('tipo_nombre'),
            ClaseActivo.nombre_clase.label('clase_nombre'),
            Activo.nombre_activo.label('activo_nombre'),
            Activo.placa_codigo_interno.label('activo_placa')
        )
        .join(MantenimientoTipo, Mantenimiento.tipo_id == MantenimientoTipo.id)
        .join(Activo, Mantenimiento.activo_id == Activo.id)
        .outerjoin(ClaseActivo, Activo.clase_id == ClaseActivo.id)
    )

    # Aplicar filtros
    conditions = []
    if filtro_clase:
        conditions.append(ClaseActivo.nombre_clase.ilike(f'%{filtro_clase}%'))
    if filtro_tipo_mantenimiento:
        try:
            tipo_id = int(filtro_tipo_mantenimiento)
            conditions.append(Mantenimiento.tipo_id == tipo_id)
        except ValueError:
            pass
    if filtro_estado:
        conditions.append(Mantenimiento.estado == filtro_estado)
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d')
            conditions.append(Mantenimiento.fecha_mantenimiento >= fecha_desde)
        except ValueError:
            pass
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d')
            from datetime import timedelta
            fecha_hasta = fecha_hasta + timedelta(days=1)
            conditions.append(Mantenimiento.fecha_mantenimiento < fecha_hasta)
        except ValueError:
            pass

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Mantenimiento.fecha_mantenimiento.desc())
    resultados = db.session.execute(stmt).all()

    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Mantenimientos"

    # Estilos
    header_fill = PatternFill(start_color="28a745", end_color="28a745", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Encabezados
    headers = [
        'ID', 'Tipo Mantenimiento', 'Fecha', 'Placa Activo',
        'Nombre Activo', 'Clase Activo', 'Estado', 'Duración (min)', 'Observaciones'
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Datos
    row_num = 2
    for row in resultados:
        mantenimiento, tipo_nombre, clase_nombre, activo_nombre, activo_placa = row

        data_row = [
            mantenimiento.id,
            tipo_nombre,
            mantenimiento.fecha_mantenimiento.strftime('%d/%m/%Y %H:%M') if mantenimiento.fecha_mantenimiento else '',
            activo_placa or '',
            activo_nombre or '',
            clase_nombre or 'Sin clase',
            mantenimiento.estado,
            mantenimiento.duracion_minutos or '',
            mantenimiento.observaciones or ''
        ]

        for col_num, value in enumerate(data_row, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = border

        row_num += 1

    # Ajustar anchos
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            # str() en ambos lados: antes se medía con str(...) pero se asignaba
            # len(cell.value), que falla en celdas numéricas y dejaba el ancho sin
            # ajustar porque el bare except se tragaba el TypeError.
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    # Guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # Crear respuesta
    response = make_response(output.read())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=Mantenimientos_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'

    return response