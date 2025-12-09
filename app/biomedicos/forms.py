from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Optional
from wtforms_sqlalchemy.fields import QuerySelectField
from ..models import Activo, ClaseActivo


def activos_biomedicos():
    """Retorna un query de los activos que son biomédicos."""
    return (
        Activo.query.join(ClaseActivo)
        .filter(ClaseActivo.id == 1)
        .order_by(Activo.nombre_activo)
    )


class CargarHistoricoBiomedicoForm(FlaskForm):
    """Formulario para cargar un mantenimiento histórico en PDF para un activo biomédico."""

    activo_id = QuerySelectField(
        "Activo Biomédico",
        query_factory=activos_biomedicos,
        get_label="nombre_activo",
        allow_blank=False,
        validators=[DataRequired(message="Debe seleccionar un activo biomédico.")],
    )
    documento = FileField(
        "Documento PDF del Mantenimiento",
        validators=[
            DataRequired(message="Debe seleccionar un archivo PDF."),
            FileAllowed(["pdf"], "¡Solo se permiten archivos PDF!"),
        ],
    )
    fecha_mantenimiento = DateField(
        "Fecha de Realización del Mantenimiento",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha es obligatoria.")],
    )
    observaciones = TextAreaField(
        "Observaciones (Opcional)", validators=[Optional()], render_kw={"rows": 3}
    )
    submit = SubmitField("Cargar Histórico Biomédico")
