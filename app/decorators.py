from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify
from flask_login import current_user

def login_required(f):
    """
    Asegura que el usuario haya iniciado sesión.

    Las rutas de API responden 401 con JSON en lugar de redirigir: al devolver
    el HTML del login, el `fetch()` del cliente fallaba con
    "Unexpected token '<' ... is not valid JSON" y el wizard mostraba un error
    genérico en vez de avisar de que la sesión expiró.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or '/api/' in request.path:
                return jsonify({
                    'error': 'Sesión expirada',
                    'mensaje': 'Tu sesión expiró. Vuelve a iniciar sesión.',
                    'login_url': url_for('auth.login')
                }), 401
            flash('Debes iniciar sesión para ver esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Asegura que el usuario que ha iniciado sesión tenga un rol específico.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.rol != role_name:
                flash('No tienes permiso para realizar esta acción.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator