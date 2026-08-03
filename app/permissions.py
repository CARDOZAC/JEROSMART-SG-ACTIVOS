"""
Sistema de permisos basado en roles (RBAC - Role-Based Access Control).

Roles disponibles:
- Admin: Acceso completo al sistema
- Supervisor: Puede aprobar movimientos, ver reportes, eliminar firmas
- Operador: Puede crear y editar movimientos, agregar firmas
- Auditor: Solo lectura, acceso a reportes y auditoría
- User: Acceso básico de solo lectura

Uso:
    from app.permissions import require_permission, puede_editar_movimiento

    @require_permission('eliminar_movimiento')
    def eliminar_movimiento(movimiento_id):
        ...
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, jsonify, request
from flask_login import current_user


# ==============================================================================
# DEFINICIÓN DE PERMISOS POR ROL
# ==============================================================================

PERMISOS_POR_ROL = {
    'Admin': {
        'crear_movimiento',
        'editar_movimiento',
        'eliminar_movimiento',
        'ver_movimiento',
        'aprobar_movimiento',
        'rechazar_movimiento',
        'firmar_movimiento',
        'eliminar_firma',
        'ver_reportes',
        'exportar_datos',
        'gestionar_usuarios',
        'ver_auditoria',
        'eliminar_activos',
        'configurar_sistema'
    },
    'Supervisor': {
        'crear_movimiento',
        'editar_movimiento',
        'ver_movimiento',
        'aprobar_movimiento',
        'rechazar_movimiento',
        'firmar_movimiento',
        'eliminar_firma',
        'ver_reportes',
        'exportar_datos',
        'ver_auditoria'
    },
    'Operador': {
        'crear_movimiento',
        'editar_movimiento',
        'ver_movimiento',
        'firmar_movimiento',
        'exportar_datos'  # Operadores pueden exportar sus propios movimientos
    },
    'Auditor': {
        'ver_movimiento',
        'ver_reportes',
        'exportar_datos',  # Auditores necesitan exportar para análisis
        'ver_auditoria'
    },
    'User': {
        'ver_movimiento',
        'ver_reportes',
        'exportar_datos'  # Todos pueden exportar datos básicos
    }
}


# ==============================================================================
# FUNCIONES DE VERIFICACIÓN DE PERMISOS
# ==============================================================================

def tiene_permiso(permiso):
    """
    Verifica si el usuario actual tiene un permiso específico.

    Args:
        permiso (str): Nombre del permiso a verificar

    Returns:
        bool: True si tiene el permiso, False en caso contrario

    Ejemplo:
        if tiene_permiso('eliminar_movimiento'):
            # Permitir acción
    """
    if not current_user.is_authenticated:
        return False

    rol_usuario = getattr(current_user, 'rol', 'User')
    permisos_rol = PERMISOS_POR_ROL.get(rol_usuario, set())

    return permiso in permisos_rol


def tiene_cualquier_permiso(*permisos):
    """
    Verifica si el usuario tiene al menos uno de los permisos especificados.

    Args:
        *permisos: Lista de permisos a verificar

    Returns:
        bool: True si tiene al menos uno, False en caso contrario
    """
    return any(tiene_permiso(p) for p in permisos)


def tiene_todos_permisos(*permisos):
    """
    Verifica si el usuario tiene todos los permisos especificados.

    Args:
        *permisos: Lista de permisos a verificar

    Returns:
        bool: True si tiene todos, False en caso contrario
    """
    return all(tiene_permiso(p) for p in permisos)


# ==============================================================================
# DECORADORES DE PERMISOS
# ==============================================================================

def require_permission(permiso, redirigir_a='movimientos.ver_movimientos'):
    """
    Decorador que requiere que el usuario tenga un permiso específico.

    Args:
        permiso (str): Nombre del permiso requerido
        redirigir_a (str): Ruta a la que redirigir si no tiene permiso (para HTML)

    Uso:
        @require_permission('eliminar_movimiento')
        def eliminar_movimiento(movimiento_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Autenticación requerida'}), 401
                flash('Debe iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login'))

            if not tiene_permiso(permiso):
                # Log de intento de acceso no autorizado
                from flask import current_app
                current_app.logger.warning(
                    f"[SEGURIDAD] Acceso denegado: "
                    f"usuario={current_user.email} | "
                    f"rol={current_user.rol} | "
                    f"permiso_requerido={permiso} | "
                    f"ip={request.remote_addr} | "
                    f"ruta={request.path}"
                )

                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'No tiene permisos para realizar esta acción'
                    }), 403

                flash('No tiene permisos para realizar esta acción.', 'danger')
                return redirect(url_for(redirigir_a))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(*permisos, redirigir_a='movimientos.ver_movimientos'):
    """
    Decorador que requiere que el usuario tenga al menos uno de los permisos.

    Args:
        *permisos: Lista de permisos (basta con tener uno)
        redirigir_a (str): Ruta a la que redirigir si no tiene permiso

    Uso:
        @require_any_permission('editar_movimiento', 'eliminar_movimiento')
        def modificar_movimiento(movimiento_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Autenticación requerida'}), 401
                flash('Debe iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login'))

            if not tiene_cualquier_permiso(*permisos):
                from flask import current_app
                current_app.logger.warning(
                    f"[SEGURIDAD] Acceso denegado: "
                    f"usuario={current_user.email} | "
                    f"rol={current_user.rol} | "
                    f"permisos_requeridos={permisos} | "
                    f"ip={request.remote_addr}"
                )

                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'No tiene permisos para realizar esta acción'
                    }), 403

                flash('No tiene permisos para realizar esta acción.', 'danger')
                return redirect(url_for(redirigir_a))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorador que requiere que el usuario sea Admin.
    Atajo para @require_permission con verificación de rol directo.

    Uso:
        @admin_required
        def configurar_sistema():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        if current_user.rol != 'Admin':
            from flask import current_app
            current_app.logger.warning(
                f"[SEGURIDAD] Acceso Admin denegado: "
                f"usuario={current_user.email} | "
                f"rol={current_user.rol} | "
                f"ip={request.remote_addr}"
            )

            flash('Solo los administradores pueden acceder a esta página.', 'danger')
            return redirect(url_for('movimientos.ver_movimientos'))

        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# FUNCIONES DE NEGOCIO
# ==============================================================================

def puede_editar_movimiento(movimiento):
    """
    Determina si el usuario actual puede editar un movimiento específico.

    Reglas:
    - Admin: Puede editar cualquier movimiento
    - Supervisor: Puede editar movimientos propios o de su área
    - Operador: Solo puede editar sus propios movimientos si están en borrador
    - Otros: No pueden editar

    Args:
        movimiento: Objeto Movimiento a verificar

    Returns:
        bool: True si puede editar, False en caso contrario
    """
    if not current_user.is_authenticated:
        return False

    # Admin puede editar todo
    if current_user.rol == 'Admin':
        return True

    # Supervisor puede editar movimientos propios o de su área
    if current_user.rol == 'Supervisor':
        if movimiento.usuario_id == current_user.id:
            return True
        # Aquí podríamos agregar lógica de área/departamento
        return True  # Por ahora, supervisor puede editar todo

    # Operador solo puede editar sus propios movimientos en borrador
    if current_user.rol == 'Operador':
        return (
            movimiento.usuario_id == current_user.id and
            movimiento.estado_completitud == 'borrador'
        )

    return False


def puede_eliminar_movimiento(movimiento):
    """
    Determina si el usuario actual puede eliminar un movimiento.

    Reglas:
    - Admin: Puede eliminar cualquier movimiento
    - Supervisor: Puede eliminar movimientos en borrador
    - Operador: Puede eliminar sus propios borradores
    - Otros: No pueden eliminar

    Args:
        movimiento: Objeto Movimiento a verificar

    Returns:
        bool: True si puede eliminar, False en caso contrario
    """
    if not current_user.is_authenticated:
        return False

    # Admin puede eliminar todo
    if current_user.rol == 'Admin':
        return True

    # Supervisor puede eliminar borradores
    if current_user.rol == 'Supervisor':
        return movimiento.estado_completitud == 'borrador'

    # Operador solo puede eliminar sus propios borradores
    if current_user.rol == 'Operador':
        return (
            movimiento.usuario_id == current_user.id and
            movimiento.estado_completitud == 'borrador'
        )

    return False


def puede_aprobar_movimiento(movimiento):
    """
    Determina si el usuario puede aprobar un movimiento.

    Reglas:
    - No puede aprobar sus propios movimientos
    - Debe tener el permiso 'aprobar_movimiento'
    - El movimiento debe estar pendiente de aprobación

    Args:
        movimiento: Objeto Movimiento a verificar

    Returns:
        bool: True si puede aprobar, False en caso contrario
    """
    if not current_user.is_authenticated:
        return False

    # No puede aprobar sus propios movimientos
    if movimiento.usuario_id == current_user.id:
        return False

    # Debe estar pendiente
    if movimiento.estado_aprobacion != 'Pendiente':
        return False

    # Debe tener el permiso
    return tiene_permiso('aprobar_movimiento')


# ==============================================================================
# CONTEXTO PARA TEMPLATES (Jinja2)
# ==============================================================================

def registrar_funciones_contexto(app):
    """
    Registra las funciones de permisos en el contexto de Jinja2.
    Esto permite usar las funciones directamente en las plantillas HTML.

    Uso en app/__init__.py:
        from app.permissions import registrar_funciones_contexto
        registrar_funciones_contexto(app)

    Uso en templates:
        {% if tiene_permiso('eliminar_movimiento') %}
            <button>Eliminar</button>
        {% endif %}
    """
    @app.context_processor
    def inject_permissions():
        return {
            'tiene_permiso': tiene_permiso,
            'tiene_cualquier_permiso': tiene_cualquier_permiso,
            'tiene_todos_permisos': tiene_todos_permisos,
            'puede_editar_movimiento': puede_editar_movimiento,
            'puede_eliminar_movimiento': puede_eliminar_movimiento,
            'puede_aprobar_movimiento': puede_aprobar_movimiento,
        }
