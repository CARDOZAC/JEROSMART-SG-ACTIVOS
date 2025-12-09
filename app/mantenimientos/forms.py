from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Optional
from wtforms_sqlalchemy.fields import QuerySelectField
from ..models import Activo, MantenimientoTipo, ClaseActivo


def activos_no_biomedicos():
    """Retorna un query de los activos que no son biomédicos."""
    return (
        Activo.query.join(ClaseActivo)
        .filter(ClaseActivo.id.in_([2, 3, 4]))
        .order_by(Activo.nombre_activo)
    )


def tipos_de_mantenimiento():
    """Retorna un query de todos los tipos de mantenimiento."""
    return MantenimientoTipo.query.order_by(MantenimientoTipo.nombre)


class MantenimientoForm(FlaskForm):
    """Formulario para crear o editar un mantenimiento."""

    activo_id = QuerySelectField(
        "Activo Fijo",
        query_factory=activos_no_biomedicos,
        get_label="nombre_activo",
        allow_blank=False,
        validators=[DataRequired(message="Debe seleccionar un activo.")],
    )
    tipo_id = QuerySelectField(
        "Tipo de Mantenimiento",
        query_factory=tipos_de_mantenimiento,
        get_label="nombre",
        allow_blank=False,
        validators=[DataRequired(message="Debe seleccionar un tipo de mantenimiento.")],
    )
    fecha_mantenimiento = DateField(
        "Fecha Programada",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha es obligatoria.")],
    )
    estado = SelectField(
        "Estado",
        choices=[
            ("Pendiente", "Pendiente"),
            ("En Proceso", "En Proceso"),
            ("Completado", "Completado"),
            ("Cancelado", "Cancelado"),
        ],
        validators=[DataRequired(message="Debe seleccionar un estado.")],
    )
    observaciones = TextAreaField(
        "Observaciones y Actividades Realizadas",
        validators=[Optional()],
        render_kw={"rows": 5},
    )
    submit = SubmitField("Guardar Mantenimiento")


class CargarHistoricoForm(FlaskForm):
    """Formulario para cargar un mantenimiento histórico en PDF."""

    activo_id = QuerySelectField(
        "Activo Fijo",
        query_factory=activos_no_biomedicos,
        get_label="nombre_activo",
        allow_blank=False,
        validators=[DataRequired(message="Debe seleccionar un activo.")],
    )
    documento = FileField(
        "Documento PDF",
        validators=[
            DataRequired(message="Debe seleccionar un archivo."),
            FileAllowed(["pdf"], "¡Solo se permiten archivos PDF!"),
        ],
    )
    fecha_mantenimiento = DateField(
        "Fecha de Realización",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha es obligatoria.")],
    )
    observaciones = TextAreaField(
        "Observaciones (Opcional)", validators=[Optional()], render_kw={"rows": 3}
    )
    submit = SubmitField("Cargar Mantenimiento")
