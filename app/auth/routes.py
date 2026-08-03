from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from sqlalchemy import select

from ..models import User  # Asumo que tu modelo de usuario se llama User y está en app/models.py
from .forms import LoginForm, ForgotPasswordForm, ResetPasswordForm
from ..extensions import db, login_manager
from ..decorators import login_required
from . import auth_bp  # Importar el Blueprint definido en __init__.py

# El user_loader de Flask-Login está definido una sola vez, en app/extensions.py.
# Aquí había una segunda definición que lo sobrescribía al importar este módulo.

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        stmt = select(User).where(User.email == form.email.data)
        user = db.session.scalars(stmt).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            # Guardar el rol en la sesión para fácil acceso en templates
            session['rol'] = user.rol
            session['user_id'] = user.id
            session['email'] = user.email
            session['cargo'] = user.cargo
            current_app.logger.info(f"[LOGIN] Usuario {user.email} con rol {user.rol} inició sesión")
            return redirect(url_for('main.index'))

        # No se distingue "usuario inexistente" de "contraseña incorrecta",
        # ni en el mensaje ni en el log: hacerlo permite enumerar cuentas
        # válidas. Se registra solo la IP para detectar intentos por fuerza
        # bruta.
        current_app.logger.warning(f"[LOGIN] Intento fallido desde {request.remote_addr}")
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
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            cuerpo = f"""
            <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; color: #1c1c1e;">
                <h2 style="font-size: 20px; margin-bottom: 8px;">Restablecer tu contraseña</h2>
                <p style="color: #6c6c70; font-size: 15px; line-height: 1.6;">
                    Recibimos una solicitud para restablecer la contraseña de tu cuenta.
                    Haz clic en el botón para elegir una nueva. El enlace caduca en 1 hora.
                </p>
                <p style="margin: 28px 0;">
                    <a href="{reset_url}"
                       style="background: #007AFF; color: #fff; text-decoration: none;
                              padding: 12px 22px; border-radius: 10px; font-weight: 600;
                              display: inline-block;">Restablecer contraseña</a>
                </p>
                <p style="color: #6c6c70; font-size: 13px; line-height: 1.6;">
                    Si no solicitaste este cambio, puedes ignorar este mensaje: tu contraseña
                    seguirá siendo la misma.
                </p>
                <p style="color: #8e8e93; font-size: 12px; word-break: break-all;">
                    Si el botón no funciona, copia esta dirección en tu navegador:<br>{reset_url}
                </p>
            </div>
            """

            # El envío no debe revelar al visitante si el correo existe ni
            # tumbar la petición si el SMTP está mal configurado.
            try:
                from ..email_service import enviar_email
                enviar_email(
                    to=user.email,
                    subject='Restablecer tu contraseña - SG Activos Fijos',
                    html=cuerpo
                )
                current_app.logger.info(f"[AUTH] Enlace de restablecimiento enviado a {user.email}")
            except Exception as e:
                current_app.logger.error(f"[AUTH] No se pudo enviar el correo de restablecimiento: {e}")

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