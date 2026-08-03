"""
Sistema de caché para PDFs generados.

Reduce la carga del servidor al cachear PDFs ya generados.
Implementa estrategias de invalidación automática cuando se modifica un movimiento.
"""

import os
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import current_app


class PDFCacheManager:
    """
    Gestor de caché de PDFs con invalidación inteligente.

    Estrategia:
    - Los PDFs se guardan en uploads/pdf_cache/
    - El nombre del archivo incluye un hash del movimiento
    - Se invalida automáticamente si el movimiento cambia
    - Limpieza automática de archivos antiguos (>30 días)
    """

    def __init__(self, cache_dir=None):
        """
        Inicializa el gestor de caché.

        Args:
            cache_dir: Directorio donde guardar los PDFs (opcional)
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            base_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
            self.cache_dir = base_dir / 'pdf_cache'

        # Crear directorio si no existe
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Configuración
        self.max_age_days = 30  # Días antes de considerar un PDF obsoleto
        self.enabled = current_app.config.get('PDF_CACHE_ENABLED', True)

    def _generate_cache_key(self, movimiento):
        """
        Genera una clave única para el movimiento.

        La clave incluye:
        - ID del movimiento
        - Fecha de última modificación
        - Cantidad de activos
        - Estado de aprobación

        Args:
            movimiento: Objeto Movimiento

        Returns:
            str: Hash SHA256 del movimiento
        """
        # Crear cadena única con datos relevantes
        cache_data = {
            'id': movimiento.id,
            'tipo': movimiento.tipo_movimiento,
            'fecha': movimiento.fecha.isoformat() if movimiento.fecha else None,
            'estado_aprobacion': movimiento.estado_aprobacion,
            'num_activos': len(movimiento.activos) if movimiento.activos else 0,
            'observaciones_hash': hashlib.md5(
                (movimiento.observaciones_generales or '').encode()
            ).hexdigest()
        }

        # Incluir hash de firmas si existen
        if movimiento.firmas:
            firmas_hashes = [
                hashlib.md5(f.firma_base64.encode()).hexdigest()
                for f in movimiento.firmas if f.firma_base64
            ]
            cache_data['firmas'] = sorted(firmas_hashes)

        # Generar hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _get_cache_path(self, movimiento):
        """
        Obtiene la ruta del archivo caché para un movimiento.

        Args:
            movimiento: Objeto Movimiento

        Returns:
            Path: Ruta completa al archivo PDF en caché
        """
        cache_key = self._generate_cache_key(movimiento)
        filename = f"mov_{movimiento.id}_{cache_key[:12]}.pdf"
        return self.cache_dir / filename

    def get_cached_pdf(self, movimiento):
        """
        Obtiene un PDF desde el caché si existe y es válido.

        Args:
            movimiento: Objeto Movimiento

        Returns:
            bytes: Contenido del PDF o None si no existe en caché
        """
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(movimiento)

        # Verificar si el archivo existe
        if not cache_path.exists():
            current_app.logger.debug(f"PDF cache MISS: {cache_path.name}")
            return None

        # Verificar antigüedad del archivo
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if file_age > timedelta(days=self.max_age_days):
            current_app.logger.info(f"PDF cache EXPIRED (age: {file_age.days} days): {cache_path.name}")
            # Eliminar archivo obsoleto
            try:
                cache_path.unlink()
            except Exception as e:
                current_app.logger.error(f"Error eliminando PDF obsoleto: {e}")
            return None

        # Leer y retornar contenido
        try:
            with open(cache_path, 'rb') as f:
                pdf_content = f.read()

            current_app.logger.debug(f"PDF cache HIT: {cache_path.name} ({len(pdf_content)} bytes)")
            return pdf_content

        except Exception as e:
            current_app.logger.error(f"Error leyendo PDF desde caché: {e}")
            return None

    def save_pdf_to_cache(self, movimiento, pdf_content):
        """
        Guarda un PDF generado en el caché.

        Args:
            movimiento: Objeto Movimiento
            pdf_content: Contenido del PDF (bytes)

        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        if not self.enabled:
            return False

        cache_path = self._get_cache_path(movimiento)

        try:
            # Guardar PDF
            with open(cache_path, 'wb') as f:
                f.write(pdf_content)

            current_app.logger.info(
                f"PDF guardado en caché: {cache_path.name} "
                f"({len(pdf_content)} bytes)"
            )

            return True

        except Exception as e:
            current_app.logger.error(f"Error guardando PDF en caché: {e}", exc_info=True)
            return False

    def invalidate_cache(self, movimiento_id):
        """
        Invalida (elimina) todos los PDFs en caché para un movimiento.

        Esto se debe llamar cuando:
        - Se modifica el movimiento
        - Se agregan/eliminan activos
        - Se agregan/eliminan firmas

        Args:
            movimiento_id: ID del movimiento

        Returns:
            int: Cantidad de archivos eliminados
        """
        pattern = f"mov_{movimiento_id}_*.pdf"
        deleted_count = 0

        try:
            for pdf_file in self.cache_dir.glob(pattern):
                pdf_file.unlink()
                deleted_count += 1
                current_app.logger.info(f"PDF cache invalidado: {pdf_file.name}")

        except Exception as e:
            current_app.logger.error(f"Error invalidando caché: {e}")

        return deleted_count

    def cleanup_old_files(self, days=None):
        """
        Limpia archivos de caché más antiguos que X días.

        Args:
            days: Días de antigüedad (por defecto usa self.max_age_days)

        Returns:
            int: Cantidad de archivos eliminados
        """
        days = days or self.max_age_days
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        try:
            for pdf_file in self.cache_dir.glob("mov_*.pdf"):
                file_time = datetime.fromtimestamp(pdf_file.stat().st_mtime)

                if file_time < cutoff_time:
                    file_age_days = (datetime.now() - file_time).days
                    pdf_file.unlink()
                    deleted_count += 1
                    current_app.logger.info(
                        f"PDF obsoleto eliminado: {pdf_file.name} (age: {file_age_days} days)"
                    )

            if deleted_count > 0:
                current_app.logger.info(f"Limpieza de caché completada: {deleted_count} archivos eliminados")

        except Exception as e:
            current_app.logger.error(f"Error en limpieza de caché: {e}")

        return deleted_count

    def get_cache_stats(self):
        """
        Obtiene estadísticas del caché.

        Returns:
            dict: Estadísticas del caché
        """
        pdf_files = list(self.cache_dir.glob("mov_*.pdf"))

        total_size = sum(f.stat().st_size for f in pdf_files)
        avg_size = total_size / len(pdf_files) if pdf_files else 0

        # Calcular edad promedio
        if pdf_files:
            total_age = sum(
                (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds()
                for f in pdf_files
            )
            avg_age_hours = (total_age / len(pdf_files)) / 3600
        else:
            avg_age_hours = 0

        return {
            'total_files': len(pdf_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'avg_size_kb': round(avg_size / 1024, 2),
            'avg_age_hours': round(avg_age_hours, 2),
            'cache_dir': str(self.cache_dir),
            'enabled': self.enabled
        }

    def clear_all_cache(self):
        """
        Elimina TODOS los PDFs del caché.
        ADVERTENCIA: Usar solo para mantenimiento.

        Returns:
            int: Cantidad de archivos eliminados
        """
        deleted_count = 0

        try:
            for pdf_file in self.cache_dir.glob("mov_*.pdf"):
                pdf_file.unlink()
                deleted_count += 1

            current_app.logger.warning(
                f"CACHÉ LIMPIADO COMPLETAMENTE: {deleted_count} archivos eliminados"
            )

        except Exception as e:
            current_app.logger.error(f"Error limpiando caché: {e}")

        return deleted_count


# ==============================================================================
# FUNCIONES HELPER
# ==============================================================================

def get_pdf_from_cache_or_generate(movimiento, generator_func):
    """
    Obtiene un PDF desde caché o lo genera si no existe.

    Args:
        movimiento: Objeto Movimiento
        generator_func: Función que genera el PDF (debe retornar bytes)

    Returns:
        bytes: Contenido del PDF

    Ejemplo:
        pdf_content = get_pdf_from_cache_or_generate(
            movimiento,
            lambda: generar_acta_entrega_pdf(movimiento)
        )
    """
    cache_manager = PDFCacheManager()

    # Intentar obtener desde caché
    cached_pdf = cache_manager.get_cached_pdf(movimiento)
    if cached_pdf:
        return cached_pdf

    # Generar nuevo PDF
    try:
        pdf_content = generator_func()

        # Guardar en caché
        cache_manager.save_pdf_to_cache(movimiento, pdf_content)

        return pdf_content

    except Exception as e:
        current_app.logger.error(f"Error generando PDF: {e}", exc_info=True)
        raise


def invalidate_movimiento_cache(movimiento_id):
    """
    Invalida el caché de un movimiento específico.
    Se debe llamar después de modificar un movimiento.

    Args:
        movimiento_id: ID del movimiento

    Ejemplo:
        # Después de agregar una firma
        invalidate_movimiento_cache(movimiento.id)
    """
    cache_manager = PDFCacheManager()
    return cache_manager.invalidate_cache(movimiento_id)
