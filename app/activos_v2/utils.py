# ==============================================================================
# UTILIDADES DEL MÓDULO ACTIVOS V2
# ==============================================================================

import os
from werkzeug.utils import secure_filename
from datetime import datetime


# ==============================================================================
# CONFIGURACIÓN DE UPLOADS
# ==============================================================================
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename):
    """
    Verifica si el archivo tiene una extensión permitida.

    Args:
        filename (str): Nombre del archivo

    Returns:
        bool: True si la extensión es válida
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_path(tipo, entity_id):
    """
    Genera la ruta de upload para un tipo de entidad.

    Args:
        tipo (str): Tipo de entidad ('mantenimientos', 'activos', etc.)
        entity_id (int): ID de la entidad

    Returns:
        str: Ruta relativa al directorio uploads
    """
    return os.path.join("uploads", tipo, str(entity_id))


def save_uploaded_file(file, upload_folder):
    """
    Guarda un archivo subido en el servidor.

    Args:
        file: Objeto FileStorage de Flask
        upload_folder (str): Carpeta destino

    Returns:
        tuple: (ruta_completa, nombre_seguro, tamaño_bytes)
    """
    if file and allowed_file(file.filename):
        # Generar nombre seguro con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = secure_filename(file.filename)
        name, ext = os.path.splitext(original_name)
        filename = f"{name}_{timestamp}{ext}"

        # Crear carpeta si no existe
        os.makedirs(upload_folder, exist_ok=True)

        # Guardar archivo
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Obtener tamaño
        file_size = os.path.getsize(filepath)

        return filepath, filename, file_size

    return None, None, None


def format_currency(value):
    """
    Formatea un valor numérico como moneda colombiana.

    Args:
        value (float/Decimal): Valor a formatear

    Returns:
        str: Valor formateado (ej: $1.234.567,89)
    """
    if value is None:
        return "$0"

    try:
        # Convertir a float
        value = float(value)

        # Formatear con separadores
        formatted = f"${value:,.2f}"

        # Reemplazar separadores al estilo colombiano
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

        return formatted
    except (ValueError, TypeError):
        return "$0"


def format_file_size(bytes_size):
    """
    Formatea el tamaño de un archivo en formato legible.

    Args:
        bytes_size (int): Tamaño en bytes

    Returns:
        str: Tamaño formateado (ej: 2.5 MB)
    """
    if bytes_size is None or bytes_size == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(bytes_size)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def get_estado_badge_class(estado):
    """
    Retorna la clase CSS para el badge del estado.

    Args:
        estado (str): Estado del activo

    Returns:
        str: Clase CSS del badge
    """
    estado_classes = {
        "Operativo": "badge-success",
        "En reparación": "badge-warning",
        "En mantenimiento": "badge-info",
        "Dado de baja": "badge-danger",
        "Disponible": "badge-primary",
    }

    return estado_classes.get(estado, "badge-secondary")


def get_tipo_mantenimiento_badge_class(tipo):
    """
    Retorna la clase CSS para el badge del tipo de mantenimiento.

    Args:
        tipo (str): Tipo de mantenimiento

    Returns:
        str: Clase CSS del badge
    """
    tipo_classes = {
        "Preventivo": "badge-info",
        "Correctivo": "badge-warning",
        "Calibración": "badge-primary",
        "Inspección": "badge-secondary",
        "Actualización": "badge-success",
    }

    return tipo_classes.get(tipo, "badge-secondary")
