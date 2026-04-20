from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    DateField,
    FloatField,
)
from wtforms.validators import DataRequired, Length, EqualTo, Optional, Regexp


class LoginForm(FlaskForm):
    """Formulario para inicio de sesión de usuarios."""

    username = StringField(
        "Usuario", validators=[DataRequired(), Length(min=4, max=80)]
    )
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar Sesión")


class RegisterForm(FlaskForm):
    """Formulario para registrar nuevos usuarios (solo admins)."""

    username = StringField(
        "Nombre de Usuario", validators=[DataRequired(), Length(min=4, max=80)]
    )
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar Contraseña",
        validators=[
            DataRequired(),
            EqualTo("password", message="Las contraseñas deben coincidir."),
        ],
    )
    rol = SelectField(
        "Rol",
        choices=[("user", "Usuario"), ("admin", "Administrador")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Registrar Usuario")


class ActivoForm(FlaskForm):
    """Formulario para crear o editar un activo."""

    nombre = StringField(
        "Nombre del Activo", validators=[DataRequired(), Length(max=150)]
    )
    placa_inventario = StringField(
        "Placa de Inventario", validators=[DataRequired(), Length(max=50)]
    )
    serial = StringField("Serial", validators=[Optional(), Length(max=100)])
    modelo = StringField("Modelo", validators=[Optional(), Length(max=100)])
    marca = StringField("Marca", validators=[Optional(), Length(max=100)])
    estado = SelectField(
        "Estado",
        choices=[
            ("Bueno", "Bueno"),
            ("Regular", "Regular"),
            ("Malo", "Malo"),
            ("En reparación", "En reparación"),
        ],
        validators=[DataRequired()],
    )
    fecha_compra = DateField(
        "Fecha de Compra", format="%Y-%m-%d", validators=[Optional()]
    )
    valor = FloatField("Valor de Compra", validators=[Optional()])
    funcionario_id = SelectField("Asignado a", coerce=int, validators=[Optional()])
    proveedor_id = SelectField("Proveedor", coerce=int, validators=[Optional()])
    submit = SubmitField("Guardar Activo")


class FuncionarioForm(FlaskForm):
    """Formulario para crear o editar un funcionario."""

    nombre_completo = StringField(
        "Nombre Completo", validators=[DataRequired(), Length(max=120)]
    )
    cedula = StringField(
        "Cédula",
        validators=[
            DataRequired(),
            Length(max=20),
            Regexp("^[0-9]+$", message="La cédula solo debe contener números."),
        ],
    )
    cargo = StringField("Cargo", validators=[Optional(), Length(max=80)])
    area = StringField("Área", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Guardar Funcionario")
