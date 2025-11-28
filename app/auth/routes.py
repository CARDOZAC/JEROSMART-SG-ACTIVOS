from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from sqlalchemy import select

from ..models import User  # Asumo que tu modelo de usuario se llama User y está en app/models.py
from .forms import LoginForm, ForgotPasswordForm, ResetPasswordForm
from ..extensions import db, login_manager
from ..decorators import login_required
from . import auth_bp  # Importar el Blueprint definido en __init__.py

@login_manager.user_loader
def load_user(user_id):
    """
    Función que Flask-Login usa para recargar el objeto de usuario desde el ID
    almacenado en la sesión. Es esencial para el funcionamiento de la sesión.
    """
    # user_id es una cadena, se debe convertir a entero para la consulta.
    return db.session.get(User, int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    # DEBUG: Log del intento de login
    if request.method == 'POST':
        current_app.logger.info(f"[LOGIN DEBUG] Intento de login recibido")
        current_app.logger.info(f"[LOGIN DEBUG] Email recibido: {form.email.data}")
        current_app.logger.info(f"[LOGIN DEBUG] Form válido: {form.validate_on_submit()}")
        if form.errors:
            current_app.logger.error(f"[LOGIN DEBUG] Errores del formulario: {form.errors}")

    if form.validate_on_submit():
        stmt = select(User).where(User.email == form.email.data)
        user = db.session.scalars(stmt).first()

        # DEBUG: Log del usuario encontrado
        current_app.logger.info(f"[LOGIN DEBUG] Usuario encontrado: {user is not None}")
        if user:
            current_app.logger.info(f"[LOGIN DEBUG] Email del usuario: {user.email}")
            password_ok = user.check_password(form.password.data)
            current_app.logger.info(f"[LOGIN DEBUG] Contraseña correcta: {password_ok}")

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            # Guardar el rol en la sesión para fácil acceso en templates
            session['rol'] = user.rol
            session['user_id'] = user.id
            session['email'] = user.email
            current_app.logger.info(f"[LOGIN] Usuario {user.email} con rol {user.rol} inició sesión")
            return redirect(url_for('main.index'))
        else:
            current_app.logger.warning(f"[LOGIN DEBUG] Login fallido para email: {form.email.data}")
            flash('Credenciales inválidas. Por favor, verifica tu correo y contraseña.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    # Limpiar la sesión
    session.pop('rol', None)
    session.pop('user_id', None)
    session.pop('email', None)
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """
    Ruta para manejar la solicitud de reseteo de contraseña.
    Muestra un formulario para que el usuario ingrese su email.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        stmt = select(User).where(User.email == form.email.data)
        user = db.session.scalars(stmt).first()
        if user:
            # --- LÓGICA PARA ENVIAR EMAIL ---
            # Aquí se implementaría la lógica de envío de correo.
            # Por ahora, simulamos el proceso para que la app no falle.
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Simulación de envío de correo
            print(f"--- SIMULACIÓN DE ENVÍO DE CORREO ---")
            print(f"Para: {user.email}")
            print(f"Asunto: Reseteo de Contraseña")
            print(f"Cuerpo: Haz clic en el siguiente enlace para resetear tu contraseña: {reset_url}")
            print(f"------------------------------------")

        # Por seguridad, siempre mostramos el mismo mensaje, exista o no el correo.
        flash('Si tu correo está registrado, recibirás un enlace para resetear tu contraseña en breve.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # El token es válido por 1 hora (3600 segundos)
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadTimeSignature):
        flash('El enlace de reseteo ha expirado o es inválido. Por favor, solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        stmt = select(User).where(User.email == email)
        user = db.session.scalars(stmt).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Tu contraseña ha sido actualizada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)