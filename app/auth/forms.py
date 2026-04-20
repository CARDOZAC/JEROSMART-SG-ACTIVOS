from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    remember_me = BooleanField("Recordarme")
    submit = SubmitField("Iniciar Sesión")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    submit = SubmitField("Enviar Enlace de Reseteo")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Nueva Contraseña", validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirmar Contraseña",
        validators=[
            DataRequired(),
            EqualTo("password", message="Las contraseñas deben coincidir."),
        ],
    )
    submit = SubmitField("Actualizar Contraseña")
