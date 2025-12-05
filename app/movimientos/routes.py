import os
import json
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app, session, make_response
)
import weasyprint # noqa
from sqlalchemy import select, func
from ..extensions import db
from flask_login import current_user
from ..decorators import login_required
from ..models import (
    Movimiento,
    Activo,
    User,
    MovimientoActivo,
    Accesorio,
    DetalleEntrega,
    DetalleTraslado,
    DetalleEntradaSalida,
    DetallePazSalvo,
    DetalleReporteDanoPerdida,
    Firma,
    Proveedor
)

# Importar el blueprint desde __init__.py (evitar duplicación)
from . import movimientos_bp

# =====================================================================
# VISTAS PRINCIPALES (Renderizado de plantillas)
# =====================================================================

@movimientos_bp.route('/')
@login_required
def ver_movimientos():
    """Muestra una lista paginada y filtrable de todos los movimientos."""
    filtros = {
        'q': request.args.get('q', '').strip(),
        'tipo': request.args.get('tipo', '')
    }

    # Subconsulta para contar activos por movimiento
    asset_count_subq = (
        select(MovimientoActivo.movimiento_id, func.count(MovimientoActivo.activo_id).label("asset_count"))
        .group_by(MovimientoActivo.movimiento_id)
        .subquery()
    )

    # Consulta principal
    stmt = (
        select(
            Movimiento.id,
            Movimiento.tipo_movimiento,
            Movimiento.fecha,
            Movimiento.observaciones_generales,
            Movimiento.usuario_id,
            Movimiento.funcionario_id,
            User.email.label("usuario_nombre"),
            func.coalesce(asset_count_subq.c.asset_count, 0).label("asset_count")
        )
        .select_from(Movimiento)
        .outerjoin(User, Movimiento.usuario_id == User.id)
        .outerjoin(asset_count_subq, Movimiento.id == asset_count_subq.c.movimiento_id)
    )

    # Aplicar filtros si existen
    if filtros['tipo']:
        stmt = stmt.where(Movimiento.tipo_movimiento == filtros['tipo'])
    if filtros['q']:
        # Sanitizar entrada para prevenir SQL injection / DoS usando función helper
        from .forms import sanitize_search_term
        safe_term, is_valid = sanitize_search_term(filtros['q'], min_length=2, max_length=100)

        if not is_valid:
            flash('La búsqueda debe tener entre 2 y 100 caracteres válidos', 'warning')
            return render_template('ver_movimientos.html', movimientos=[], filtros=filtros)

        # Usar parámetros preparados de SQLAlchemy (previene SQL injection)
        search_term = f"%{safe_term}%"
        stmt = stmt.where(Movimiento.observaciones_generales.ilike(search_term))

    stmt = stmt.order_by(Movimiento.fecha.desc()).limit(50)

    # Procesar resultados para la plantilla
    results = db.session.execute(stmt).all()
    movimientos = [dict(row._mapping) for row in results]

    return render_template('ver_movimientos.html', movimientos=movimientos, filtros=filtros)

@movimientos_bp.route('/<int:movimiento_id>')
@login_required
def ver_movimiento(movimiento_id):
    """
    Muestra la página de detalles para un movimiento específico.
    """
    movimiento = db.session.get(Movimiento, movimiento_id)
    if not movimiento:
        flash(f"El movimiento con ID {movimiento_id} no fue encontrado.", 'warning')
        return redirect(url_for('movimientos.ver_movimientos'))

    # Cargar detalles específicos usando mapeo explícito (más seguro que getattr dinámico)
    DETALLE_ATTR_MAP = {
        'Entrega': 'detalle_entrega',
        'Traslado': 'detalle_traslado',
        'Entrada/Salida': 'detalle_entrada_salida',
        'Paz y Salvo': 'detalle_paz_salvo',
        'Reporte de Daño o Pérdida': 'detalle_reporte_dano_perdida'
    }

    attr_name = DETALLE_ATTR_MAP.get(movimiento.tipo_movimiento)
    detalles = getattr(movimiento, attr_name, None) if attr_name else None

    if not detalles:
        current_app.logger.warning(
            f"No se encontraron detalles para movimiento #{movimiento_id} "
            f"tipo '{movimiento.tipo_movimiento}'"
        )

    # Cargar activos y sus accesorios
    activos_con_accesorios = []
    for ma in movimiento.activos:
        activo_info = {
            'activo': ma.activo,
            'accesorios': ma.accesorios
        }
        activos_con_accesorios.append(activo_info)

    # Cargar firmas
    firmas = {firma.rol_firma: firma.firma_base64 for firma in movimiento.firmas}

    # Cargar usuario que registró el movimiento
    usuario_registra = movimiento.usuario  # Relación ya definida en el modelo

    return render_template(
        'ver_movimiento.html',
        movimiento=movimiento,
        detalles=detalles,
        activos_con_accesorios=activos_con_accesorios,
        firmas=firmas,
        usuario_registra=usuario_registra,  # Agregado
        active_page='ver_movimientos'
    )


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
            tipo_movimiento_form = data.get('tipo_movimiento') # 'Entrada', 'Salida', 'Entrega', etc.

            tipo_movimiento_db = tipo_movimiento_form
            if tipo_movimiento_form in ['Entrada', 'Salida']:
                tipo_movimiento_db = 'Entrada/Salida'

            # 1. Combinar fecha y hora del formulario o usar la actual
            fecha_form = data.get(f'fecha_{tipo_movimiento_form.lower()}')
            hora_form = data.get(f'hora_{tipo_movimiento_form.lower()}')

            fecha_movimiento_dt = datetime.now() # Default
            if fecha_form and hora_form:
                try:
                    fecha_movimiento_dt = datetime.strptime(f'{fecha_form} {hora_form}', '%Y-%m-%d %H:%M')
                except ValueError as e:
                    current_app.logger.error(f"Formato de fecha/hora inválido: {fecha_form} {hora_form}")
                    raise ValueError(f"Formato de fecha/hora inválido '{fecha_form} {hora_form}'. Use el formato YYYY-MM-DD HH:MM.") from e
            elif fecha_form:
                 try:
                    fecha_movimiento_dt = datetime.strptime(fecha_form, '%Y-%m-%d')
                 except ValueError as e:
                    current_app.logger.error(f"Formato de fecha inválido: {fecha_form}")
                    raise ValueError(f"Formato de fecha inválido '{fecha_form}'. Use el formato YYYY-MM-DD.") from e

            # 1. Crear el objeto principal 'Movimiento'
            nuevo_movimiento = Movimiento(
                tipo_movimiento=tipo_movimiento_db,
                fecha=fecha_movimiento_dt,  # ✅ Pasar objeto datetime directamente
                usuario_id=current_user.id,
                observaciones_generales=data.get('observaciones_generales')
            )
            db.session.add(nuevo_movimiento)
            # Hacemos un flush para obtener el ID del movimiento antes del commit final
            db.session.flush()
            movimiento_id = nuevo_movimiento.id
            
            # 2. Procesar activos y accesorios
            activos_json = data.get('activos_data', '[]')
            accesorios_json = data.get('accesorios_data', '{}')
            firmas_json = data.get('firmas_data', '{}') # NUEVO: Capturar firmas

            # DEBUG: Log de firmas recibidas
            current_app.logger.info(f"[CREATE MOVIMIENTO] firmas_json recibido: {firmas_json[:200] if firmas_json else 'VACIO'}")

            # Parsear JSON con manejo de errores robusto
            try:
                activos_data = json.loads(activos_json) if activos_json else []
                if not isinstance(activos_data, list):
                    raise ValueError("activos_data debe ser una lista")
            except (json.JSONDecodeError, ValueError) as e:
                current_app.logger.error(f"Error parseando activos_data: {e}")
                raise ValueError(f"Datos de activos inválidos: {str(e)}")

            try:
                accesorios_data = json.loads(accesorios_json) if accesorios_json else {}
                if not isinstance(accesorios_data, dict):
                    raise ValueError("accesorios_data debe ser un diccionario")
            except (json.JSONDecodeError, ValueError) as e:
                current_app.logger.error(f"Error parseando accesorios_data: {e}")
                raise ValueError(f"Datos de accesorios inválidos: {str(e)}")

            # NIIF/NIC: Calcular valor total para determinar si requiere aprobación
            valor_total_movimiento = 0.0

            for activo in activos_data:
                activo_id = activo.get('id')
                activo_obj = db.session.get(Activo, activo_id)

                if not activo_obj:
                    raise ValueError(f"Activo con ID {activo_id} no encontrado")

                # NIIF/NIC: Snapshot contable al momento del movimiento (NIC 16, párrafo 50)
                valor_comercial = activo_obj.valor_comercial_safe
                valor_libros = activo_obj.valor_en_libros
                depreciacion_acum = activo_obj.depreciacion_acumulada

                valor_total_movimiento += valor_libros

                movimiento_activo = MovimientoActivo(
                    movimiento_id=movimiento_id,
                    activo_id=activo_id,
                    # Snapshot contable (NIIF Compliance)
                    valor_comercial_momento=valor_comercial,
                    valor_libros_momento=valor_libros,
                    depreciacion_acumulada_momento=depreciacion_acum,
                    ubicacion_origen=activo_obj.ubicacion
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

            # NIIF/NIC: Sistema de aprobación según monto (Segregación de funciones)
            # Movimientos > 5 millones COP requieren aprobación de superior
            UMBRAL_APROBACION = 5000000  # 5 millones COP

            if valor_total_movimiento > UMBRAL_APROBACION:
                nuevo_movimiento.requiere_aprobacion = True
                nuevo_movimiento.estado_aprobacion = 'Pendiente'
                flash(f'Movimiento creado. Requiere aprobación (valor total: ${valor_total_movimiento:,.0f} COP)', 'warning')
            else:
                # Auto-aprobado para montos bajos
                nuevo_movimiento.requiere_aprobacion = False
                nuevo_movimiento.estado_aprobacion = 'Aprobado'
                nuevo_movimiento.aprobado_por_id = current_user.id
                nuevo_movimiento.fecha_aprobacion = datetime.now()  # ✅ Pasar objeto datetime directamente

            # 3. Insertar en la tabla de detalles específica
            if tipo_movimiento_form == 'Entrega':
                # Convertir fecha_oc_contrato a objeto date si existe
                fecha_oc_dt = None
                fecha_oc_str = data.get('entrega_contrato_fecha')
                if fecha_oc_str:
                    try:
                        fecha_oc_dt = datetime.strptime(fecha_oc_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        current_app.logger.warning(f"Formato de fecha_oc_contrato inválido: {fecha_oc_str}")

                # --- Lógica robusta para procesar proveedor_id (Estilo 'pETR') ---
                proveedor_id_raw = data.get('proveedor_id')
                proveedor_id_final = None  # Default to NULL

                if proveedor_id_raw and proveedor_id_raw.strip():
                    # 1. Si el valor es numérico, lo usamos directamente.
                    if proveedor_id_raw.isdigit():
                        proveedor_id_final = int(proveedor_id_raw)
                    # 2. Si es el texto 'NO APLICA', buscamos su ID correspondiente.
                    elif proveedor_id_raw.upper() == 'NO APLICA':
                        proveedor_no_aplica = db.session.scalar(
                            select(Proveedor).filter(func.upper(Proveedor.razon_social) == 'NO APLICA')
                        )
                        if proveedor_no_aplica:
                            proveedor_id_final = proveedor_no_aplica.id
                        # Si no se encuentra, se mantiene como None, lo cual es seguro.
                    else:
                        # 3. Log de advertencia si se recibe un valor inesperado no numérico
                        current_app.logger.warning(f"Valor inesperado para proveedor_id: '{proveedor_id_raw}'. Se establecerá a NULL.")

                detalle = DetalleEntrega( # noqa
                    movimiento_id=movimiento_id,
                    proveedor_id=proveedor_id_final,
                    factura=data.get('entrega_factura'),
                    orden_compra_contrato=data.get('entrega_contrato_nro'),
                    fecha_oc_contrato=fecha_oc_dt,  # ✅ Objeto date en lugar de string
                    tipo_contrato=data.get('tipo_contrato'),
                    valor_contrato=float(data.get('valor_contrato')) \
                        if data.get('valor_contrato') and str(data.get('valor_contrato')).replace('.', '', 1).replace('-', '').isdigit() \
                        else None,
                    objeto_contrato=data.get('entrega_objeto_contrato'),
                    tipo_elementos=json.dumps(request.form.getlist('entrega_tipo_elementos')),
                    requiere_montaje='requiere_montaje' in data,
                    requiere_capacitacion='requiere_capacitacion' in data,
                    incluye_accesorios='incluye_accesorios' in data,
                    tipo_transporte=data.get('tipo_transporte'),
                    tipo_asignacion=data.get('tipo_asignacion'),
                    lugar_entrega_actual=data.get('lugar_entrega_actual'),  # ✅ NUEVO: Agregado
                    quien_entrega_nombre=data.get('entrega_responsable_nombre'),
                    quien_entrega_cedula=data.get('entrega_responsable_cc'),
                    quien_entrega_cargo=data.get('entrega_responsable_cargo'),
                    quien_entrega_area=data.get('entrega_responsable_area'),
                    quien_entrega_centro_costo=data.get('quien_entrega_centro_costo'),
                    quien_recibe_nombre=data.get('recibe_responsable_nombre'),
                    quien_recibe_cedula=data.get('recibe_responsable_cc'),
                    quien_recibe_cargo=data.get('recibe_responsable_cargo'),
                    quien_recibe_area=data.get('recibe_responsable_area'),
                    quien_recibe_centro_costo=data.get('recibe_responsable_centro_costo'),
                    garantia_meses=int(data.get('garantia_meses')) if data.get('garantia_meses') and data.get('garantia_meses').isdigit() else None  # ✅ NUEVO: Agregado
                )
                db.session.add(detalle)
            elif tipo_movimiento_form == 'Traslado':
                # Convertir fecha_traslado a objeto datetime si existe
                fecha_traslado_dt = None
                fecha_traslado_str = data.get('fecha_traslado')
                if fecha_traslado_str:
                    try:
                        # Si también hay hora, combinarlas
                        hora_traslado_str = data.get('hora_traslado')
                        if hora_traslado_str:
                            fecha_traslado_dt = datetime.strptime(f'{fecha_traslado_str} {hora_traslado_str}', '%Y-%m-%d %H:%M')
                        else:
                            fecha_traslado_dt = datetime.strptime(fecha_traslado_str, '%Y-%m-%d')
                    except (ValueError, TypeError) as e:
                        current_app.logger.warning(f"Formato de fecha_traslado inválido: {fecha_traslado_str}")

                detalle = DetalleTraslado( # noqa
                    movimiento_id=movimiento_id,
                    fecha_traslado=fecha_traslado_dt,  # ✅ Objeto datetime en lugar de string
                    hora_traslado=data.get('hora_traslado'),
                    caracteristica=data.get('traslado_caracteristica'),
                    lugar_destino=data.get('traslado_lugar_destino'),  # ✅ Corregido nombre de campo
                    tipo_traslado_json=json.dumps(request.form.getlist('traslado_tipo')),  # ✅ Corregido: sin []
                    accesorios_generales_json=data.get('accesorios_generales_json', '[]'),
                    ubicacion_inicial=data.get('traslado_ubicacion_inicial'),
                    ubicacion_final=data.get('traslado_ubicacion_final'),  # ✅ Corregido nombre de campo
                    origen_responsable_nombre=data.get('origen_responsable_nombre'),  # ✅ Corregido
                    origen_responsable_cc=data.get('origen_responsable_cc'),  # ✅ Corregido
                    origen_responsable_cargo=data.get('origen_responsable_cargo'),  # ✅ Corregido
                    origen_area=data.get('origen_responsable_area'),  # ✅ Corregido
                    origen_codigo_costo=data.get('origen_codigo_costo'),  # ✅ Ya está bien
                    origen_centro_costo=data.get('origen_centro_costo'),  # ✅ Ya está bien
                    nuevo_responsable_nombre=data.get('nuevo_responsable_nombre'),  # ✅ Corregido
                    nuevo_responsable_cc=data.get('nuevo_responsable_cc'),  # ✅ Corregido
                    nuevo_responsable_cargo=data.get('nuevo_responsable_cargo'),  # ✅ Corregido
                    destino_area=data.get('nuevo_responsable_area'),  # ✅ Corregido
                    destino_codigo_costo=data.get('nuevo_codigo_costo'),  # ✅ Ya está bien
                    destino_centro_costo=data.get('nuevo_centro_costo'),  # ✅ Ya está bien
                    estado_activo=data.get('estado_activo')  # ✅ NUEVO: Agregado
                )
                db.session.add(detalle)
            elif tipo_movimiento_form in ['Entrada', 'Salida']:
                # FASE 3: VALIDACIONES DE CAMPOS REQUERIDOS
                errores_validacion = []

                # Validar campos obligatorios
                if not data.get('ciudad'):
                    errores_validacion.append('Ciudad es requerida')
                if not data.get('sede'):
                    errores_validacion.append('Sede es requerida')
                if not data.get('tercero_entidad_persona'):
                    errores_validacion.append('Nombre de Entidad/Persona (Tercero) es requerido')
                if not data.get('tercero_nit_cc'):
                    errores_validacion.append('NIT/Cédula del Tercero es requerido')

                # Validar fecha de retorno solo para Salidas
                if tipo_movimiento_form == 'Salida' and not data.get('fecha_retorno_estimada'):
                    errores_validacion.append('Fecha de Retorno Estimada es requerida para Salidas')

                # Validar motivo "Otro"
                if data.get('motivo_seleccionado') == 'Otro' and not data.get('motivo_otro'):
                    errores_validacion.append('Debe especificar el motivo cuando selecciona "Otro"')

                # Si hay errores de validación, abortar y mostrar mensaje
                if errores_validacion:
                    for error in errores_validacion:
                        flash(error, 'danger')
                    current_app.logger.warning(f"Validación fallida en Entrada/Salida: {errores_validacion}")
                    return redirect(url_for('movimientos.add_movimiento'))

                # Convertir fecha_retorno_estimada a objeto date si existe
                fecha_retorno = None
                fecha_retorno_str = data.get('fecha_retorno_estimada')
                if fecha_retorno_str:
                    try:
                        fecha_retorno = datetime.strptime(fecha_retorno_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        current_app.logger.warning(f"Formato de fecha_retorno_estimada inválido: {fecha_retorno_str}")
                        flash('Formato de fecha de retorno inválido', 'danger')
                        return redirect(url_for('movimientos.add_movimiento'))

                # MEJORAS FASE 2.2: Capturar tercero_id y nuevos campos
                tercero_id = data.get('tercero_id')
                # Convertir string vacío a None
                if tercero_id == '' or tercero_id == 'None':
                    tercero_id = None
                elif tercero_id:
                    tercero_id = int(tercero_id)

                detalle = DetalleEntradaSalida( # noqa
                    movimiento_id=movimiento_id,
                    # NUEVOS CAMPOS (Fase 2.2)
                    tercero_id=tercero_id,
                    ciudad=data.get('ciudad'),
                    sede=data.get('sede'),
                    autorizado_por_nombre=data.get('autorizado_por_nombre'),
                    autorizado_por_cargo=data.get('autorizado_por_cargo'),
                    # CAMPOS EXISTENTES
                    solicitante_responsable_nombre=data.get('solicitante_responsable_nombre'),
                    solicitante_responsable_cc=data.get('solicitante_responsable_cc'),
                    solicitante_responsable_cargo_area=data.get('solicitante_responsable_cargo_area'),
                    tercero_entidad_persona=data.get('tercero_entidad_persona'),
                    tercero_nit_cc=data.get('tercero_nit_cc'),
                    tercero_direccion=data.get('tercero_direccion'),
                    tercero_movil=data.get('tercero_movil'),
                    tipo_operacion=data.get('tipo_operacion_es_radio'),  # Cambiado de tipo_operacion_es
                    motivo=data.get('motivo_seleccionado'),  # Cambiado de motivo_es
                    motivo_otro=data.get('motivo_otro'),  # Cambiado de motivo_otro_es
                    fecha_retorno_estimada=fecha_retorno,  # ✅ Objeto date en lugar de string
                    accesorios_generales=data.get('accesorios_generales')  # Cambiado de accesorios_generales_es
                )
                db.session.add(detalle)
            elif tipo_movimiento_form == 'Paz y Salvo':
                # Optimización: Buscar el ID del funcionario por la cédula proporcionada
                cedula_funcionario = data.get('funcionario_id')
                from ..models import Funcionario # Evitar importación circular
                funcionario_obj = db.session.scalar(
                    select(Funcionario).where(Funcionario.cedula == cedula_funcionario)
                )
                if not funcionario_obj:
                    raise ValueError(f"No se encontró un funcionario con la cédula: {cedula_funcionario}")

                detalle = DetallePazSalvo( # noqa
                    movimiento_id=movimiento_id,
                    # Se guarda solo el ID, el resto de datos se obtienen por relación
                    funcionario_desvinculado_id=funcionario_obj.id,
                    observaciones_paz_salvo=data.get('observaciones_paz_salvo')
                )
                db.session.add(detalle)

            elif tipo_movimiento_form == 'Reporte de Daño o Pérdida':
                # Procesar causas del incidente (checkboxes múltiples)
                causas_incidente = data.getlist('causa_incidente')
                causas_str = ', '.join(causas_incidente) if causas_incidente else ''

                # Agregar causa "otro" si existe
                if data.get('causa_incidente_otro'):
                    causas_str += f" (Otro: {data.get('causa_incidente_otro')})"

                detalle = DetalleReporteDanoPerdida( # noqa
                    movimiento_id=movimiento_id,
                    reporte_tipo=data.get('reporte_tipo'),
                    fecha_incidente=datetime.strptime(data.get('fecha_incidente'), '%Y-%m-%d').date() if data.get('fecha_incidente') else None,
                    hora_incidente=data.get('hora_incidente'),
                    area_incidente=data.get('area_incidente'),
                    ubicacion_especifica=data.get('ubicacion_especifica'),
                    descripcion_incidente=data.get('descripcion_incidente'),
                    causas_incidente=causas_str,
                    estado_activo=data.get('estado_activo'),
                    requiere_reparacion=data.get('requiere_reparacion'),
                    costo_estimado=float(data.get('costo_estimado', 0)) if data.get('costo_estimado') else None,
                    garantia_vigente=data.get('garantia_vigente'),
                    responsable_reporte_nombre=data.get('responsable_reporte_nombre'),
                    responsable_reporte_cc=data.get('responsable_reporte_cc'),
                    responsable_reporte_cargo=data.get('responsable_reporte_cargo'),
                    responsable_reporte_area=data.get('responsable_reporte_area'),
                    responsable_reporte_telefono=data.get('responsable_reporte_telefono'),
                    responsable_reporte_email=data.get('responsable_reporte_email'),
                    acciones_tomadas=data.get('acciones_tomadas'),
                    observaciones_adicionales=data.get('observaciones_adicionales')
                )
                db.session.add(detalle)

            # 4. Procesar y guardar firmas (NUEVO)
            try:
                firmas_data = json.loads(firmas_json) if firmas_json else {}
                if not isinstance(firmas_data, dict):
                    raise ValueError("firmas_data debe ser un diccionario")
            except (json.JSONDecodeError, ValueError) as e:
                current_app.logger.error(f"Error parseando firmas_data: {e}")
                # No es crítico, continuar sin firmas
                firmas_data = {}

            if firmas_data:
                current_app.logger.info(f"Procesando {len(firmas_data)} firmas digitales para movimiento #{movimiento_id}")
                for rol, firma_b64 in firmas_data.items():
                    if firma_b64: # Solo guardar si hay firma
                        nueva_firma = Firma(
                            documento_id=movimiento_id,
                            tipo_documento='movimiento',
                            rol_firma=rol,
                            firma_base64=firma_b64
                        )
                        db.session.add(nueva_firma)

            db.session.commit()
            flash(f'Acta de {nuevo_movimiento.tipo_movimiento} #{movimiento_id} creada exitosamente.', 'success')
            return redirect(url_for('movimientos.ver_movimientos'))

        except json.JSONDecodeError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de decodificación JSON al procesar movimiento: {e}")
            flash(f'Error interno con los datos del formulario (JSON). Detalles: {e}', 'danger')
        except Exception as e: # SQLAlchemy envuelve IntegrityError en sus propias excepciones
            db.session.rollback()
            current_app.logger.error(f"Error de integridad de BD al procesar movimiento: {e}")
            flash(f'Error de base de datos. Es posible que un dato ya exista o falte una referencia. Detalles: {e}', 'danger')

    # Para el método GET, simplemente renderizamos la plantilla del asistente.
    # --- Lógica para el método GET ---
    # Asegurar que el proveedor "No Aplica" exista
    proveedor_no_aplica = db.session.scalar(
        select(Proveedor).filter_by(razon_social='No Aplica')
    )
    if not proveedor_no_aplica:
        proveedor_no_aplica = Proveedor(
            razon_social='No Aplica',
            nit='0',
            direccion='N/A',
            persona_contacto='N/A',
            numero_contacto='N/A'
        )
        db.session.add(proveedor_no_aplica)
        db.session.commit()

    # Cargar todos los proveedores, ordenando "No Aplica" primero
    proveedores = db.session.scalars(
        select(Proveedor).order_by(
            db.case(
                (Proveedor.razon_social == 'No Aplica', 0),
                else_=1
            ),
            Proveedor.razon_social
        )
    ).all()
    
    return render_template(
        'add_movimiento.html',
        proveedores=proveedores,
        active_page='add_movimiento'
    )


# =====================================================================
# API ENDPOINTS (Para ser consumidos por el frontend)
# =====================================================================

@movimientos_bp.route('/api/buscar_activos')
@login_required
def buscar_activos_api():
    """
    API para la búsqueda predictiva de activos.
    Utilizado en el asistente de creación de movimientos para añadir activos a un acta.
    """
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

    return jsonify([dict(row) for row in activos]) # Convertir a dict para JSON


@movimientos_bp.route('/api/tercero')
@login_required
def get_tercero_api():
    """
    API para obtener datos de un tercero por ID.
    Utilizado en el formulario de Entrada/Salida para autocompletar datos del tercero.
    """
    from app.models import Tercero

    tercero_id = request.args.get('id', type=int)
    if not tercero_id:
        return jsonify({'error': 'ID de tercero requerido'}), 400

    tercero = db.session.get(Tercero, tercero_id)
    if not tercero:
        return jsonify({'error': 'Tercero no encontrado'}), 404

    return jsonify(tercero.to_dict())


@movimientos_bp.route('/<int:movimiento_id>/pdf')
@login_required
def generar_acta_pdf(movimiento_id):
    """
    Genera el PDF del acta correspondiente a un movimiento.
    Determina qué plantilla usar según el tipo de movimiento.

    Estilo James Gosling: Robusto, con validación exhaustiva y logging detallado.
    """
    try:
        # ========================================================================
        # PASO 1: Validación de entrada y obtención del movimiento
        # ========================================================================
        current_app.logger.info(f"[PDF Generation] Iniciando generación de PDF para movimiento_id={movimiento_id}")

        movimiento = db.session.get(Movimiento, movimiento_id)
        if not movimiento:
            current_app.logger.error(f"[PDF Generation] Movimiento {movimiento_id} no encontrado")
            return "Movimiento no encontrado", 404

        tipo = movimiento.tipo_movimiento
        current_app.logger.info(f"[PDF Generation] Tipo de movimiento: {tipo}")

        # ========================================================================
        # PASO 2: Obtener activos del movimiento
        # ========================================================================
        activos_relacionados = db.session.scalars(
            select(MovimientoActivo).where(MovimientoActivo.movimiento_id == movimiento_id)
        ).all()
        current_app.logger.info(f"[PDF Generation] Activos encontrados: {len(activos_relacionados)}")

        # ========================================================================
        # PASO 3: Obtener accesorios para cada activo (del movimiento Y permanentes)
        # ========================================================================
        accesorios_lista = []  # Lista plana de todos los accesorios para el PDF

        for activo_rel in activos_relacionados:
            # Accesorios del movimiento (tabla Accesorio)
            accesorios_movimiento = db.session.scalars(
                select(Accesorio).where(Accesorio.movimiento_activo_id == activo_rel.id)
            ).all()

            for acc in accesorios_movimiento:
                accesorios_lista.append({
                    "descripcion": acc.descripcion,
                    "cantidad": acc.cantidad
                })

            # Accesorios permanentes del activo (tabla ActivoAccesorio)
            if activo_rel.activo and activo_rel.activo.accesorios_activo:
                for acc_permanente in activo_rel.activo.accesorios_activo:
                    descripcion_completa = acc_permanente.descripcion
                    # Agregar marca, modelo y serie si existen
                    detalles = []
                    if acc_permanente.marca:
                        detalles.append(f"Marca: {acc_permanente.marca}")
                    if acc_permanente.modelo:
                        detalles.append(f"Modelo: {acc_permanente.modelo}")
                    if acc_permanente.serie:
                        detalles.append(f"Serie: {acc_permanente.serie}")

                    if detalles:
                        descripcion_completa += f" ({', '.join(detalles)})"

                    accesorios_lista.append({
                        "descripcion": descripcion_completa,
                        "cantidad": 1  # Los accesorios permanentes son únicos
                    })

        current_app.logger.info(f"[PDF Generation] Accesorios procesados: {len(accesorios_lista)} accesorios en total")

        # ========================================================================
        # PASO 4: Obtener firmas (ACTUALIZADO para incluir SVG y metadata)
        # ========================================================================
        # Hacemos la consulta explícita para evitar ambigüedades en las relaciones
        firmas_query = db.session.scalars(
            select(Firma).where(
                Firma.documento_id == movimiento_id,
                Firma.tipo_documento == 'movimiento'
            )
        ).all()

        # ✅ NUEVO: Pasar objetos Firma completos para acceder a SVG y metadata
        # Diccionario con objetos Firma completos (para templates que soporten SVG)
        firmas_objetos = {firma.rol_firma: firma for firma in firmas_query}

        # Mantener compatibilidad: diccionario con solo base64 (para templates legacy)
        firmas = {firma.rol_firma: firma.firma_base64 for firma in firmas_query}

        current_app.logger.info(
            f"[PDF Generation] Firmas encontradas: {len(firmas)} "
            f"(SVG disponibles: {sum(1 for f in firmas_query if f.firma_svg)})"
        )

        # ========================================================================
        # PASO 4.5: Formatear fecha y hora para el PDF (CORRECCIÓN)
        # ========================================================================
        fecha_formateada = {
            'date': '',
            'time': ''
        }
        try:
            # movimiento.fecha YA es un objeto datetime, no string
            if isinstance(movimiento.fecha, datetime):
                dt_obj = movimiento.fecha
            elif isinstance(movimiento.fecha, str):
                dt_obj = datetime.strptime(movimiento.fecha, '%Y-%m-%d %H:%M:%S')
            else:
                dt_obj = datetime.now()

            fecha_formateada['date'] = dt_obj.strftime('%d/%m/%Y')
            fecha_formateada['time'] = dt_obj.strftime('%I:%M %p')
        except (ValueError, TypeError) as e:
            current_app.logger.warning(f"[PDF Generation] No se pudo parsear la fecha '{movimiento.fecha}' para el PDF. Error: {e}")

        # ========================================================================
        # PASO 5: Determinar plantilla y detalles específicos por tipo
        # ========================================================================
        template_name = None
        detalles = None
        proveedor = None
        funcionario = None

        if tipo == 'Traslado':
            template_name = 'pdf_templates/acta_traslado.html'
            detalles = movimiento.detalle_traslado
        elif tipo == 'Entrega':
            template_name = 'pdf_templates/acta_entrega.html'
            detalles = movimiento.detalle_entrega
            # Obtener proveedor relacionado (si existe)
            if detalles and detalles.proveedor_id:
                proveedor = detalles.proveedor
                current_app.logger.info(f"[PDF Generation] Proveedor: {proveedor.razon_social if proveedor else 'None'}")
        elif tipo == 'Entrada/Salida':
            template_name = 'pdf_templates/acta_entrada_salida.html'
            detalles = movimiento.detalle_entrada_salida
        elif tipo == 'Paz y Salvo':
            template_name = 'pdf_templates/acta_paz_y_salvo.html'
            detalles = movimiento.detalle_paz_salvo

        if not template_name:
            current_app.logger.error(f"[PDF Generation] No hay plantilla para tipo: {tipo}")
            return f"No hay una plantilla de PDF definida para el tipo de movimiento: {tipo}", 501

        # Obtener funcionario del movimiento (si existe)
        if movimiento.funcionario_id:
            funcionario = movimiento.funcionario
            current_app.logger.info(f"[PDF Generation] Funcionario: {funcionario.nombres if funcionario else 'None'}")

        # ========================================================================
        # PASO 6: Procesar detalles y datos JSON
        # ========================================================================
        context = {} # Iniciar un contexto limpio
        if not detalles:
            current_app.logger.warning(f"[PDF Generation] No hay detalles específicos para movimiento {movimiento_id}")

        if detalles:
            # Para Traslado: procesar tipo_traslado_json
            if tipo == 'Traslado':
                try:
                    # Usamos getattr para evitar errores si el campo no existe en un modelo antiguo
                    detalles.tipo_traslado_parsed = json.loads(getattr(detalles, 'tipo_traslado_json', '[]') or '[]')
                    # Nuevo: Parsear accesorios generales para el PDF de traslado
                    context['accesorios'] = json.loads(getattr(detalles, 'accesorios_generales_json', '[]') or '[]')
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"[PDF Generation] Error parseando tipo_traslado_json: {e}")
                    detalles.tipo_traslado_parsed = []
                    context['accesorios'] = []

            # Para Entrega: procesar tipo_elementos
            if hasattr(detalles, 'tipo_elementos') and detalles.tipo_elementos:
                try:
                    detalles.tipo_elementos_parsed = json.loads(detalles.tipo_elementos)
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"[PDF Generation] Error parseando tipo_elementos: {e}")
                    detalles.tipo_elementos_parsed = {}

        # ========================================================================
        # PASO 7: Preparar contexto para la plantilla
        # ========================================================================
        # Contexto base: proporciona todas las variables que las plantillas esperan
        context = {
            "movimiento": movimiento,
            "activos": activos_relacionados,  # Lista de MovimientoActivo (no solo Activo)
            "activos_list": [ar.activo for ar in activos_relacionados],  # Lista de Activo puros
            "detalles": detalles,
            "firmas": firmas,  # Diccionario legacy (base64 solo)
            "firmas_objetos": firmas_objetos,  # ✅ NUEVO: Objetos Firma completos con SVG y metadata
            "proveedor": proveedor,  # Variable específica para templates de Entrega
            "funcionario": funcionario,  # Funcionario del movimiento
            "fecha_formateada": fecha_formateada, # CORRECCIÓN: Variable que faltaba
            # Valores por defecto para evitar errores en la plantilla si no se sobreescriben
            "observaciones": movimiento.observaciones_generales or '',
            "accesorios": accesorios_lista  # Lista de accesorios para el PDF (movimiento + permanentes)
        }

        # Agregar variables específicas por tipo (compatibilidad con templates)
        if tipo == 'Entrega':
            # La plantilla de entrega espera un objeto 'detalle_entrega'.
            # Se pasa directamente, incluso si es None, para que la plantilla
            # pueda manejarlo. Las demás variables se acceden desde este objeto.
            context["detalle_entrega"] = detalles

        elif tipo == 'Traslado':
            # Mapeo explícito para que la plantilla de traslado funcione
            context["numero_traslado"] = movimiento.id
            if detalles:
                context["fecha_traslado"] = detalles.fecha_traslado
                context["hora_traslado"] = detalles.hora_traslado
                context["caracteristica"] = detalles.caracteristica
                context["lugar_destino"] = detalles.lugar_destino
                context["tipo_traslado"] = json.loads(detalles.tipo_traslado_json or '[]')
                context["accesorios"] = json.loads(detalles.accesorios_generales_json or '[]')
                context["responsable_actual"] = detalles.origen_responsable_nombre
                context["cedula_origen"] = detalles.origen_responsable_cc
                context["cargo_origen"] = detalles.origen_responsable_cargo
                context["area_origen"] = detalles.origen_area
                context["codigo_costo_origen"] = detalles.origen_codigo_costo
                context["centro_costo_origen"] = detalles.origen_centro_costo
                context["ubicacion_inicial"] = detalles.ubicacion_inicial
                context["nuevo_responsable"] = detalles.nuevo_responsable_nombre
                context["cedula_destino"] = detalles.nuevo_responsable_cc
                context["cargo_destino"] = detalles.nuevo_responsable_cargo
                context["area_destino"] = detalles.destino_area
                context["codigo_costo_destino"] = detalles.destino_codigo_costo
                context["centro_costo_destino"] = detalles.destino_centro_costo
                context["ubicacion_final"] = detalles.ubicacion_final
            else:
                # Provide default empty values if no details exist
                context.update({
                    "fecha_traslado": "", "hora_traslado": "", "caracteristica": "",
                    "lugar_destino": "", "tipo_traslado": [],
                    "responsable_actual": "", "cedula_origen": "", "cargo_origen": "",
                    "area_origen": "", "codigo_costo_origen": "", "centro_costo_origen": "",
                    "ubicacion_inicial": "", "nuevo_responsable": "", "cedula_destino": "",
                    "cargo_destino": "", "area_destino": "", "codigo_costo_destino": "",
                    "centro_costo_destino": "", "ubicacion_final": ""
                })

        elif tipo == 'Entrada/Salida':
            # Aseguramos que los nuevos campos estén disponibles en el PDF
            context["detalle_entrada_salida"] = detalles # Se puede mantener por compatibilidad
            if detalles:
                context["motivo_otro"] = detalles.motivo_otro
                context["accesorios_generales"] = detalles.accesorios_generales
        
        elif tipo == 'Paz y Salvo':
            # Optimización: Cargar dinámicamente los datos del funcionario y sus activos
            context["detalle_paz_salvo"] = detalles
            if detalles and detalles.funcionario_desvinculado:
                funcionario_desv = detalles.funcionario_desvinculado
                context["nombre_funcionario"] = f"{funcionario_desv.nombres} {funcionario_desv.apellidos}"
                context["cargo_funcionario"] = funcionario_desv.cargo
                context["area_funcionario"] = funcionario_desv.area
                context["cedula_funcionario"] = funcionario_desv.cedula

                # Consulta para obtener los activos que el funcionario tenía a su cargo
                activos_a_cargo = db.session.scalars(
                    select(Activo).where(Activo.funcionario_id == funcionario_desv.id)
                ).all()
                context["activos_a_cargo"] = activos_a_cargo

        elif tipo == 'Reporte de Daño o Pérdida':
            template_name = 'pdf_templates/acta_reporte_dano_perdida.html'
            detalles = movimiento.detalle_reporte_dano_perdida

            # Agregar variables comunes del header (sin logo_path ya que usa url_for en el template)
            context["fecha_actual"] = datetime.now().strftime('%d/%m/%Y')
            context["consecutivo_movimiento"] = f"DP-{movimiento.id:05d}"

            if detalles:
                # Extraer todos los campos del detalle para pasarlos al template
                context["reporte_tipo"] = detalles.reporte_tipo
                context["fecha_incidente"] = detalles.fecha_incidente.strftime('%d/%m/%Y') if detalles.fecha_incidente else ''
                context["hora_incidente"] = detalles.hora_incidente
                context["area_incidente"] = detalles.area_incidente
                context["ubicacion_especifica"] = detalles.ubicacion_especifica
                context["descripcion_incidente"] = detalles.descripcion_incidente
                context["causas_incidente"] = detalles.causas_incidente or ''
                context["estado_activo"] = detalles.estado_activo
                context["requiere_reparacion"] = detalles.requiere_reparacion
                context["costo_estimado"] = float(detalles.costo_estimado) if detalles.costo_estimado else None
                context["garantia_vigente"] = detalles.garantia_vigente
                context["responsable_reporte_nombre"] = detalles.responsable_reporte_nombre
                context["responsable_reporte_cc"] = detalles.responsable_reporte_cc
                context["responsable_reporte_cargo"] = detalles.responsable_reporte_cargo
                context["responsable_reporte_area"] = detalles.responsable_reporte_area
                context["responsable_reporte_telefono"] = detalles.responsable_reporte_telefono
                context["responsable_reporte_email"] = detalles.responsable_reporte_email
                context["acciones_tomadas"] = detalles.acciones_tomadas
                context["observaciones_adicionales"] = detalles.observaciones_adicionales

                # Extraer causa_incidente_otro si está en la cadena
                if '(Otro:' in context["causas_incidente"]:
                    import re
                    match = re.search(r'\(Otro: (.+?)\)', context["causas_incidente"])
                    context["causa_incidente_otro"] = match.group(1) if match else ''
                else:
                    context["causa_incidente_otro"] = ''

                # Agregar datos del activo (primer activo del movimiento)
                if activos_relacionados:
                    primer_activo = activos_relacionados[0].activo
                    context["placa_codigo_interno"] = primer_activo.placa_codigo_interno if primer_activo else ''
                    context["nombre_activo"] = primer_activo.nombre_activo if primer_activo else ''
                    context["marca"] = primer_activo.marca if primer_activo else ''
                    context["modelo"] = primer_activo.modelo if primer_activo else ''
                    context["numero_serie"] = primer_activo.serie if primer_activo else ''


        current_app.logger.info(f"[PDF Generation] Contexto preparado con {len(context)} variables")

        # ========================================================================
        # PASO 8: Renderizar template y generar PDF
        # ========================================================================
        current_app.logger.info(f"[PDF Generation] Renderizando template: {template_name}")
        html = render_template(template_name, **context)

        current_app.logger.info(f"[PDF Generation] Generando PDF con WeasyPrint")
        pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()

        current_app.logger.info(f"[PDF Generation] PDF generado exitosamente ({len(pdf_bytes)} bytes)")

        # ========================================================================
        # PASO 9: Preparar respuesta HTTP
        # ========================================================================
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="Acta_{tipo}_{movimiento_id}.pdf"'

        return response

    except Exception as e:
        # Manejo robusto de errores (estilo James Gosling)
        current_app.logger.error(f"[PDF Generation] Error crítico generando PDF: {str(e)}", exc_info=True)
        return f"Error al generar el PDF: {str(e)}", 500


@movimientos_bp.route('/plantillas-pdf')
@login_required
def ver_plantillas_pdf():
    """
    Página de índice con enlaces para descargar todas las plantillas PDF en blanco.
    """
    return render_template('plantillas_pdf_index.html')


@movimientos_bp.route('/plantillas-pdf/<tipo>')
@login_required
def generar_plantilla_pdf_ejemplo(tipo):
    """
    Genera PDFs de ejemplo/plantilla sin datos reales para cada tipo de acta.
    Útil para revisión y aprobación de formatos.

    Tipos disponibles: 'entrega', 'traslado', 'entrada-salida', 'paz-y-salvo', 'comodato', 'reporte-dano-perdida'
    """
    try:
        # Mapear tipo de URL a tipo de movimiento y template
        tipo_map = {
            'entrega': {
                'tipo_movimiento': 'Entrega',
                'template': 'pdf_templates/acta_entrega.html'
            },
            'traslado': {
                'tipo_movimiento': 'Traslado',
                'template': 'pdf_templates/acta_traslado.html'
            },
            'entrada-salida': {
                'tipo_movimiento': 'Entrada/Salida',
                'template': 'pdf_templates/acta_entrada_salida.html'
            },
            'paz-y-salvo': {
                'tipo_movimiento': 'Paz y Salvo',
                'template': 'pdf_templates/acta_paz_y_salvo.html'
            },
            'comodato': {
                'tipo_movimiento': 'Comodato',
                'template': 'pdf_templates/acta_comodato.html'
            },
            'reporte-dano-perdida': {
                'tipo_movimiento': 'Reporte de Daño o Pérdida',
                'template': 'pdf_templates/acta_reporte_dano_perdida.html'
            }
        }

        if tipo not in tipo_map:
            return "Tipo de plantilla no válido. Use: entrega, traslado, entrada-salida, paz-y-salvo, comodato, reporte-dano-perdida", 400

        config = tipo_map[tipo]
        template_name = config['template']
        tipo_movimiento = config['tipo_movimiento']

        current_app.logger.info(f"[PLANTILLA PDF] Generando plantilla de ejemplo para tipo: {tipo_movimiento}")

        # ========================================================================
        # Datos de ejemplo/mock para cada tipo de acta
        # ========================================================================

        # Crear objeto mock de Movimiento
        class MockMovimiento:
            def __init__(self):
                self.id = 0
                self.tipo_movimiento = tipo_movimiento
                self.fecha = datetime.now()
                self.observaciones_generales = ''

        movimiento_mock = MockMovimiento()

        # Crear objeto mock de Activo
        class MockActivo:
            def __init__(self, num):
                self.id = num
                self.nombre_activo = ''
                self.placa_codigo_interno = ''
                self.marca = ''
                self.modelo = ''
                self.serie = ''
                self.estado = 'Operativo'
                self.accesorios_activo = []

        # Crear objeto mock de MovimientoActivo
        class MockMovimientoActivo:
            def __init__(self, num):
                self.id = num
                self.activo = MockActivo(num)
                self.valor_comercial_momento = 0
                self.valor_libros_momento = 0

        # Lista de activos de ejemplo (vacíos)
        activos_mock = [MockMovimientoActivo(i) for i in range(1, 4)]

        # Contexto base común para todas las plantillas
        context = {
            "movimiento": movimiento_mock,
            "activos": activos_mock,
            "activos_list": [ma.activo for ma in activos_mock],
            "firmas": {},
            "firmas_objetos": {},  # Diccionario vacío para plantillas de ejemplo
            "observaciones": '',
            "accesorios": [],
            "fecha_formateada": {
                'date': datetime.now().strftime('%d/%m/%Y'),
                'time': datetime.now().strftime('%I:%M %p')
            }
        }

        # ========================================================================
        # Detalles específicos por tipo de acta
        # ========================================================================

        if tipo == 'entrega':
            class MockDetalleEntrega:
                def __init__(self):
                    self.proveedor = None
                    self.factura = ''
                    self.orden_compra_contrato = ''
                    self.fecha_oc_contrato = None
                    self.tipo_contrato = ''
                    self.valor_contrato = None
                    self.objeto_contrato = ''
                    self.tipo_elementos = '[]'
                    self.requiere_montaje = False
                    self.requiere_capacitacion = False
                    self.incluye_accesorios = False
                    self.tipo_transporte = ''
                    self.tipo_asignacion = ''
                    self.quien_entrega_nombre = ''
                    self.quien_entrega_cedula = ''
                    self.quien_entrega_cargo = ''
                    self.quien_entrega_area = ''
                    self.quien_entrega_centro_costo = ''
                    self.quien_recibe_nombre = ''
                    self.quien_recibe_cedula = ''
                    self.quien_recibe_cargo = ''
                    self.quien_recibe_area = ''
                    self.quien_recibe_centro_costo = ''

            context["detalles"] = MockDetalleEntrega()
            context["detalle_entrega"] = context["detalles"]
            context["proveedor"] = None

        elif tipo == 'traslado':
            class MockDetalleTraslado:
                def __init__(self):
                    self.fecha_traslado = None
                    self.hora_traslado = ''
                    self.caracteristica = ''
                    self.lugar_destino = ''
                    self.ubicacion_inicial = ''
                    self.ubicacion_final = ''
                    self.origen_responsable_nombre = ''
                    self.origen_responsable_cc = ''
                    self.origen_responsable_cargo = ''
                    self.origen_area = ''
                    self.origen_codigo_costo = ''
                    self.origen_centro_costo = ''
                    self.nuevo_responsable_nombre = ''
                    self.nuevo_responsable_cc = ''
                    self.nuevo_responsable_cargo = ''
                    self.destino_area = ''
                    self.destino_codigo_costo = ''
                    self.destino_centro_costo = ''
                    self.estado_activo = ''

            context["detalles"] = MockDetalleTraslado()
            context["numero_traslado"] = 0
            context["fecha_traslado"] = None
            context["hora_traslado"] = ''
            context["caracteristica"] = ''
            context["lugar_destino"] = ''
            context["tipo_traslado"] = []
            context["responsable_actual"] = ''
            context["cedula_origen"] = ''
            context["cargo_origen"] = ''
            context["area_origen"] = ''
            context["codigo_costo_origen"] = ''
            context["centro_costo_origen"] = ''
            context["ubicacion_inicial"] = ''
            context["nuevo_responsable"] = ''
            context["cedula_destino"] = ''
            context["cargo_destino"] = ''
            context["area_destino"] = ''
            context["codigo_costo_destino"] = ''
            context["centro_costo_destino"] = ''
            context["ubicacion_final"] = ''

        elif tipo == 'entrada-salida':
            class MockDetalleEntradaSalida:
                def __init__(self):
                    self.ciudad = ''
                    self.sede = ''
                    self.solicitante_responsable_nombre = ''
                    self.solicitante_responsable_cc = ''
                    self.solicitante_responsable_cargo_area = ''
                    self.tercero_entidad_persona = ''
                    self.tercero_nit_cc = ''
                    self.tercero_direccion = ''
                    self.tercero_movil = ''
                    self.tipo_operacion = ''
                    self.motivo = ''
                    self.motivo_otro = ''
                    self.fecha_retorno_estimada = None
                    self.accesorios_generales = ''
                    self.autorizado_por_nombre = ''
                    self.autorizado_por_cargo = ''

            context["detalles"] = MockDetalleEntradaSalida()
            context["detalle_entrada_salida"] = context["detalles"]
            context["motivo_otro"] = ''
            context["accesorios_generales"] = ''

        elif tipo == 'paz-y-salvo':
            class MockFuncionario:
                def __init__(self):
                    self.nombres = ''
                    self.apellidos = ''
                    self.cedula = ''
                    self.cargo = ''
                    self.area = ''

            class MockDetallePazSalvo:
                def __init__(self):
                    self.observaciones_paz_salvo = ''
                    self.funcionario_desvinculado = MockFuncionario()

            context["detalles"] = MockDetallePazSalvo()
            context["detalle_paz_salvo"] = context["detalles"]
            context["nombre_funcionario"] = ''
            context["cargo_funcionario"] = ''
            context["area_funcionario"] = ''
            context["cedula_funcionario"] = ''
            context["activos_a_cargo"] = []

        elif tipo == 'reporte-dano-perdida':
            # Agregar variables comunes del header (sin logo_path ya que usa url_for en el template)
            context["fecha_actual"] = datetime.now().strftime('%d/%m/%Y')
            context["consecutivo_movimiento"] = "DP-00000"

            # Variables del reporte (todas vacías para plantilla)
            context["reporte_tipo"] = ''
            context["fecha_incidente"] = ''
            context["hora_incidente"] = ''
            context["area_incidente"] = ''
            context["ubicacion_especifica"] = ''
            context["descripcion_incidente"] = ''
            context["causas_incidente"] = ''
            context["causa_incidente_otro"] = ''
            context["estado_activo"] = ''
            context["requiere_reparacion"] = ''
            context["costo_estimado"] = None
            context["garantia_vigente"] = ''
            context["responsable_reporte_nombre"] = ''
            context["responsable_reporte_cc"] = ''
            context["responsable_reporte_cargo"] = ''
            context["responsable_reporte_area"] = ''
            context["responsable_reporte_telefono"] = ''
            context["responsable_reporte_email"] = ''
            context["acciones_tomadas"] = ''
            context["observaciones_adicionales"] = ''

            # Variables del activo (vacías)
            context["placa_codigo_interno"] = ''
            context["nombre_activo"] = ''
            context["marca"] = ''
            context["modelo"] = ''
            context["numero_serie"] = ''

        # ========================================================================
        # Renderizar y generar PDF
        # ========================================================================
        current_app.logger.info(f"[PLANTILLA PDF] Renderizando template: {template_name}")
        html = render_template(template_name, **context)

        current_app.logger.info(f"[PLANTILLA PDF] Generando PDF con WeasyPrint")
        pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()

        current_app.logger.info(f"[PLANTILLA PDF] PDF generado exitosamente ({len(pdf_bytes)} bytes)")

        # ========================================================================
        # Preparar respuesta HTTP
        # ========================================================================
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Plantilla_Acta_{tipo_movimiento.replace("/", "_")}.pdf"'

        return response

    except Exception as e:
        current_app.logger.error(f"[PLANTILLA PDF] Error generando plantilla: {str(e)}", exc_info=True)
        return f"Error al generar la plantilla PDF: {str(e)}", 500


@movimientos_bp.route('/eliminar/<int:movimiento_id>', methods=['POST'])
@login_required
def eliminar_movimiento(movimiento_id):
    """Elimina un movimiento y sus datos asociados."""
    movimiento = db.session.get(Movimiento, movimiento_id)
    if not movimiento:
        flash(f"Movimiento #{movimiento_id} no encontrado.", "danger")
        return redirect(url_for('movimientos.ver_movimientos'))

    try:
        # Gracias a cascade="all, delete-orphan", SQLAlchemy se encarga de todo.
        db.session.delete(movimiento)
        db.session.commit()
        flash(f"Movimiento #{movimiento_id} eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar movimiento #{movimiento_id}: {e}")
        flash(f"Error al eliminar el movimiento: {e}", "danger")
    
    return redirect(url_for('movimientos.ver_movimientos'))

# =====================================================================
# ASISTENTE DE FIRMAS
# =====================================================================

@movimientos_bp.route('/firmar/<int:movimiento_id>', methods=['GET', 'POST'])
@login_required
def firmar_movimiento(movimiento_id):
    """
    Gestiona el asistente de recolección de firmas para un movimiento.
    GET: Muestra el asistente de firmas.
    POST: Guarda una nueva firma en formato Base64.
    """
    movimiento = db.session.get(Movimiento, movimiento_id)
    if not movimiento:
        flash(f"Movimiento con ID {movimiento_id} no encontrado.", 'danger')
        return redirect(url_for('movimientos.ver_movimientos'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            rol_firma = data.get('rol_firma')
            nombre_firmante = data.get('nombre_firmante', '').strip()  # ✅ NUEVO
            signature_b64 = data.get('signature')  # SVG data URL
            signature_svg = data.get('signature_svg')  # SVG raw XML
            metadata = data.get('metadata', {})
            consentimiento = data.get('consentimiento_aceptado', False)

            # ✅ Validación de datos requeridos
            if not rol_firma or not signature_b64:
                current_app.logger.warning(f"⚠️ Intento de firma sin datos completos: mov={movimiento_id}")
                return jsonify({'success': False, 'message': 'Faltan datos requeridos (rol o firma).'}), 400

            if not signature_svg:
                current_app.logger.warning(f"⚠️ Firma sin SVG vectorial: mov={movimiento_id}, rol={rol_firma}")
                # No es crítico, pero se registra

            # ✅ Extraer IP real del request de forma segura
            # NOTA: trust_proxy=True solo si la aplicación está detrás de nginx/Apache/AWS ELB
            # Si no está seguro, usar trust_proxy=False para evitar IP spoofing
            from .forms import get_client_ip
            ip_address = get_client_ip(request)

            # ✅ Extraer User Agent
            user_agent = request.headers.get('User-Agent', '')[:500]

            # ✅ Calcular hash SHA256 del documento para auditoría
            import hashlib
            # Incluir datos relevantes del movimiento en el hash
            hash_data = f"{movimiento_id}|{movimiento.tipo_movimiento}|{movimiento.fecha}|{rol_firma}|{datetime.utcnow().isoformat()}"
            doc_hash = hashlib.sha256(hash_data.encode('utf-8')).hexdigest()

            # ✅ Validar consentimiento
            if not consentimiento:
                current_app.logger.warning(
                    f"⚠️ Firma sin consentimiento explícito: mov={movimiento_id}, rol={rol_firma}, ip={ip_address}"
                )

            # Verificar si ya existe una firma para este rol
            existing_firma = db.session.execute(
                select(Firma).where(
                    Firma.documento_id == movimiento_id,
                    Firma.tipo_documento == 'movimiento',
                    Firma.rol_firma == rol_firma
                )
            ).scalar_one_or_none()

            if existing_firma:
                # Actualizar firma existente
                existing_firma.firma_base64 = signature_b64
                existing_firma.nombre_firmante = nombre_firmante  # ✅ NUEVO
                existing_firma.firma_svg = signature_svg
                existing_firma.ip_address = ip_address
                existing_firma.user_agent = user_agent
                existing_firma.timestamp_firma = datetime.utcnow()
                existing_firma.hash_documento = doc_hash
                existing_firma.consentimiento_aceptado = consentimiento

                current_app.logger.info(
                    f"🔄 Firma actualizada: mov={movimiento_id}, rol={rol_firma}, "
                    f"ip={ip_address}, svg={len(signature_svg or '')} chars"
                )
            else:
                # Crear nueva firma
                nueva_firma = Firma(
                    documento_id=movimiento_id,
                    tipo_documento='movimiento',
                    rol_firma=rol_firma,
                    nombre_firmante=nombre_firmante,  # ✅ NUEVO
                    firma_base64=signature_b64,
                    firma_svg=signature_svg,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp_firma=datetime.utcnow(),
                    hash_documento=doc_hash,
                    consentimiento_aceptado=consentimiento
                )
                db.session.add(nueva_firma)

                current_app.logger.info(
                    f"✅ Nueva firma guardada: mov={movimiento_id}, rol={rol_firma}, "
                    f"ip={ip_address}, hash={doc_hash[:12]}..., svg={len(signature_svg or '')} chars"
                )

            db.session.commit()

            # ✅ Log detallado de auditoría (para cumplimiento legal)
            current_app.logger.info(
                f"[AUDITORIA_FIRMA] "
                f"timestamp={datetime.utcnow().isoformat()} | "
                f"movimiento_id={movimiento_id} | "
                f"tipo={movimiento.tipo_movimiento} | "
                f"rol={rol_firma} | "
                f"ip={ip_address} | "
                f"hash_doc={doc_hash} | "
                f"consentimiento={consentimiento} | "
                f"user_agent={user_agent[:50]}..."
            )

            # ✅ Metadata adicional del cliente (solo para debug, no se guarda en DB)
            if metadata:
                current_app.logger.debug(
                    f"[METADATA_CLIENTE] mov={movimiento_id}, rol={rol_firma}, "
                    f"screen={metadata.get('screen_resolution')}, "
                    f"timezone={metadata.get('timezone')}"
                )

            return jsonify({
                'success': True,
                'message': 'Firma guardada exitosamente con metadata de auditoría.',
                'image_url': signature_b64,
                'debug_info': {
                    'hash': doc_hash[:12],
                    'ip': ip_address,
                    'timestamp': datetime.utcnow().isoformat(),
                    'svg_size': len(signature_svg or ''),
                    'consentimiento': consentimiento
                }
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"❌ Error al guardar firma: mov={movimiento_id}, rol={data.get('rol_firma', 'desconocido')}, "
                f"error={str(e)}",
                exc_info=True
            )
            return jsonify({
                'success': False,
                'message': f'Error interno al guardar la firma: {str(e)}'
            }), 500

    # --- Lógica para el método GET ---
    try:
        # Cargar roles requeridos desde el archivo JSON
        firmas_config_path = os.path.join(current_app.root_path, '..', 'firmas_requeridas.json')
        with open(firmas_config_path, 'r', encoding='utf-8') as f:
            roles_config = json.load(f)
        
        tipo_mov_key = movimiento.tipo_movimiento.lower().replace('/', '_')
        roles_requeridos = roles_config.get(tipo_mov_key, [])

        # Cargar firmas ya guardadas
        firmas_guardadas = {f.rol_firma: f.firma_base64 for f in movimiento.firmas}

        # Cargar detalles específicos usando la relación del modelo
        detalles = getattr(movimiento, f"detalle_{movimiento.tipo_movimiento.lower().replace('/', '_')}", None)

        # Cargar activos y sus accesorios
        activos_con_accesorios = []
        for ma in movimiento.activos:
            activo_info = {
                'activo': ma.activo,
                'accesorios': ma.accesorios
            }
            activos_con_accesorios.append(activo_info)

        return render_template(
            'firmar.html',
            movimiento=movimiento,
            roles_requeridos=roles_requeridos,
            firmas_guardadas=firmas_guardadas,
            detalles=detalles,
            activos_con_accesorios=activos_con_accesorios
        )
    except FileNotFoundError:
        flash("Error: El archivo 'firmas_requeridas.json' no se encuentra.", 'danger')
        return redirect(url_for('movimientos.ver_movimiento', movimiento_id=movimiento_id))
    except Exception as e:
        flash(f"Error al cargar la página de firmas: {e}", 'danger')
        return redirect(url_for('movimientos.ver_movimiento', movimiento_id=movimiento_id))


@movimientos_bp.route('/firmar/<int:movimiento_id>/<string:rol_firma>', methods=['DELETE'])
@login_required
def eliminar_firma(movimiento_id, rol_firma):
    """
    Elimina una firma específica de un movimiento.
    """
    try:
        firma_a_eliminar = db.session.execute(
            select(Firma).where(
                Firma.documento_id == movimiento_id,
                Firma.tipo_documento == 'movimiento',
                Firma.rol_firma == rol_firma
            )
        ).scalar_one_or_none()

        if not firma_a_eliminar:
            return jsonify({'success': False, 'message': 'Firma no encontrada.'}), 404

        db.session.delete(firma_a_eliminar)
        db.session.commit()
        
        current_app.logger.info(f"Firma eliminada para rol '{rol_firma}' en movimiento {movimiento_id}.")

        return jsonify({'success': True, 'message': 'Firma eliminada correctamente.'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar firma para movimiento {movimiento_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error interno del servidor: {e}'}), 500
