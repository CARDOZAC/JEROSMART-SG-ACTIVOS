import os
import json
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app, session, make_response
)
import weasyprint
from sqlalchemy import select, func, or_, and_
from ..extensions import db
from flask_login import login_required, current_user
from ..models import (
    Movimiento,
    Activo,
    MovimientoActivo,
    Accesorio,
    DetalleEntrega,
    DetalleTraslado,
    DetalleEntradaSalida,
    DetallePazSalvo,
    Firma
)

movimientos_bp = Blueprint(
    'movimientos',
    __name__,
    template_folder='templates',
)

@movimientos_bp.route('/')
@login_required
def ver_movimientos():
    """Muestra una lista de todos los movimientos registrados."""
    filtros = {
        'q': request.args.get('q', '').strip(),
        'tipo': request.args.get('tipo', ''),
        'desde': request.args.get('desde', ''),
        'hasta': request.args.get('hasta', '')
    }

    stmt = select(Movimiento)
    conditions = []
    if filtros['q']:
        search_term = f"%{filtros['q']}%"
        # Since Movimiento doesn't have many searchable text fields directly,
        # we might need to join with details or just search observations.
        conditions.append(Movimiento.observaciones_generales.ilike(search_term))
    if filtros['tipo']:
        conditions.append(Movimiento.tipo_movimiento == filtros['tipo'])
    if filtros['desde']:
        conditions.append(Movimiento.fecha >= filtros['desde'])
    if filtros['hasta']:
        conditions.append(Movimiento.fecha <= filtros['hasta'])

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Movimiento.fecha.desc()).limit(50)
    movimientos = db.session.execute(stmt).scalars().all()
    return render_template("ver_movimientos.html", movimientos=movimientos, filtros=filtros)

@movimientos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def add_movimiento():
    """
    Gestiona la creación de un nuevo movimiento a través de un asistente (wizard).
    Esta ruta maneja tanto la visualización del formulario como el procesamiento de los datos.
    """
    if request.method == 'POST':
        try:
            data = request.form
            tipo_movimiento = data.get('tipo_movimiento')
            
            # 1. Crear el objeto principal 'Movimiento'
            nuevo_movimiento = Movimiento(
                tipo_movimiento=tipo_movimiento,
                fecha=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                usuario_id=current_user.id,
                observaciones_generales=data.get('observaciones_acta')
            )
            db.session.add(nuevo_movimiento)
            # Hacemos un flush para obtener el ID del movimiento antes del commit final
            db.session.flush()
            movimiento_id = nuevo_movimiento.id
            
            # 2. Procesar activos y accesorios
            activos_json = data.get('activos_data', '[]')
            accesorios_json = data.get('accesorios_data', '{}')
            activos_data = json.loads(activos_json)
            accesorios_data = json.loads(accesorios_json)
            
            for activo in activos_data:
                activo_id = activo.get('id')
                movimiento_activo = MovimientoActivo(
                    movimiento_id=movimiento_id,
                    activo_id=activo_id
                )
                db.session.add(movimiento_activo)
                db.session.flush() # Para obtener el ID de movimiento_activo
                
                # Insertar accesorios para este activo
                if str(activo_id) in accesorios_data:
                    for accesorio in accesorios_data[str(activo_id)]:
                        nuevo_accesorio = Accesorio(
                            movimiento_activo_id=movimiento_activo.id,
                            descripcion=accesorio.get('descripcion'),
                            cantidad=accesorio.get('cantidad')
                        )
                        db.session.add(nuevo_accesorio)
            
            # 3. Insertar en la tabla de detalles específica
            if tipo_movimiento == 'Entrega':
                detalle = DetalleEntrega(
                    movimiento_id=movimiento_id,
                    proveedor_id=data.get('proveedor_id') if data.get('proveedor_id') and str(data.get('proveedor_id')).isdigit() else None,
                    factura=data.get('entrega_factura'),
                    orden_compra_contrato=data.get('entrega_contrato_nro'),
                    fecha_oc_contrato=data.get('entrega_contrato_fecha'),
                    objeto_contrato=data.get('entrega_objeto_contrato'),
                    tipo_elementos=json.dumps(request.form.getlist('entrega_tipo_elementos')),
                    requiere_montaje='requiere_montaje' in data,
                    requiere_capacitacion='requiere_capacitacion' in data,
                    tipo_asignacion=data.get('entrega_tipo_asignacion'),
                    quien_entrega_nombre=data.get('entrega_nombre'),
                    quien_recibe_nombre=data.get('recibe_nombre'),
                    observaciones_acta=data.get('observaciones_acta')
                )
                db.session.add(detalle)
            elif tipo_movimiento == 'Traslado':
                detalle = DetalleTraslado(
                    movimiento_id=movimiento_id,
                    fecha_traslado=data.get('fecha_traslado'),
                    hora_traslado=data.get('hora_traslado'),
                    tipo_traslado_json=json.dumps(request.form.getlist('traslado_tipo[]')),
                    ubicacion_inicial=data.get('traslado_ubicacion_inicial'),
                    ubicacion_final=data.get('traslado_ubicacion_final'),
                    origen_responsable_nombre=data.get('origen_responsable_nombre'),
                    origen_responsable_cc=data.get('origen_responsable_cc'),
                    origen_responsable_cargo=data.get('origen_responsable_cargo'),
                    nuevo_responsable_nombre=data.get('nuevo_responsable_nombre'),
                    nuevo_responsable_cc=data.get('nuevo_responsable_cc'),
                    nuevo_responsable_cargo=data.get('nuevo_responsable_cargo')
                )
                db.session.add(detalle)
            elif tipo_movimiento == 'Entrada/Salida':
                detalle = DetalleEntradaSalida(
                    movimiento_id=movimiento_id,
                    ciudad=data.get('ciudad_es'),
                    sede=data.get('sede_es'),
                    solicitante_responsable_nombre=data.get('solicitante_responsable_nombre'),
                    solicitante_responsable_cc=data.get('solicitante_responsable_cc'),
                    solicitante_responsable_cargo_area=data.get('solicitante_responsable_cargo_area'),
                    tercero_entidad_persona=data.get('tercero_entidad_persona'),
                    tercero_nit_cc=data.get('tercero_nit_cc'),
                    tercero_direccion=data.get('tercero_direccion'),
                    tercero_movil=data.get('tercero_movil'),
                    tipo_operacion=data.get('tipo_operacion_es'),
                    motivo=data.get('motivo_es'),
                    fecha_retorno_estimada=data.get('fecha_retorno_estimada')
                )
                db.session.add(detalle)
            elif tipo_movimiento == 'Paz y Salvo':
                detalle = DetallePazSalvo(
                    movimiento_id=movimiento_id,
                    funcionario_desvinculado_id=data.get('funcionario_id'),
                    nombre_funcionario=data.get('paz_salvo_nombre_funcionario'),
                    cargo_funcionario=data.get('paz_salvo_cargo_funcionario'),
                    area_funcionario=data.get('paz_salvo_area_funcionario'),
                    observaciones_paz_salvo=data.get('observaciones_paz_salvo')
                )
                db.session.add(detalle)
            
            db.session.commit()
            flash(f'Acta de {tipo_movimiento} #{movimiento_id} creada exitosamente.', 'success')
            return redirect(url_for('movimientos.ver_movimientos'))

        except json.JSONDecodeError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de decodificación JSON al procesar movimiento: {e}")
            flash(f'Error interno con los datos del formulario (JSON). Detalles: {e}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al procesar movimiento: {e}")
            flash(f'Error al guardar el movimiento: {e}', 'danger')

    return render_template('add_movimiento.html', active_page='add_movimiento')

@movimientos_bp.route('/api/buscar_activos')
@login_required
def buscar_activos_api():
    term = request.args.get('term', '')
    if len(term) < 2:
        return jsonify([])

    search_term = f'%{term}%'
    stmt = (
        select(Activo.id, Activo.nombre_activo, Activo.placa_codigo_interno, Activo.serie)
        .where(
            (Activo.nombre_activo.ilike(search_term)) |
            (Activo.placa_codigo_interno.ilike(search_term))
        )
        .limit(10)
    )
    activos = db.session.execute(stmt).mappings().all()
    return jsonify([dict(row) for row in activos])


@movimientos_bp.route('/<int:movimiento_id>/pdf')
@login_required
def generar_acta_pdf(movimiento_id):
    movimiento = db.session.get(Movimiento, movimiento_id)
    if not movimiento:
        return "Movimiento no encontrado", 404

    activos_relacionados = db.session.scalars(
        select(MovimientoActivo).where(MovimientoActivo.movimiento_id == movimiento_id)
    ).all()
    activos = [ar.activo for ar in activos_relacionados]

    accesorios_por_activo = {}
    for ar in activos_relacionados:
        accesorios = db.session.scalars(select(Accesorio).where(Accesorio.movimiento_activo_id == ar.id)).all()
        if accesorios:
            accesorios_por_activo[ar.activo_id] = [{"descripcion": acc.descripcion, "cantidad": acc.cantidad} for acc in accesorios]

    firmas_db = db.session.scalars(select(Firma).where(Firma.documento_id == movimiento_id, Firma.tipo_documento == 'movimiento')).all()
    firmas = {firma.rol_firma: firma.firma_base64 for firma in firmas_db}

    template_name = None
    detalles = None
    tipo = movimiento.tipo_movimiento

    if tipo == 'Traslado':
        template_name = 'pdf_templates/acta_traslado.html'
        detalles = movimiento.detalle_traslado
    elif tipo == 'Entrega':
        template_name = 'pdf_templates/acta_entrega.html'
        detalles = movimiento.detalle_entrega
    elif tipo == 'Entrada/Salida':
        template_name = 'pdf_templates/acta_entrada_salida.html'
        detalles = movimiento.detalle_entrada_salida
    elif tipo == 'Paz y Salvo':
        template_name = 'pdf_templates/acta_paz_y_salvo.html'
        detalles = movimiento.detalle_paz_salvo

    if not template_name:
        return f"No hay una plantilla de PDF definida para el tipo de movimiento: {tipo}", 501

    detalles_dict = detalles.__dict__ if detalles else {}
    if 'tipo_traslado_json' in detalles_dict and detalles_dict['tipo_traslado_json']:
        try:
            detalles_dict['tipo_traslado'] = json.loads(detalles_dict['tipo_traslado_json'])
        except:
            detalles_dict['tipo_traslado'] = []
    if 'tipo_elementos' in detalles_dict and detalles_dict['tipo_elementos']:
        try:
            detalles_dict['tipo_elementos_list'] = json.loads(detalles_dict['tipo_elementos'])
        except:
            detalles_dict['tipo_elementos_list'] = []

    context = {
        "movimiento": movimiento,
        "activos": activos,
        "detalles": detalles_dict,
        "accesorios_por_activo": accesorios_por_activo,
        "firmas": firmas,
    }

    html = render_template(template_name, **context)
    pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="Acta_{tipo}_{movimiento_id}.pdf"'
    return response

@movimientos_bp.route('/<int:movimiento_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_movimiento(movimiento_id):
    movimiento = db.session.get(Movimiento, movimiento_id)
    if not movimiento:
        flash("Movimiento no encontrado.", "danger")
        return redirect(url_for('movimientos.ver_movimientos'))

    if request.method == 'POST':
        try:
            data = request.form
            movimiento.observaciones_generales = data.get('observaciones_generales')

            movimiento.activos.clear()
            db.session.flush()

            activos_data = json.loads(data.get('activos_data', '[]'))
            accesorios_data = json.loads(data.get('accesorios_data', '{}'))

            for activo in activos_data:
                activo_id = activo.get('id')
                movimiento_activo = MovimientoActivo(
                    movimiento_id=movimiento_id,
                    activo_id=activo_id
                )
                db.session.add(movimiento_activo)
                db.session.flush()

                if str(activo_id) in accesorios_data:
                    for acc in accesorios_data[str(activo_id)]:
                        nuevo_acc = Accesorio(
                            movimiento_activo_id=movimiento_activo.id,
                            descripcion=acc.get('descripcion'),
                            cantidad=acc.get('cantidad')
                        )
                        db.session.add(nuevo_acc)

            tipo = movimiento.tipo_movimiento
            if tipo == 'Entrega':
                d = movimiento.detalle_entrega
                d.proveedor_id = data.get('proveedor_id') if data.get('proveedor_id') and str(data.get('proveedor_id')).isdigit() else None
                d.factura = data.get('entrega_factura')
                d.orden_compra_contrato = data.get('entrega_contrato_nro')
                d.fecha_oc_contrato = data.get('entrega_contrato_fecha')
                d.objeto_contrato = data.get('entrega_objeto_contrato')
                d.tipo_elementos = json.dumps(request.form.getlist('entrega_tipo_elementos'))
                d.requiere_montaje = 'requiere_montaje' in data
                d.requiere_capacitacion = 'requiere_capacitacion' in data
                d.tipo_asignacion = data.get('entrega_tipo_asignacion')
                d.quien_entrega_nombre = data.get('entrega_nombre')
                d.quien_recibe_nombre = data.get('recibe_nombre')
                d.observaciones_acta = data.get('observaciones_acta')
            elif tipo == 'Traslado':
                d = movimiento.detalle_traslado
                d.fecha_traslado = data.get('fecha_traslado')
                d.hora_traslado = data.get('hora_traslado')
                d.tipo_traslado_json = json.dumps(request.form.getlist('traslado_tipo[]'))
                d.ubicacion_inicial = data.get('traslado_ubicacion_inicial')
                d.ubicacion_final = data.get('traslado_ubicacion_final')
                d.origen_responsable_nombre = data.get('origen_responsable_nombre')
                d.origen_responsable_cc = data.get('origen_responsable_cc')
                d.origen_responsable_cargo = data.get('origen_responsable_cargo')
                d.nuevo_responsable_nombre = data.get('nuevo_responsable_nombre')
                d.nuevo_responsable_cc = data.get('nuevo_responsable_cc')
                d.nuevo_responsable_cargo = data.get('nuevo_responsable_cargo')
            elif tipo == 'Entrada/Salida':
                d = movimiento.detalle_entrada_salida
                d.ciudad = data.get('ciudad_es')
                d.sede = data.get('sede_es')
                d.solicitante_responsable_nombre = data.get('solicitante_responsable_nombre')
                d.solicitante_responsable_cc = data.get('solicitante_responsable_cc')
                d.solicitante_responsable_cargo_area = data.get('solicitante_responsable_cargo_area')
                d.tercero_entidad_persona = data.get('tercero_entidad_persona')
                d.tercero_nit_cc = data.get('tercero_nit_cc')
                d.tercero_direccion = data.get('tercero_direccion')
                d.tercero_movil = data.get('tercero_movil')
                d.tipo_operacion = data.get('tipo_operacion_es')
                d.motivo = data.get('motivo_es')
                d.fecha_retorno_estimada = data.get('fecha_retorno_estimada')
            elif tipo == 'Paz y Salvo':
                d = movimiento.detalle_paz_salvo
                d.funcionario_desvinculado_id = data.get('funcionario_id')
                d.nombre_funcionario = data.get('paz_salvo_nombre_funcionario')
                d.cargo_funcionario = data.get('paz_salvo_cargo_funcionario')
                d.area_funcionario = data.get('paz_salvo_area_funcionario')
                d.observaciones_paz_salvo = data.get('observaciones_paz_salvo')

            db.session.commit()
            flash(f"Movimiento #{movimiento_id} actualizado con éxito.", "success")
            return redirect(url_for('movimientos.ver_movimientos'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al editar movimiento #{movimiento_id}: {e}")
            flash(f"Error al actualizar el movimiento: {e}", "danger")

    detalles = getattr(movimiento, f"detalle_{movimiento.tipo_movimiento.lower().replace('/', '_').replace(' ', '_')}")
    activos_relacionados = db.session.scalars(select(MovimientoActivo).where(MovimientoActivo.movimiento_id == movimiento_id)).all()
    activos_asociados = [{"id": ar.activo.id, "nombre_activo": ar.activo.nombre_activo, "placa_codigo_interno": ar.activo.placa_codigo_interno, "serie": ar.activo.serie} for ar in activos_relacionados]
    accesorios_asociados = []
    for ar in activos_relacionados:
        accs = db.session.scalars(select(Accesorio).where(Accesorio.movimiento_activo_id == ar.id)).all()
        for acc in accs:
            accesorios_asociados.append({"descripcion": acc.descripcion, "cantidad": acc.cantidad, "activo_id": ar.activo_id})

    return render_template(
        'edit_movimiento.html',
        movimiento=movimiento,
        detalles=detalles,
        activos_asociados=activos_asociados,
        accesorios_asociados=accesorios_asociados
    )

@movimientos_bp.route('/<int:movimiento_id>/eliminar', methods=['POST'])
@login_required
def eliminar_movimiento(movimiento_id):
    movimiento = db.session.get(Movimiento, movimiento_id)
    if not movimiento:
        flash(f"Movimiento #{movimiento_id} no encontrado.", "danger")
        return redirect(url_for('movimientos.ver_movimientos'))

    try:
        db.session.delete(movimiento)
        db.session.commit()
        flash(f"Movimiento #{movimiento_id} eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar movimiento #{movimiento_id}: {e}")
        flash(f"Error al eliminar el movimiento: {e}", "danger")
    
    return redirect(url_for('movimientos.ver_movimientos'))
