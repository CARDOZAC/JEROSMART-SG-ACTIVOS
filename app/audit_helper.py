"""
Helper para sistema de auditoría automática de movimientos.

Este módulo proporciona funciones para registrar automáticamente
todos los cambios realizados en movimientos para cumplimiento legal.
"""

from datetime import datetime
from flask import request
from flask_login import current_user
from app.extensions import db
from app.models import MovimientoHistorico


def registrar_auditoria_movimiento(movimiento, tipo_operacion, campo_modificado=None,
                                   valor_anterior=None, valor_nuevo=None, observaciones=None):
    """
    Registra un cambio en el historial de auditoría de un movimiento.

    Args:
        movimiento: Objeto Movimiento
        tipo_operacion: 'CREATE', 'UPDATE', 'DELETE', 'APROBACION', 'RECHAZO'
        campo_modificado: Nombre del campo que cambió
        valor_anterior: Valor antes del cambio
        valor_nuevo: Valor después del cambio
        observaciones: Notas adicionales del cambio
    """
    try:
        # Obtener IP del usuario
        ip_address = request.remote_addr if request else 'sistema'

        # Obtener User Agent
        user_agent = request.headers.get('User-Agent', '')[:500] if request else 'sistema'

        # Crear registro de auditoría
        audit_log = MovimientoHistorico(
            movimiento_id=movimiento.id,
            campo_modificado=campo_modificado or tipo_operacion,
            valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
            valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else None,
            usuario_id=current_user.id if current_user.is_authenticated else None,
            timestamp=datetime.now(),
            ip_address=ip_address[:45],  # Limitar longitud
            user_agent=user_agent,
            tipo_operacion=tipo_operacion,
            observaciones=observaciones
        )

        db.session.add(audit_log)
        # No hacemos commit aquí, se hará en la transacción principal

    except Exception as e:
        # Log del error pero no detener la operación principal
        from flask import current_app
        current_app.logger.error(f"Error registrando auditoría de movimiento: {e}")


def registrar_creacion_movimiento(movimiento, observaciones=None):
    """Registra la creación de un nuevo movimiento."""
    registrar_auditoria_movimiento(
        movimiento=movimiento,
        tipo_operacion='CREATE',
        campo_modificado='movimiento_creado',
        valor_nuevo=f"Tipo: {movimiento.tipo_movimiento}",
        observaciones=observaciones or f"Movimiento #{movimiento.id} creado"
    )


def registrar_aprobacion_movimiento(movimiento, aprobador, observaciones=None):
    """Registra la aprobación de un movimiento."""
    registrar_auditoria_movimiento(
        movimiento=movimiento,
        tipo_operacion='APROBACION',
        campo_modificado='estado_aprobacion',
        valor_anterior='Pendiente',
        valor_nuevo='Aprobado',
        observaciones=observaciones or f"Aprobado por {aprobador.email}"
    )


def registrar_rechazo_movimiento(movimiento, motivo, observaciones=None):
    """Registra el rechazo de un movimiento."""
    registrar_auditoria_movimiento(
        movimiento=movimiento,
        tipo_operacion='RECHAZO',
        campo_modificado='estado_aprobacion',
        valor_anterior='Pendiente',
        valor_nuevo='Rechazado',
        observaciones=observaciones or f"Rechazado. Motivo: {motivo}"
    )


def registrar_eliminacion_movimiento(movimiento_id, tipo_movimiento, usuario_email):
    """
    Registra la eliminación de un movimiento.
    Nota: Se debe llamar ANTES de eliminar el movimiento.
    """
    try:
        ip_address = request.remote_addr if request else 'sistema'
        user_agent = request.headers.get('User-Agent', '')[:500] if request else 'sistema'

        audit_log = MovimientoHistorico(
            movimiento_id=movimiento_id,
            campo_modificado='movimiento_eliminado',
            valor_anterior=f"Tipo: {tipo_movimiento}",
            valor_nuevo='ELIMINADO',
            usuario_id=current_user.id if current_user.is_authenticated else None,
            timestamp=datetime.now(),
            ip_address=ip_address[:45],
            user_agent=user_agent,
            tipo_operacion='DELETE',
            observaciones=f"Movimiento eliminado por {usuario_email}"
        )

        db.session.add(audit_log)
        db.session.flush()  # Flush para que se guarde antes de eliminar el movimiento

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error registrando eliminación de movimiento: {e}")


def obtener_historial_movimiento(movimiento_id, limit=50):
    """
    Obtiene el historial completo de auditoría de un movimiento.

    Args:
        movimiento_id: ID del movimiento
        limit: Número máximo de registros a devolver

    Returns:
        Lista de objetos MovimientoHistorico ordenados por fecha descendente
    """
    return MovimientoHistorico.query\
        .filter_by(movimiento_id=movimiento_id)\
        .order_by(MovimientoHistorico.timestamp.desc())\
        .limit(limit)\
        .all()
