from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from ..models import User  # Asumo que tu modelo de usuario se llama User y está en app/models.py
from .forms import LoginForm, ForgotPasswordForm, ResetPasswordForm
from ..extensions import db, login_manager

# El Blueprint se define sin prefijo, ya que se establece al registrarlo en app/__init__.py
auth_bp = Blueprint('auth', __name__, template_folder='templates')

@login_manager.user_loader
def load_user(user_id):
    """
    Función que Flask-Login usa para recargar el objeto de usuario desde el ID
    almacenado en la sesión. Es esencial para el funcionamiento de la sesión.
    """
    # user_id es una cadena, se debe convertir a entero para la consulta.
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.index'))
        else:
            flash('Credenciales inválidas. Por favor, verifica tu correo y contraseña.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
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
        user = User.query.filter_by(email=form.email.data).first()
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

    return render_template('forgot_password.html', form=form)


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
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Tu contraseña ha sido actualizada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form, token=token)