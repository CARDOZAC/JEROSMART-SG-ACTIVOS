from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional


class ActivoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional()])
    categoria = StringField("Categoría", validators=[Optional()])
    estado = SelectField(
        "Estado",
        choices=[("nuevo", "Nuevo"), ("usado", "Usado"), ("baja", "De baja")],
        validators=[DataRequired()],
    )
    valor = FloatField("Valor", validators=[Optional()])
    fecha_adquisicion = DateField(
        "Fecha de adquisición", format="%Y-%m-%d", validators=[Optional()]
    )
    submit = SubmitField("Guardar")
