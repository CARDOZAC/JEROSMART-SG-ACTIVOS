"""
Context Builders para el Módulo Biomédico.

Este módulo sigue el principio de "Separación de Intereses". Su única
responsabilidad es tomar los modelos de la base de datos y transformarlos
en un diccionario (contexto) perfectamente estructurado para que las plantillas
Jinja2 (especialmente las de PDFs) puedan renderizarlos sin lógica compleja.

Estilo "Petr": Las plantillas deben ser 'tontas'. La inteligencia pertenece aquí.
"""

import os
import base64
from flask import current_app
from datetime import datetime


def get_file_base64(ruta_relativa):
    """Función helper para convertir un archivo a base64 para el PDF."""
    if not ruta_relativa:
        return None
    try:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], ruta_relativa)
        with open(full_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except (FileNotFoundError, TypeError):
        current_app.logger.warning(f"Archivo no encontrado para PDF: {ruta_relativa}")
        return None


def build_hoja_vida_pdf_context(hoja_vida):
    """
    Construye el contexto completo para el PDF de la Hoja de Vida.
    Toma un objeto HojaVidaBiomedico y devuelve un diccionario listo para la plantilla.
    """
    import hashlib

    activo = hoja_vida.activo

    # Generar checksum único para el documento (seguridad y trazabilidad)
    timestamp = datetime.now().isoformat()
    data_string = f"{activo.id}-{activo.placa_codigo_interno}-{timestamp}"
    checksum = hashlib.sha256(data_string.encode()).hexdigest()

    # Procesar mantenimientos
    mantenimientos_procesados = []
    # Ordenar por fecha descendente
    if hoja_vida.mantenimientos:
        mantenimientos_sorted = sorted(
            hoja_vida.mantenimientos, key=lambda m: m.fecha, reverse=True
        )

        for mant in mantenimientos_sorted:
            mantenimientos_procesados.append(
                {
                    "fecha": mant.fecha,
                    "tipo": mant.tipo_mtto,
                    "descripcion": mant.actividad_observaciones,
                    "tecnico_responsable": mant.firma_responsable or "N/A",
                }
            )

    # Procesar documentos adjuntos
    documentos_adjuntos = []
    if hoja_vida.documentos:
        for doc in hoja_vida.documentos:
            documentos_adjuntos.append(
                {
                    "tipo_documento": doc.tipo_documento.replace("_", " ").title(),
                    "nombre_archivo_original": doc.nombre_archivo_original,
                    "ruta_archivo": doc.ruta_archivo,
                    "tamano_bytes": doc.tamano_bytes or 0,
                    "fecha_carga": doc.fecha_carga,
                }
            )

    context = {
        "hoja_vida": hoja_vida,  # Nombre correcto para el template
        "activo": activo,
        "mantenimientos": mantenimientos_procesados,
        "documentos": documentos_adjuntos,
        "fecha_generacion": datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        ),  # Formato legible
        "checksum": checksum,  # Hash de seguridad
    }
    return context


def build_mantenimiento_pdf_context(mantenimiento):
    """
    Construye el contexto completo para el PDF de Mantenimiento.
    Toma un objeto Mantenimiento y devuelve un diccionario listo para la plantilla.

    Siguiendo el principio de James Gosling: "Simplicidad, modularidad y robustez"
    """
    import hashlib
    import json

    activo = mantenimiento.activo

    # Generar checksum único para trazabilidad
    timestamp = datetime.now().isoformat()
    data_string = f"{mantenimiento.id}-{activo.placa_codigo_interno}-{timestamp}"
    checksum = hashlib.sha256(data_string.encode()).hexdigest()

    # Parsear reporte técnico desde JSON
    reporte_tecnico = {}
    if mantenimiento.atributos_reporte_json:
        try:
            reporte_tecnico = json.loads(mantenimiento.atributos_reporte_json)
        except (json.JSONDecodeError, TypeError):
            current_app.logger.warning(
                f"Error al parsear JSON del reporte técnico del mantenimiento {mantenimiento.id}"
            )
            reporte_tecnico = {}

    # Agregar datos adicionales al reporte técnico
    reporte_tecnico["tecnico_responsable"] = reporte_tecnico.get(
        "tecnico_responsable", "N/A"
    )

    # Procesar accesorios/repuestos
    accesorios_procesados = []
    # Nota: Los accesorios se guardarían en una tabla relacionada o en JSON
    # Por ahora, intentamos extraerlos del JSON si existen
    accesorios_json = reporte_tecnico.get("accesorios", [])
    if isinstance(accesorios_json, str):
        try:
            accesorios_json = json.loads(accesorios_json)
        except json.JSONDecodeError:
            accesorios_json = []

    for acc in accesorios_json:
        if isinstance(acc, dict):
            accesorios_procesados.append(
                {
                    "nombre": acc.get("nombre", "N/A"),
                    "cantidad": acc.get("cantidad", 1),
                    "referencia": acc.get("referencia", "-"),
                }
            )

    # Procesar firmas (convertidas a base64 si existen)
    firma_tecnico = reporte_tecnico.get("firma_tecnico")
    firma_responsable = reporte_tecnico.get("firma_responsable")

    # Limpiar las firmas de data URL prefix si es necesario
    if firma_tecnico and firma_tecnico.startswith("data:image"):
        firma_tecnico = firma_tecnico  # Ya está en formato data URL, listo para usar

    if firma_responsable and firma_responsable.startswith("data:image"):
        firma_responsable = firma_responsable

    context = {
        "mantenimiento": mantenimiento,
        "activo": activo,
        "reporte_tecnico": type(
            "ReporteTecnico", (), reporte_tecnico
        )(),  # Convertir dict a objeto para acceso con punto
        "accesorios": accesorios_procesados,
        "firma_tecnico": firma_tecnico,
        "firma_responsable": firma_responsable,
        "fecha_generacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "checksum": checksum,
    }

    return context
