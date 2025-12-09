from functools import wraps
from flask import session, flash, redirect, url_for
from flask_login import current_user


def login_required(f):
    """
    Asegura que el usuario haya iniciado sesión.
    Redirige a la página de login si no lo está.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para ver esta página.", "warning")
            return redirect(url_for("auth.login"))
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
                flash("No tienes permiso para realizar esta acción.", "danger")
                return redirect(url_for("main.index"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
