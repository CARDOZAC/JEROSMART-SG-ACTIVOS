from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    """Formulario para el inicio de sesión de usuarios."""

    email = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio."),
            Email(message="Ingrese un correo válido."),
        ],
    )
    password = PasswordField(
        "Contraseña", validators=[DataRequired(message="La contraseña es obligatoria.")]
    )
    remember_me = BooleanField("Recordarme")
    submit = SubmitField("Iniciar Sesión")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    submit = SubmitField("Enviar Enlace de Reseteo")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Nueva Contraseña",
        validators=[
            DataRequired(),
            Length(min=6, message="La contraseña debe tener al menos 6 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar Nueva Contraseña",
        validators=[
            DataRequired(),
            EqualTo("password", message="Las contraseñas deben coincidir."),
        ],
    )
    submit = SubmitField("Restablecer Contraseña")
