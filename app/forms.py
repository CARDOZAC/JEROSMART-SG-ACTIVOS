from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    DateField,
    FloatField,
    TextAreaField,
    IntegerField,
    BooleanField,
    FileField,
)
from wtforms.validators import DataRequired, Length, EqualTo, Optional, Regexp, Email


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


# ===========================
# Formulario Hoja de Vida Biomédico
# ===========================
class HojaVidaBiomedicoForm(FlaskForm):
    # ---------- Datos Generales ----------
    equipo = StringField("Equipo", validators=[DataRequired(), Length(max=150)])
    permiso_comercializacion = StringField(
        "Permiso de Comercialización", validators=[Optional()]
    )
    marca = StringField("Marca", validators=[Optional()])
    modelo = StringField("Modelo", validators=[Optional()])
    serie = StringField("Serie", validators=[Optional()])
    inv_activo = StringField("Inventario Activo", validators=[Optional()])
    servicio = StringField("Servicio", validators=[Optional()])
    ubicacion = StringField("Ubicación", validators=[Optional()])

    n_factura = StringField("No. Factura", validators=[Optional()])
    n_orden_compra = StringField("No. Orden de Compra", validators=[Optional()])
    fecha_fabricacion = DateField(
        "Fecha de Fabricación", format="%Y-%m-%d", validators=[Optional()]
    )
    fecha_instalacion = DateField(
        "Fecha de Instalación", format="%Y-%m-%d", validators=[Optional()]
    )

    # ---------- Datos de Adquisición ----------
    distribuidor = StringField("Distribuidor", validators=[Optional()])
    forma_adquisicion = StringField("Forma de Adquisición", validators=[Optional()])
    telefono = StringField("Teléfono", validators=[Optional()])
    correo_electronico = StringField(
        "Correo Electrónico", validators=[Optional(), Email()]
    )
    fecha_ingreso = DateField(
        "Fecha de Ingreso", format="%Y-%m-%d", validators=[Optional()]
    )
    vencimiento_garantia = DateField(
        "Vencimiento Garantía", format="%Y-%m-%d", validators=[Optional()]
    )
    costo = FloatField("Costo", validators=[Optional()])
    vida_util_anios = IntegerField("Vida Útil (años)", validators=[Optional()])

    # ---------- Datos Técnicos ----------
    voltaje = StringField("Voltaje", validators=[Optional()])
    frecuencia = StringField("Frecuencia", validators=[Optional()])
    dimensiones = StringField("Dimensiones", validators=[Optional()])
    corriente = StringField("Corriente", validators=[Optional()])
    potencia = StringField("Potencia", validators=[Optional()])
    peso = StringField("Peso", validators=[Optional()])
    equipo_fijo_movil = SelectField(
        "Fijo/Móvil",
        choices=[("fijo", "Fijo"), ("movil", "Móvil")],
        validators=[Optional()],
    )
    humedad_relativa = StringField("Humedad Relativa", validators=[Optional()])
    temperatura_trabajo = StringField("Temperatura de Trabajo", validators=[Optional()])

    manual_usuario = BooleanField("Manual de Usuario")
    manual_servicio = BooleanField("Manual de Servicio")

    clasificacion_riesgo = StringField(
        "Clasificación de Riesgo", validators=[Optional()]
    )
    clasificacion_biomedica = StringField(
        "Clasificación Biomédica", validators=[Optional()]
    )

    # ---------- Mantenimiento ----------
    periodicidad_mantenimiento = StringField(
        "Periodicidad Mantenimiento", validators=[Optional()]
    )
    requiere_calibracion = BooleanField("Requiere Calibración")
    periodicidad_metrologia = StringField(
        "Periodicidad Metrología", validators=[Optional()]
    )

    submit = SubmitField("Guardar Hoja de Vida")
