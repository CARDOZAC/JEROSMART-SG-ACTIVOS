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


@activos.command("import-conciliacion")
@click.argument("archivo_csv", type=click.Path(exists=True))
@click.option(
    "--usuario-id",
    type=int,
    default=None,
    help="ID del usuario que realiza la verificación (opcional)",
)
@click.option(
    "--estado",
    type=click.Choice(["Verificado", "Pendiente", "No Encontrado"]),
    default="Verificado",
    help="Estado de conciliación a establecer (default: Verificado)",
)
@click.option(
    "--dry-run", is_flag=True, help="Simula la importación sin hacer cambios en la BD"
)
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
        with open(archivo_csv, "r", encoding="utf-8-sig") as file:
            # Detectar dialecto CSV
            sample = file.read(1024)
            file.seek(0)
            dialect = csv.Sniffer().sniff(sample)

            reader = csv.DictReader(file, dialect=dialect)

            # Validar columnas requeridas
            if "placa_codigo_interno" not in reader.fieldnames:
                click.echo(
                    "Error: El archivo CSV debe tener la columna 'placa_codigo_interno'"
                )
                click.echo(f"   Columnas encontradas: {', '.join(reader.fieldnames)}")
                return

            # Procesar registros
            activos_procesados = 0
            activos_actualizados = 0
            activos_no_encontrados = []
            errores = []

            for idx, row in enumerate(
                reader, start=2
            ):  # Línea 2 porque línea 1 es el header
                placa = row.get("placa_codigo_interno", "").strip()

                if not placa:
                    click.echo(f"Linea {idx}: Placa vacia, saltando...")
                    continue

                # Buscar activo en la BD
                activo = Activo.query.filter_by(placa_codigo_interno=placa).first()

                if not activo:
                    activos_no_encontrados.append(placa)
                    click.echo(
                        f"Linea {idx}: Activo con placa '{placa}' NO encontrado en BD"
                    )
                    continue

                # Obtener datos de verificación
                estado_csv = row.get("estado_conciliacion", estado).strip()
                notas = row.get("notas_verificacion", "").strip() or None

                # Validar estado
                if estado_csv not in ["Verificado", "Pendiente", "No Encontrado"]:
                    click.echo(
                        f"ATENCION  Línea {idx}: Estado '{estado_csv}' inválido, usando '{estado}'"
                    )
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
                            campo_modificado="CONCILIACION_FISICA",
                            valor_anterior=f"Estado: {estado_anterior}, Fecha: {fecha_anterior}",
                            valor_nuevo=f"Estado: {estado_csv}, Fecha: {datetime.utcnow().isoformat()}",
                            usuario_id=usuario_id,
                            timestamp=datetime.utcnow(),
                            tipo_operacion="VERIFICACION",
                            observaciones=f'Importación masiva de conciliación. Notas: {notas or "N/A"}',
                        )
                        db.session.add(historial)

                        activos_actualizados += 1
                        click.echo(
                            f"OK  Línea {idx}: Activo '{placa}' actualizado a '{estado_csv}'"
                        )
                    except Exception as e:
                        errores.append(f"Línea {idx} ({placa}): {str(e)}")
                        click.echo(
                            f"ERROR Línea {idx}: Error al actualizar '{placa}': {str(e)}"
                        )
                        continue
                else:
                    click.echo(
                        f"OK  Línea {idx}: [SIMULACIÓN] Activo '{placa}' -> '{estado_csv}'"
                    )
                    activos_actualizados += 1

                activos_procesados += 1

                # Commit cada 100 registros para evitar transacciones muy grandes
                if not dry_run and activos_procesados % 100 == 0:
                    db.session.commit()
                    click.echo(
                        f"GUARDANDO Checkpoint: {activos_procesados} activos procesados, cambios guardados"
                    )

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
        click.echo(
            f"\nATENCION  Esta fue una SIMULACIÓN. Ejecuta sin --dry-run para aplicar cambios."
        )
    else:
        click.echo(f"\nOK Importación completada exitosamente!")

    click.echo(f"{'='*70}\n")


@activos.command("marcar-verificados")
@click.option("--todos", is_flag=True, help="Marcar TODOS los activos como Verificados")
@click.option(
    "--usuario-id",
    type=int,
    default=None,
    help="ID del usuario que realiza la verificación",
)
@click.option(
    "--solo-pendientes",
    is_flag=True,
    help="Solo marcar activos que estén en estado Pendiente",
)
@click.option("--dry-run", is_flag=True, help="Simula la operación sin hacer cambios")
@with_appcontext
def marcar_verificados(todos, usuario_id, solo_pendientes, dry_run):
    """
    Marca activos como Verificados en masa.

    Ejemplo de uso:
        flask activos marcar-verificados --todos --usuario-id 1
        flask activos marcar-verificados --todos --solo-pendientes --dry-run
    """
    if not todos:
        click.echo(
            "ERROR Debes usar la opción --todos para confirmar que deseas marcar todos los activos."
        )
        click.echo(
            "   Esto es una medida de seguridad para evitar cambios masivos accidentales."
        )
        return

    click.echo(f"\n{'='*70}")
    click.echo(f"OK MARCADO MASIVO DE ACTIVOS COMO VERIFICADOS")
    click.echo(f"{'='*70}\n")

    if dry_run:
        click.echo(
            "ATENCION  MODO SIMULACIÓN (--dry-run): No se harán cambios en la BD\n"
        )

    # Construir query
    query = Activo.query
    if solo_pendientes:
        query = query.filter_by(estado_conciliacion="Pendiente")
        click.echo("🔍 Filtro: Solo activos con estado 'Pendiente'")

    activos = query.all()
    total = len(activos)

    if total == 0:
        click.echo("ATENCION  No se encontraron activos para actualizar.")
        return

    click.echo(f" Total de activos a actualizar: {total}\n")

    if total > 1000:
        click.confirm(
            f"ATENCION  Vas a actualizar {total} activos. ¿Continuar?", abort=True
        )

    # Actualizar activos
    actualizados = 0
    fecha_verificacion = datetime.utcnow()

    for activo in activos:
        if not dry_run:
            try:
                estado_anterior = activo.estado_conciliacion
                activo.estado_conciliacion = "Verificado"
                activo.fecha_ultima_verificacion = fecha_verificacion
                activo.usuario_ultima_verificacion_id = usuario_id

                # Registro de auditoría
                historial = ActivoHistorico(
                    activo_id=activo.id,
                    campo_modificado="estado_conciliacion",
                    valor_anterior=estado_anterior,
                    valor_nuevo="Verificado",
                    usuario_id=usuario_id,
                    timestamp=fecha_verificacion,
                    tipo_operacion="VERIFICACION",
                    observaciones="Verificación masiva mediante CLI",
                )
                db.session.add(historial)

                actualizados += 1

                # Commit cada 500 registros
                if actualizados % 500 == 0:
                    db.session.commit()
                    click.echo(
                        f"GUARDANDO Checkpoint: {actualizados}/{total} activos actualizados"
                    )
            except Exception as e:
                click.echo(
                    f"ERROR Error al actualizar activo {activo.placa_codigo_interno}: {str(e)}"
                )
                continue
        else:
            actualizados += 1

    if not dry_run:
        db.session.commit()

    click.echo(f"\n{'='*70}")
    click.echo(
        f"OK Operación completada: {actualizados}/{total} activos marcados como Verificados"
    )
    if dry_run:
        click.echo(
            f"ATENCION  Esta fue una SIMULACIÓN. Ejecuta sin --dry-run para aplicar cambios."
        )
    click.echo(f"{'='*70}\n")


@activos.command("estadisticas-conciliacion")
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
    verificados = Activo.query.filter_by(estado_conciliacion="Verificado").count()
    pendientes = Activo.query.filter_by(estado_conciliacion="Pendiente").count()
    no_encontrados = Activo.query.filter_by(estado_conciliacion="No Encontrado").count()

    # Calcular porcentajes
    pct_verificados = (verificados / total * 100) if total > 0 else 0
    pct_pendientes = (pendientes / total * 100) if total > 0 else 0
    pct_no_encontrados = (no_encontrados / total * 100) if total > 0 else 0

    click.echo(f"Total de activos: {total}")
    click.echo(f"{'='*70}")
    click.echo(f"OK  Verificados:     {verificados:6d} ({pct_verificados:5.1f}%)")
    click.echo(f"PEND Pendientes:      {pendientes:6d} ({pct_pendientes:5.1f}%)")
    click.echo(
        f"ERROR No Encontrados:  {no_encontrados:6d} ({pct_no_encontrados:5.1f}%)"
    )
    click.echo(f"{'='*70}\n")

    # Barra de progreso visual
    barra_width = 50
    barra_verificados = int(pct_verificados / 100 * barra_width)
    barra_pendientes = int(pct_pendientes / 100 * barra_width)
    barra_no_encontrados = int(pct_no_encontrados / 100 * barra_width)

    click.echo("Progreso visual:")
    click.echo(
        f"[{'#' * barra_verificados}{'-' * (barra_width - barra_verificados)}] Verificados"
    )
    click.echo(
        f"[{'*' * barra_pendientes}{'-' * (barra_width - barra_pendientes)}] Pendientes"
    )
    click.echo(
        f"[{'+' * barra_no_encontrados}{'-' * (barra_width - barra_no_encontrados)}] No Encontrados"
    )

    click.echo(f"\n{'='*70}\n")


def init_cli(app):
    """Registra los comandos CLI en la aplicación Flask."""
    app.cli.add_command(activos)
