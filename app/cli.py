"""
Comandos CLI para gestión de activos fijos - JeroSmart
FASE 1.1: Sistema de Conciliación Física (Anti-Activo Fantasma)
"""
import click
from flask.cli import with_appcontext
from flask import current_app
from datetime import datetime
import csv
import os
from .extensions import db
from .models import Activo, User, ActivoHistorico
from flask_login import current_user


@click.group()
def activos():
    """Comandos para gestión de activos fijos."""
    pass


@activos.command('import-conciliacion')
@click.argument('archivo_csv', type=click.Path(exists=True))
@click.option('--usuario-id', type=int, default=None,
              help='ID del usuario que realiza la verificación (opcional)')
@click.option('--estado', type=click.Choice(['Verificado', 'Pendiente', 'No Encontrado']),
              default='Verificado',
              help='Estado de conciliación a establecer (default: Verificado)')
@click.option('--dry-run', is_flag=True,
              help='Simula la importación sin hacer cambios en la BD')
@with_appcontext
def import_conciliacion(archivo_csv, usuario_id, estado, dry_run):
    """
    Importa el estado de conciliación física de activos desde un archivo CSV.

    El archivo CSV debe tener las siguientes columnas:
    - placa_codigo_interno: Código o placa del activo (OBLIGATORIO)
    - estado_conciliacion: Estado (opcional, usa --estado si no se especifica)
    - notas_verificacion: Observaciones de la verificación (opcional)

    Ejemplo de uso:
        flask activos import-conciliacion activos_verificados.csv
        flask activos import-conciliacion activos.csv --estado Verificado --usuario-id 1
        flask activos import-conciliacion activos.csv --dry-run
    """
    click.echo(f"\n{'='*70}")
    click.echo(f"IMPORTACION DE CONCILIACION FISICA DE ACTIVOS")
    click.echo(f"{'='*70}\n")

    if dry_run:
        click.echo("MODO SIMULACION (--dry-run): No se haran cambios en la BD\n")

    # Validar usuario si se especificó
    usuario = None
    if usuario_id:
        usuario = User.query.get(usuario_id)
        if not usuario:
            click.echo(f"Error: Usuario con ID {usuario_id} no encontrado.")
            return
        click.echo(f"Usuario verificador: {usuario.email} (ID: {usuario.id})")
    else:
        click.echo("Usuario verificador: No especificado (usara NULL)")

    click.echo(f"Archivo: {archivo_csv}")
    click.echo(f"Estado default: {estado}\n")

    # Leer archivo CSV
    try:
        with open(archivo_csv, 'r', encoding='utf-8-sig') as file:
            # Detectar dialecto CSV
            sample = file.read(1024)
            file.seek(0)
            dialect = csv.Sniffer().sniff(sample)

            reader = csv.DictReader(file, dialect=dialect)

            # Validar columnas requeridas
            if 'placa_codigo_interno' not in reader.fieldnames:
                click.echo("Error: El archivo CSV debe tener la columna 'placa_codigo_interno'")
                click.echo(f"   Columnas encontradas: {', '.join(reader.fieldnames)}")
                return

            # Procesar registros
            activos_procesados = 0
            activos_actualizados = 0
            activos_no_encontrados = []
            errores = []

            for idx, row in enumerate(reader, start=2):  # Línea 2 porque línea 1 es el header
                placa = row.get('placa_codigo_interno', '').strip()

                if not placa:
                    click.echo(f"Linea {idx}: Placa vacia, saltando...")
                    continue

                # Buscar activo en la BD
                activo = Activo.query.filter_by(placa_codigo_interno=placa).first()

                if not activo:
                    activos_no_encontrados.append(placa)
                    click.echo(f"Linea {idx}: Activo con placa '{placa}' NO encontrado en BD")
                    continue

                # Obtener datos de verificación
                estado_csv = row.get('estado_conciliacion', estado).strip()
                notas = row.get('notas_verificacion', '').strip() or None

                # Validar estado
                if estado_csv not in ['Verificado', 'Pendiente', 'No Encontrado']:
                    click.echo(f"ATENCION  Línea {idx}: Estado '{estado_csv}' inválido, usando '{estado}'")
                    estado_csv = estado

                # Actualizar activo
                if not dry_run:
                    try:
                        # Guardar valores anteriores para auditoría
                        estado_anterior = activo.estado_conciliacion
                        fecha_anterior = activo.fecha_ultima_verificacion

                        # Actualizar campos
                        activo.estado_conciliacion = estado_csv
                        activo.fecha_ultima_verificacion = datetime.utcnow()
                        activo.usuario_ultima_verificacion_id = usuario_id
                        activo.notas_verificacion = notas

                        db.session.add(activo)

                        # Crear registro de auditoría manual (los event listeners también lo harán)
                        historial = ActivoHistorico(
                            activo_id=activo.id,
                            campo_modificado='CONCILIACION_FISICA',
                            valor_anterior=f'Estado: {estado_anterior}, Fecha: {fecha_anterior}',
                            valor_nuevo=f'Estado: {estado_csv}, Fecha: {datetime.utcnow().isoformat()}',
                            usuario_id=usuario_id,
                            timestamp=datetime.utcnow(),
                            tipo_operacion='VERIFICACION',
                            observaciones=f'Importación masiva de conciliación. Notas: {notas or "N/A"}'
                        )
                        db.session.add(historial)

                        activos_actualizados += 1
                        click.echo(f"OK  Línea {idx}: Activo '{placa}' actualizado a '{estado_csv}'")
                    except Exception as e:
                        errores.append(f"Línea {idx} ({placa}): {str(e)}")
                        click.echo(f"ERROR Línea {idx}: Error al actualizar '{placa}': {str(e)}")
                        continue
                else:
                    click.echo(f"OK  Línea {idx}: [SIMULACIÓN] Activo '{placa}' -> '{estado_csv}'")
                    activos_actualizados += 1

                activos_procesados += 1

                # Commit cada 100 registros para evitar transacciones muy grandes
                if not dry_run and activos_procesados % 100 == 0:
                    db.session.commit()
                    click.echo(f"GUARDANDO Checkpoint: {activos_procesados} activos procesados, cambios guardados")

            # Commit final
            if not dry_run:
                db.session.commit()

    except FileNotFoundError:
        click.echo(f"ERROR Error: Archivo '{archivo_csv}' no encontrado.")
        return
    except csv.Error as e:
        click.echo(f"ERROR Error al leer CSV: {str(e)}")
        return
    except Exception as e:
        if not dry_run:
            db.session.rollback()
        click.echo(f"ERROR Error inesperado: {str(e)}")
        import traceback
        click.echo(traceback.format_exc())
        return

    # Resumen
    click.echo(f"\n{'='*70}")
    click.echo(f" RESUMEN DE IMPORTACIÓN")
    click.echo(f"{'='*70}")
    click.echo(f"OK  Activos procesados: {activos_procesados}")
    click.echo(f"OK  Activos actualizados: {activos_actualizados}")
    click.echo(f"ATENCION  Activos no encontrados en BD: {len(activos_no_encontrados)}")
    click.echo(f"ERROR Errores: {len(errores)}")

    if activos_no_encontrados:
        click.echo(f"\nATENCION  Activos NO encontrados en la BD:")
        for placa in activos_no_encontrados[:10]:  # Mostrar solo primeros 10
            click.echo(f"   - {placa}")
        if len(activos_no_encontrados) > 10:
            click.echo(f"   ... y {len(activos_no_encontrados) - 10} más")

    if errores:
        click.echo(f"\nERROR Errores durante la importación:")
        for error in errores[:5]:  # Mostrar solo primeros 5
            click.echo(f"   - {error}")
        if len(errores) > 5:
            click.echo(f"   ... y {len(errores) - 5} más")

    if dry_run:
        click.echo(f"\nATENCION  Esta fue una SIMULACIÓN. Ejecuta sin --dry-run para aplicar cambios.")
    else:
        click.echo(f"\nOK Importación completada exitosamente!")

    click.echo(f"{'='*70}\n")


@activos.command('marcar-verificados')
@click.option('--todos', is_flag=True,
              help='Marcar TODOS los activos como Verificados')
@click.option('--usuario-id', type=int, default=None,
              help='ID del usuario que realiza la verificación')
@click.option('--solo-pendientes', is_flag=True,
              help='Solo marcar activos que estén en estado Pendiente')
@click.option('--dry-run', is_flag=True,
              help='Simula la operación sin hacer cambios')
@with_appcontext
def marcar_verificados(todos, usuario_id, solo_pendientes, dry_run):
    """
    Marca activos como Verificados en masa.

    Ejemplo de uso:
        flask activos marcar-verificados --todos --usuario-id 1
        flask activos marcar-verificados --todos --solo-pendientes --dry-run
    """
    if not todos:
        click.echo("ERROR Debes usar la opción --todos para confirmar que deseas marcar todos los activos.")
        click.echo("   Esto es una medida de seguridad para evitar cambios masivos accidentales.")
        return

    click.echo(f"\n{'='*70}")
    click.echo(f"OK MARCADO MASIVO DE ACTIVOS COMO VERIFICADOS")
    click.echo(f"{'='*70}\n")

    if dry_run:
        click.echo("ATENCION  MODO SIMULACIÓN (--dry-run): No se harán cambios en la BD\n")

    # Construir query
    query = Activo.query
    if solo_pendientes:
        query = query.filter_by(estado_conciliacion='Pendiente')
        click.echo("🔍 Filtro: Solo activos con estado 'Pendiente'")

    activos = query.all()
    total = len(activos)

    if total == 0:
        click.echo("ATENCION  No se encontraron activos para actualizar.")
        return

    click.echo(f" Total de activos a actualizar: {total}\n")

    if total > 1000:
        click.confirm(f"ATENCION  Vas a actualizar {total} activos. ¿Continuar?", abort=True)

    # Actualizar activos
    actualizados = 0
    fecha_verificacion = datetime.utcnow()

    for activo in activos:
        if not dry_run:
            try:
                estado_anterior = activo.estado_conciliacion
                activo.estado_conciliacion = 'Verificado'
                activo.fecha_ultima_verificacion = fecha_verificacion
                activo.usuario_ultima_verificacion_id = usuario_id

                # Registro de auditoría
                historial = ActivoHistorico(
                    activo_id=activo.id,
                    campo_modificado='estado_conciliacion',
                    valor_anterior=estado_anterior,
                    valor_nuevo='Verificado',
                    usuario_id=usuario_id,
                    timestamp=fecha_verificacion,
                    tipo_operacion='VERIFICACION',
                    observaciones='Verificación masiva mediante CLI'
                )
                db.session.add(historial)

                actualizados += 1

                # Commit cada 500 registros
                if actualizados % 500 == 0:
                    db.session.commit()
                    click.echo(f"GUARDANDO Checkpoint: {actualizados}/{total} activos actualizados")
            except Exception as e:
                click.echo(f"ERROR Error al actualizar activo {activo.placa_codigo_interno}: {str(e)}")
                continue
        else:
            actualizados += 1

    if not dry_run:
        db.session.commit()

    click.echo(f"\n{'='*70}")
    click.echo(f"OK Operación completada: {actualizados}/{total} activos marcados como Verificados")
    if dry_run:
        click.echo(f"ATENCION  Esta fue una SIMULACIÓN. Ejecuta sin --dry-run para aplicar cambios.")
    click.echo(f"{'='*70}\n")


@activos.command('estadisticas-conciliacion')
@with_appcontext
def estadisticas_conciliacion():
    """
    Muestra estadísticas del estado de conciliación física de activos.
    """
    click.echo(f"\n{'='*70}")
    click.echo(f" ESTADÍSTICAS DE CONCILIACIÓN FÍSICA")
    click.echo(f"{'='*70}\n")

    # Contar por estado
    total = Activo.query.count()
    verificados = Activo.query.filter_by(estado_conciliacion='Verificado').count()
    pendientes = Activo.query.filter_by(estado_conciliacion='Pendiente').count()
    no_encontrados = Activo.query.filter_by(estado_conciliacion='No Encontrado').count()

    # Calcular porcentajes
    pct_verificados = (verificados / total * 100) if total > 0 else 0
    pct_pendientes = (pendientes / total * 100) if total > 0 else 0
    pct_no_encontrados = (no_encontrados / total * 100) if total > 0 else 0

    click.echo(f"Total de activos: {total}")
    click.echo(f"{'='*70}")
    click.echo(f"OK  Verificados:     {verificados:6d} ({pct_verificados:5.1f}%)")
    click.echo(f"PEND Pendientes:      {pendientes:6d} ({pct_pendientes:5.1f}%)")
    click.echo(f"ERROR No Encontrados:  {no_encontrados:6d} ({pct_no_encontrados:5.1f}%)")
    click.echo(f"{'='*70}\n")

    # Barra de progreso visual
    barra_width = 50
    barra_verificados = int(pct_verificados / 100 * barra_width)
    barra_pendientes = int(pct_pendientes / 100 * barra_width)
    barra_no_encontrados = int(pct_no_encontrados / 100 * barra_width)

    click.echo("Progreso visual:")
    click.echo(f"[{'#' * barra_verificados}{'-' * (barra_width - barra_verificados)}] Verificados")
    click.echo(f"[{'*' * barra_pendientes}{'-' * (barra_width - barra_pendientes)}] Pendientes")
    click.echo(f"[{'+' * barra_no_encontrados}{'-' * (barra_width - barra_no_encontrados)}] No Encontrados")

    click.echo(f"\n{'='*70}\n")


@activos.command('seed-demo')
@click.option('--forzar', is_flag=True,
              help='Crea los activos aunque ya existan otros en la base de datos.')
@with_appcontext
def seed_demo(forzar):
    """
    Crea 8 activos de ejemplo: 2 biomédicos, 2 electro-industriales,
    2 muebles y enseres y 2 equipos de TI.

    Es idempotente: los activos cuya placa ya exista se omiten.
    """
    from .models import ClaseActivo

    # Atributos dinámicos coherentes con ATRIBUTOS_POR_CLASE de cada módulo.
    DEMO = [
        # ---------- Equipo Biomédico (clase 1) ----------
        dict(placa='BIO-0001', nombre='Monitor de Signos Vitales', clase='Equipo Biomédico',
             marca='Mindray', modelo='ePM 12M', serie='MIN-EPM12-4417',
             ubicacion='Sala de Observación', valor=18500000.0,
             atributos={'registro_invima': '2023DM-0011245', 'clasificacion_riesgo': 'IIb',
                        'clasificacion_biomedica': 'Diagnóstico', 'fabricante': 'Mindray',
                        'pais_origen': 'China', 'vida_util': '10',
                        'frecuencia_mantenimiento': 'Semestral', 'requiere_calibracion': 'Sí',
                        'voltaje_operacion': '110V AC', 'potencia': '150'}),
        dict(placa='BIO-0002', nombre='Bomba de Infusión Volumétrica', clase='Equipo Biomédico',
             marca='B. Braun', modelo='Infusomat Space', serie='BRA-INF-90233',
             ubicacion='Hospitalización Piso 2', valor=9200000.0,
             atributos={'registro_invima': '2022DM-0009871', 'clasificacion_riesgo': 'IIb',
                        'clasificacion_biomedica': 'Tratamiento y Mantenimiento de la Vida',
                        'fabricante': 'B. Braun', 'pais_origen': 'Alemania', 'vida_util': '8',
                        'frecuencia_mantenimiento': 'Semestral', 'requiere_calibracion': 'Sí',
                        'voltaje_operacion': '110V AC', 'potencia': '45'}),

        # ---------- Equipo Electro-Industrial (clase 2) ----------
        dict(placa='IND-0001', nombre='Planta Eléctrica de Emergencia 60 KVA', clase='Equipo Electro-Industrial',
             marca='Cummins', modelo='C60D6', serie='CUM-60KVA-2210',
             ubicacion='Cuarto de Máquinas', valor=78000000.0,
             atributos={'voltaje_nominal': '220V AC', 'corriente_nominal': '157.5',
                        'potencia_nominal': '60 kVA', 'cumple_retie': 'Sí',
                        'certificado_conformidad': 'CC-RETIE-2022-4471',
                        'especificaciones_tecnicas': 'Motor diésel 4 tiempos, tablero de '
                                                     'transferencia automática, tanque 200 L.'}),
        dict(placa='IND-0002', nombre='Compresor de Aire Medicinal', clase='Equipo Electro-Industrial',
             marca='Atlas Copco', modelo='GA 15 VSD', serie='ATC-GA15-77120',
             ubicacion='Cuarto Técnico', valor=42300000.0,
             atributos={'voltaje_nominal': '220V AC', 'corriente_nominal': '41.2',
                        'potencia_nominal': '15 kW', 'cumple_retie': 'Sí',
                        'certificado_conformidad': 'CC-RETIE-2023-1188',
                        'especificaciones_tecnicas': 'Compresor de tornillo con variador de '
                                                     'velocidad y secador integrado.'}),

        # ---------- Muebles y Enseres (clase 4) ----------
        dict(placa='MUE-0001', nombre='Escritorio Ejecutivo en L', clase='Muebles y Enseres',
             marca='Office Line', modelo='EJ-160L', serie='OFL-160L-0455',
             ubicacion='Oficina Administrativa', valor=1350000.0,
             atributos={'tipo_mueble': 'Escritorio', 'material': 'Madera',
                        'dimensiones': '75cm x 160cm x 80cm', 'color': 'Wengue',
                        'estado_fisico': 'Bueno', 'tipo_adquisicion': 'Compra',
                        'especificaciones_tecnicas': 'Superficie en melamina de 25 mm con '
                                                     'pasacables y archivador de 3 gavetas.'}),
        dict(placa='MUE-0002', nombre='Archivador Metálico de 4 Gavetas', clase='Muebles y Enseres',
             marca='Metalúrgica Nacional', modelo='AR-4G', serie='MTN-AR4G-1902',
             ubicacion='Archivo Central', valor=890000.0,
             atributos={'tipo_mueble': 'Archivador', 'material': 'Metal',
                        'dimensiones': '132cm x 47cm x 62cm', 'color': 'Gris',
                        'estado_fisico': 'Excelente', 'tipo_adquisicion': 'Compra',
                        'especificaciones_tecnicas': 'Cuatro gavetas con rieles telescópicos '
                                                     'y cerradura central.'}),

        # ---------- TICs (clase 3) ----------
        dict(placa='TIC-0001', nombre='Computador Portátil Corporativo', clase='TICs',
             marca='Lenovo', modelo='ThinkPad T14 Gen 4', serie='LNV-T14-8821JK',
             ubicacion='Oficina de Sistemas', valor=5400000.0,
             atributos={'tipo_equipo': 'Portátil', 'procesador': 'Intel Core i7 1355U',
                        'ram': '16GB DDR5', 'almacenamiento': 'SSD 512GB NVMe',
                        'sistema_operativo': 'Windows 11 Pro',
                        'licencia_software': 'OEM-W11P-77213', 'direccion_ip': '192.168.1.45',
                        'direccion_mac': '3C:52:82:1A:9F:04', 'vida_util_estimada': '5'}),
        dict(placa='TIC-0002', nombre='Servidor de Aplicaciones en Rack', clase='TICs',
             marca='Dell', modelo='PowerEdge R650', serie='DEL-R650-30512',
             ubicacion='Centro de Cómputo', valor=32700000.0,
             atributos={'tipo_equipo': 'Servidor', 'procesador': 'Intel Xeon Silver 4310',
                        'ram': '64GB DDR4 ECC', 'almacenamiento': '2 x SSD 960GB RAID 1',
                        'sistema_operativo': 'Ubuntu Server 22.04 LTS',
                        'licencia_software': 'N/A (software libre)',
                        'direccion_ip': '192.168.1.10',
                        'direccion_mac': 'B0:7B:25:C4:11:87', 'vida_util_estimada': '7'}),
    ]

    click.echo(f"\n{'='*70}")
    click.echo('CREACION DE ACTIVOS DE EJEMPLO')
    click.echo(f"{'='*70}\n")

    existentes = db.session.scalar(db.select(db.func.count(Activo.id)))
    if existentes and not forzar:
        click.echo(f'La base de datos ya tiene {existentes} activo(s).')
        click.echo('Usa --forzar si aun asi quieres agregar los de ejemplo.')
        return

    # Mapear nombre de clase -> id, sin asumir los identificadores
    clases = {c.nombre_clase: c.id for c in db.session.scalars(db.select(ClaseActivo))}

    creados = omitidos = 0
    for item in DEMO:
        if db.session.scalar(db.select(Activo).where(Activo.placa_codigo_interno == item['placa'])):
            click.echo(f"  OMITIDO  {item['placa']}: la placa ya existe")
            omitidos += 1
            continue

        clase_id = clases.get(item['clase'])
        if clase_id is None:
            click.echo(f"  ERROR    {item['placa']}: no existe la clase '{item['clase']}'")
            omitidos += 1
            continue

        db.session.add(Activo(
            nombre_activo=item['nombre'],
            placa_codigo_interno=item['placa'],
            marca=item['marca'],
            modelo=item['modelo'],
            serie=item['serie'],
            ubicacion=item['ubicacion'],
            valor_comercial=item['valor'],
            estado='Operativo',
            tipo_propiedad='Propio',
            origen_adquisicion='Compra',
            clase_id=clase_id,
            estado_conciliacion='Pendiente',
            atributos_dinamicos_json=item['atributos'],
        ))
        creados += 1
        click.echo(f"  CREADO   {item['placa']}  {item['nombre']}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        click.echo(f'\nERROR al guardar: {e}')
        return

    click.echo(f"\n{'='*70}")
    click.echo(f'Activos creados: {creados} | omitidos: {omitidos}')
    click.echo(f"{'='*70}\n")


@activos.command('normalizar-json')
@click.option('--dry-run', is_flag=True, help='Muestra los cambios sin aplicarlos.')
@with_appcontext
def normalizar_json(dry_run):
    """
    Convierte a arrays los campos JSON que se guardaron como cadena.

    Algunas columnas db.JSON recibían json.dumps(...), de modo que MySQL
    almacenaba el texto "[\\"a\\",\\"b\\"]" en lugar del array ["a","b"]. Eso
    impide usar las funciones JSON nativas (JSON_CONTAINS, ->>). El código ya
    escribe listas; este comando arregla los registros anteriores.
    """
    from sqlalchemy import text

    objetivos = [
        ('detalles_entrega', 'tipo_elementos'),
        ('detalles_traslado', 'tipo_traslado_json'),
        ('detalles_traslado', 'accesorios_generales_json'),
        ('activos', 'atributos_dinamicos_json'),
        ('mantenimientos', 'atributos_reporte_json'),
    ]

    click.echo(f"\n{'='*70}")
    click.echo('NORMALIZACION DE COLUMNAS JSON')
    click.echo(f"{'='*70}\n")
    if dry_run:
        click.echo('MODO SIMULACION: no se guardaran cambios.\n')

    total = 0
    for tabla, columna in objetivos:
        try:
            afectadas = db.session.execute(text(
                f"SELECT COUNT(*) FROM `{tabla}` "
                f"WHERE `{columna}` IS NOT NULL AND JSON_TYPE(`{columna}`) = 'STRING'"
            )).scalar()
        except Exception as e:
            click.echo(f'  {tabla}.{columna}: no se pudo inspeccionar ({type(e).__name__})')
            continue

        if not afectadas:
            click.echo(f'  {tabla}.{columna}: sin filas afectadas')
            continue

        click.echo(f'  {tabla}.{columna}: {afectadas} fila(s) por convertir')
        total += afectadas

        if not dry_run:
            # JSON_UNQUOTE devuelve el texto interno y CAST lo reinterpreta
            # como documento JSON.
            db.session.execute(text(
                f"UPDATE `{tabla}` "
                f"SET `{columna}` = CAST(JSON_UNQUOTE(`{columna}`) AS JSON) "
                f"WHERE `{columna}` IS NOT NULL AND JSON_TYPE(`{columna}`) = 'STRING'"
            ))

    if not dry_run and total:
        db.session.commit()

    click.echo(f"\n{'='*70}")
    click.echo(f'Filas normalizadas: {total}')
    if dry_run and total:
        click.echo('Ejecuta sin --dry-run para aplicar los cambios.')
    click.echo(f"{'='*70}\n")


@activos.command('normalizar-rutas-archivos')
@click.option('--dry-run', is_flag=True, help='Muestra los cambios sin aplicarlos.')
@with_appcontext
def normalizar_rutas_archivos(dry_run):
    """
    Convierte a relativas las rutas absolutas de archivos adjuntos.

    Por un fallo en `_save_file`, las rutas de facturas, órdenes de compra y
    contratos se guardaban como rutas absolutas de Windows
    (C:\\...\\uploads\\invoices\\x.pdf). Eso rompe los enlaces al mover el
    proyecto o desplegar en otro sistema. Este comando las deja como
    'invoices/x.pdf'.
    """
    import os

    campos = ['ruta_orden_compra', 'ruta_factura', 'ruta_contrato_arriendo', 'ruta_foto_activo']
    base = os.path.normpath(current_app.config['UPLOAD_FOLDER'])

    click.echo(f"\n{'='*70}")
    click.echo('NORMALIZACION DE RUTAS DE ARCHIVOS ADJUNTOS')
    click.echo(f"{'='*70}")
    click.echo(f'Carpeta base: {base}\n')
    if dry_run:
        click.echo('MODO SIMULACION: no se guardaran cambios.\n')

    corregidas = 0
    for activo in Activo.query.all():
        for campo in campos:
            valor = getattr(activo, campo, None)
            if not valor:
                continue

            # Absoluta si tiene unidad de disco (C:) o empieza por separador
            if not (os.path.isabs(valor) or ':' in valor[:3]):
                continue

            normalizada = os.path.normpath(valor)
            if normalizada.lower().startswith(base.lower()):
                relativa = os.path.relpath(normalizada, base)
            else:
                # No cuelga de UPLOAD_FOLDER: se conservan las dos últimas
                # partes (subcarpeta/archivo), que es el formato esperado.
                partes = normalizada.replace('\\', '/').split('/')
                relativa = '/'.join(partes[-2:])

            relativa = relativa.replace('\\', '/')
            click.echo(f'  {activo.placa_codigo_interno} · {campo}')
            click.echo(f'      antes:   {valor}')
            click.echo(f'      despues: {relativa}')
            if not dry_run:
                setattr(activo, campo, relativa)
            corregidas += 1

    if not dry_run and corregidas:
        db.session.commit()

    click.echo(f"\n{'='*70}")
    click.echo(f'Rutas corregidas: {corregidas}')
    if dry_run and corregidas:
        click.echo('Ejecuta sin --dry-run para aplicar los cambios.')
    click.echo(f"{'='*70}\n")


def init_cli(app):
    """Registra los comandos CLI en la aplicación Flask."""
    # El módulo se llama cli_db y no db a propósito: un submódulo llamado
    # `app.db` se enlaza como atributo del paquete al importarlo y tapa la
    # instancia SQLAlchemy que `app/__init__.py` exporta con ese mismo nombre,
    # rompiendo cualquier `from app import db`.
    from .cli_db import init_db_command

    app.cli.add_command(activos)
    app.cli.add_command(init_db_command)
