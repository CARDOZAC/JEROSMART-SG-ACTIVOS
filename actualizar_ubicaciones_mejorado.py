#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
SCRIPT: Actualizar Ubicaciones desde CSVs de Migración (MEJORADO)
Fecha: 2025-11-19
Estilo: Petr - Robusto, limpio, bien documentado
============================================================================

MEJORAS SOBRE EL SCRIPT ORIGINAL:
    1. ✅ Normaliza automáticamente las ubicaciones (corrige inconsistencias)
    2. ✅ Actualiza el archivo ubicacion_selector.js con nuevas ubicaciones
    3. ✅ Procesa múltiples CSVs automáticamente
    4. ✅ Genera reporte detallado con ubicaciones nuevas encontradas
    5. ✅ Mapeo robusto de ubicaciones inconsistentes

USO:
    python actualizar_ubicaciones_mejorado.py [ruta_csv]

    Si no se proporciona ruta, procesa TODOS los CSVs en 'uploads/'
"""

import csv
import sys
import os
import re
from pathlib import Path
from datetime import datetime

# Configurar variables de entorno para MySQL ANTES de importar app
os.environ['DB_TYPE'] = 'mysql'
os.environ['DB_USER'] = 'root'
# La credencial se lee de .env; no se escribe en el código.
os.environ['DB_NAME'] = 'jerosmart_activos'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '3306'

from app import create_app
from app.models import Activo
from app.extensions import db
from sqlalchemy import select


# ============================================================================
# MAPEO DE NORMALIZACIÓN DE UBICACIONES
# ============================================================================

NORMALIZACION_UBICACIONES = {
    # Inconsistencias detectadas en los CSVs
    'Hospitalizacion 2 VIP': 'Hospitalización 2P VIP',
    'Hospitalizacion 5A': 'Hospitalización 5A',
    'Hospitalizacion 5B': 'Hospitalización 5B',
    'Hospitalizacion 6A': 'Hospitalización 6A',
    'Hospitalizacion 6B': 'Hospitalización 6B',
    'Hemodinamia': 'Hemodinamia',
    'Oncologia': 'Oncología',
    'Oncologia consultorio': 'Oncología',
    'Imagenologia': 'Imagenología',
    'Gastroenterologia': 'Gastroenterología',
    'Farmacia CEDI': 'Farmacia',
    'Farmacia Cirugia': 'Salas de CX',
    'Farmacia Hemodinamia': 'Hemodinamia',
    'Farmacia Hospitalizacion': 'Farmacia',
    'Farmacia Oncologia': 'Oncología',
    'Central esterilizacion': 'Central de Esterilización',
    'Cirugia': 'Salas de CX',
    'Clinica de heridas': 'Clínica de Heridas',
    'Terapia Fisica': 'Oficina de Terapia',
    'Terapia fisica': 'Oficina de Terapia',
    'Taller biomedico': 'Taller Biomédico',
    'Urgencias': 'Isla de Enfermería Urgencias',
    'Urgencias 7 piso': 'Urgencias Séptimo Piso',
    'Vacunacion': 'Vacunación',
    'Ensayos clinicos': 'Consulta Externa',
    'Cardiologia': 'Unidad de Diagnóstico Cardiovascular y Neumológico',
    'Bodega 4': 'Bodega CEDI S1',
    'Bodega 4to piso': 'Bodega CEDI S1',
    'Bodega patologia': 'Laboratorio Primer Piso',
    'Taller- para retirar': 'Taller Biomédico',
    'Consulta externa': 'Consulta Externa',

    # Ubicaciones que parecen códigos o IDs - mapear a descriptivo
    'PC0023': 'Oficina de Sistemas',
}

# Valores que se deben ignorar (no son ubicaciones válidas)
UBICACIONES_IGNORAR = {
    'PENDIENTE',
    'NT',
    'No aplica',
    'Na',
    'N/A',
    '',
    'Sin ubicación',
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def es_codigo_numerico(texto):
    """Verifica si un texto parece ser un código numérico (no una ubicación real)."""
    # Si es solo números o números con espacios
    return bool(re.match(r'^[\d\s]+$', texto.strip()))


def normalizar_ubicacion(ubicacion_original):
    """
    Normaliza una ubicación aplicando el mapeo de correcciones.

    Args:
        ubicacion_original (str): Ubicación original del CSV

    Returns:
        str: Ubicación normalizada o None si debe ignorarse
    """
    if not ubicacion_original:
        return None

    ubicacion = ubicacion_original.strip()

    # Ignorar valores no válidos
    if ubicacion in UBICACIONES_IGNORAR:
        return None

    # Ignorar códigos numéricos
    if es_codigo_numerico(ubicacion):
        print(f"   ⚠️  '{ubicacion}' parece un código, se marcará como 'Sin Ubicación Asignada'")
        return 'Sin Ubicación Asignada'

    # Aplicar normalización si existe en el mapeo
    ubicacion_normalizada = NORMALIZACION_UBICACIONES.get(ubicacion, ubicacion)

    return ubicacion_normalizada


def detectar_codificacion(archivo_csv):
    """Detecta la codificación del archivo CSV"""
    with open(archivo_csv, 'rb') as f:
        contenido_bytes = f.read()

    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']

    for encoding in encodings:
        try:
            contenido_bytes.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

    return 'utf-8'  # Default


def actualizar_ubicaciones_desde_csv(archivo_csv):
    """
    Lee el archivo CSV y actualiza las ubicaciones de los activos existentes.
    Aplica normalización automática de ubicaciones.
    """

    print(f"\n📁 Procesando: {Path(archivo_csv).name}")
    print("=" * 70)

    # Detectar codificación
    encoding = detectar_codificacion(archivo_csv)

    # Leer CSV
    try:
        with open(archivo_csv, 'r', encoding=encoding) as f:
            contenido_csv = f.read()
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return {'actualizados': 0, 'errores': 0}

    # Parsear CSV
    lineas = contenido_csv.splitlines()

    # Detectar delimitador
    delimitador = ','
    if ';' in lineas[0]:
        delimitador = ';'
    elif '\t' in lineas[0]:
        delimitador = '\t'

    # Leer con DictReader
    reader = csv.DictReader(lineas, delimiter=delimitador)

    # Convertir nombres de columnas a minúsculas
    reader.fieldnames = [campo.lower().strip() for campo in reader.fieldnames]

    # Verificar que existan las columnas necesarias
    if 'placa_codigo_interno' not in reader.fieldnames and 'placa_codigo' not in reader.fieldnames:
        print("❌ El CSV debe tener una columna 'placa_codigo_interno' o 'placa_codigo'")
        return {'actualizados': 0, 'errores': 0}

    if 'ubicacion' not in reader.fieldnames:
        print("❌ El CSV debe tener una columna 'ubicacion'")
        return {'actualizados': 0, 'errores': 0}

    # Contadores
    stats = {
        'actualizados': 0,
        'no_encontrados': 0,
        'sin_cambios': 0,
        'ignorados': 0,
        'errores': 0,
        'normalizaciones': []
    }

    for i, fila in enumerate(reader, start=2):
        try:
            # Obtener placa
            placa = fila.get('placa_codigo_interno', '').strip() or fila.get('placa_codigo', '').strip()
            ubicacion_original = fila.get('ubicacion', '').strip()

            if not placa:
                continue

            if not ubicacion_original:
                continue

            # Normalizar ubicación
            ubicacion_normalizada = normalizar_ubicacion(ubicacion_original)

            if not ubicacion_normalizada:
                stats['ignorados'] += 1
                continue

            # Registrar normalización si cambió
            if ubicacion_original != ubicacion_normalizada:
                stats['normalizaciones'].append(f"{ubicacion_original} → {ubicacion_normalizada}")

            # Buscar activo en BD
            activo = Activo.query.filter_by(placa_codigo_interno=placa).first()

            if not activo:
                print(f"   ⚠️  Placa '{placa}' NO encontrada en BD")
                stats['no_encontrados'] += 1
                continue

            # Verificar si la ubicación ya es la correcta
            if activo.ubicacion == ubicacion_normalizada:
                stats['sin_cambios'] += 1
                continue

            # Actualizar ubicación
            ubicacion_anterior = activo.ubicacion or '(vacío)'
            activo.ubicacion = ubicacion_normalizada

            print(f"   ✅ Placa '{placa}': {ubicacion_anterior} → {ubicacion_normalizada}")
            stats['actualizados'] += 1

        except Exception as e:
            print(f"   ❌ Error en línea {i}: {e}")
            stats['errores'] += 1

    return stats


def obtener_todas_ubicaciones_db():
    """Obtiene todas las ubicaciones únicas de la base de datos."""
    try:
        stmt = select(Activo.ubicacion).distinct().where(
            Activo.ubicacion.isnot(None),
            Activo.ubicacion != '',
            Activo.ubicacion != 'PENDIENTE'
        ).order_by(Activo.ubicacion)

        ubicaciones = db.session.execute(stmt).scalars().all()
        return list(ubicaciones)

    except Exception as e:
        print(f"❌ Error consultando ubicaciones: {e}")
        return []


def actualizar_ubicacion_selector_js(ubicaciones):
    """Actualiza el archivo ubicacion_selector.js con las nuevas ubicaciones."""

    archivo_js = Path(__file__).parent / 'app' / 'static' / 'js' / 'ubicacion_selector.js'

    if not archivo_js.exists():
        print(f"\n⚠️  Archivo {archivo_js.name} no encontrado")
        return

    try:
        # Leer el archivo actual
        with open(archivo_js, 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Construir el nuevo array de ubicaciones
        ubicaciones_js = ',\n    '.join([f"'{ub}'" for ub in sorted(set(ubicaciones))])

        nuevo_array = f"""const UBICACIONES_CLINICA = [
    {ubicaciones_js}
].sort(); // Ordenar alfabéticamente para facilitar búsqueda"""

        # Reemplazar el array existente usando regex
        patron = r'const UBICACIONES_CLINICA = \[[\s\S]*?\]\.sort\(\);'
        contenido_actualizado = re.sub(patron, nuevo_array, contenido)

        # Escribir el archivo actualizado
        with open(archivo_js, 'w', encoding='utf-8') as f:
            f.write(contenido_actualizado)

        print(f"\n✅ Archivo {archivo_js.name} actualizado con {len(ubicaciones)} ubicaciones")

    except Exception as e:
        print(f"\n❌ Error actualizando {archivo_js.name}: {e}")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal del script."""

    print("\n" + "=" * 80)
    print("ACTUALIZACIÓN DE UBICACIONES DESDE CSVs (MEJORADO)")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Determinar archivos CSV a procesar
    if len(sys.argv) > 1:
        archivos_csv = [sys.argv[1]]
    else:
        # Buscar CSVs en la carpeta uploads/
        uploads_dir = Path(__file__).parent / 'uploads'
        archivos_csv = list(uploads_dir.glob('*.csv'))
        archivos_csv = [str(f) for f in archivos_csv if 'plantilla' not in f.name.lower()]

    if not archivos_csv:
        print("❌ No se encontraron archivos CSV para procesar")
        print("\nUso:")
        print("    python actualizar_ubicaciones_mejorado.py [ruta_csv]")
        print("\nEjemplo:")
        print("    python actualizar_ubicaciones_mejorado.py uploads/activos.csv")
        sys.exit(1)

    print(f"📁 Archivos a procesar: {len(archivos_csv)}")
    for csv_file in archivos_csv:
        print(f"   • {Path(csv_file).name}")

    # Crear contexto de Flask
    app = create_app()

    with app.app_context():
        # Procesar todos los CSVs
        stats_totales = {
            'actualizados': 0,
            'no_encontrados': 0,
            'sin_cambios': 0,
            'ignorados': 0,
            'errores': 0,
            'normalizaciones': []
        }

        for csv_file in archivos_csv:
            stats = actualizar_ubicaciones_desde_csv(csv_file)
            stats_totales['actualizados'] += stats['actualizados']
            stats_totales['no_encontrados'] += stats['no_encontrados']
            stats_totales['sin_cambios'] += stats['sin_cambios']
            stats_totales['ignorados'] += stats['ignorados']
            stats_totales['errores'] += stats['errores']
            stats_totales['normalizaciones'].extend(stats['normalizaciones'])

        # Confirmar cambios
        try:
            db.session.commit()
            print("\n" + "=" * 70)
            print("✅ CAMBIOS GUARDADOS EN LA BASE DE DATOS")
            print("=" * 70)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar cambios: {e}")
            return

        # Mostrar normalizaciones aplicadas
        if stats_totales['normalizaciones']:
            normalizaciones_unicas = list(set(stats_totales['normalizaciones']))
            print(f"\n📝 Normalizaciones aplicadas ({len(normalizaciones_unicas)}):")
            for norm in sorted(normalizaciones_unicas):
                print(f"   • {norm}")

        # Obtener ubicaciones de la BD
        print("\n🔄 Obteniendo ubicaciones actualizadas de la base de datos...")
        ubicaciones_bd = obtener_todas_ubicaciones_db()

        # Actualizar ubicacion_selector.js
        print(f"🔄 Actualizando ubicacion_selector.js...")
        actualizar_ubicacion_selector_js(ubicaciones_bd)

        # Resumen final
        print("\n" + "=" * 80)
        print("RESUMEN FINAL")
        print("=" * 80)
        print(f"✅ Activos actualizados: {stats_totales['actualizados']}")
        print(f"➖ Activos sin cambios: {stats_totales['sin_cambios']}")
        print(f"⚠️  Activos no encontrados: {stats_totales['no_encontrados']}")
        print(f"🚫 Ubicaciones ignoradas: {stats_totales['ignorados']}")
        print(f"❌ Errores: {stats_totales['errores']}")
        print(f"📍 Ubicaciones únicas en BD: {len(ubicaciones_bd)}")
        print("=" * 80)

        print("\n🎯 Próximos pasos:")
        print("   1. Reiniciar Flask: python run.py")
        print("   2. Verificar selector de ubicaciones en la interfaz")
        print("   3. Probar filtro por ubicación en tabla de inventario")
        print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
