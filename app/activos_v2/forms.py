# ==============================================================================
# FORMULARIOS DEL MÓDULO ACTIVOS V2
# ==============================================================================

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    DateField,
    DecimalField,
    IntegerField,
    HiddenField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import date


# ==============================================================================
# FORMULARIO DE MANTENIMIENTO
# ==============================================================================
class MantenimientoForm(FlaskForm):
    """Formulario para registrar mantenimientos de activos"""

    fecha_mantenimiento = DateField(
        "Fecha del Mantenimiento",
        validators=[DataRequired(message="La fecha es obligatoria")],
        default=date.today,
    )

    tipo_mantenimiento = SelectField(
        "Tipo de Mantenimiento",
        choices=[
            ("", "-- Seleccione --"),
            ("Preventivo", "Preventivo"),
            ("Correctivo", "Correctivo"),
            ("Calibración", "Calibración"),
            ("Inspección", "Inspección"),
            ("Actualización", "Actualización de Software/Firmware"),
        ],
        validators=[DataRequired(message="Seleccione el tipo")],
    )

    descripcion = TextAreaField(
        "Descripción del Mantenimiento",
        validators=[
            DataRequired(message="La descripción es obligatoria"),
            Length(min=10, max=2000, message="Entre 10 y 2000 caracteres"),
        ],
        render_kw={"rows": 4, "placeholder": "Describa el mantenimiento realizado..."},
    )

    tecnico_nombre = StringField(
        "Nombre del Técnico",
        validators=[Length(max=150)],
        render_kw={"placeholder": "Nombre completo del técnico"},
    )

    tecnico_empresa = StringField(
        "Empresa/Entidad",
        validators=[Length(max=150)],
        render_kw={"placeholder": "Empresa que realizó el mantenimiento"},
    )

    costo = DecimalField(
        "Costo (COP)",
        places=2,
        validators=[
            Optional(),
            NumberRange(min=0, message="El costo debe ser positivo"),
        ],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )

    proximo_mantenimiento = DateField(
        "Próximo Mantenimiento Estimado", validators=[Optional()]
    )

    observaciones = TextAreaField(
        "Observaciones Adicionales",
        validators=[Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Observaciones, recomendaciones, repuestos cambiados, etc.",
        },
    )

    fotos = MultipleFileField(
        "Fotos del Mantenimiento",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "gif"], "Solo imágenes (JPG, PNG, GIF)")
        ],
    )

    submit = SubmitField("Guardar Mantenimiento")


# ==============================================================================
# FORMULARIO DE EDICIÓN DE ACTIVO (SIMPLIFICADO)
# ==============================================================================
class ActivoEditForm(FlaskForm):
    """Formulario simplificado para editar activos sin wizard"""

    # Datos Básicos
    nombre_activo = StringField(
        "Nombre del Activo",
        validators=[DataRequired(message="El nombre es obligatorio"), Length(max=200)],
    )

    placa_codigo_interno = StringField("Placa/Serie", validators=[Length(max=50)])

    clase_id = SelectField("Clase de Activo", coerce=int, validators=[DataRequired()])

    estado = SelectField(
        "Estado",
        choices=[
            ("Operativo", "Operativo"),
            ("En reparación", "En reparación"),
            ("En mantenimiento", "En mantenimiento"),
            ("Dado de baja", "Dado de baja"),
        ],
        validators=[DataRequired()],
    )

    # Ubicación (campo String, no FK)
    ubicacion = StringField("Ubicación", validators=[Length(max=200)])

    # Responsable (funcionario_id)
    funcionario_id = SelectField(
        "Responsable (Funcionario)", coerce=int, validators=[Optional()]
    )

    # Campos de adquisición
    proveedor_id = SelectField("Proveedor", coerce=int, validators=[Optional()])
    fecha_compra = DateField("Fecha de Compra", validators=[Optional()])
    valor_compra = DecimalField(
        "Valor de Compra", validators=[Optional(), NumberRange(min=0)]
    )

    # Documentos
    orden_compra = FileField(
        "Orden de Compra",
        validators=[
            Optional(),
            FileAllowed(["pdf", "jpg", "png", "jpeg"], "PDF, JPG o PNG solamente."),
        ],
    )
    factura = FileField(
        "Factura",
        validators=[
            Optional(),
            FileAllowed(["pdf", "jpg", "png", "jpeg"], "PDF, JPG o PNG solamente."),
        ],
    )
    documento_soporte = FileField(
        "Documento de Soporte",
        validators=[
            Optional(),
            FileAllowed(["pdf", "jpg", "png", "jpeg"], "PDF, JPG o PNG solamente."),
        ],
    )

    # Observaciones
    observaciones = TextAreaField(
        "Observaciones", validators=[Length(max=2000)], render_kw={"rows": 3}
    )

    submit = SubmitField("Guardar Cambios")


# ==============================================================================
# FORMULARIO DE FILTROS (Para búsqueda avanzada)
# ==============================================================================
class FiltrosActivosForm(FlaskForm):
    """Formulario para filtros avanzados de búsqueda"""

    nombre = StringField("Nombre", render_kw={"placeholder": "Buscar por nombre..."})
    placa = StringField("Placa", render_kw={"placeholder": "Buscar por placa..."})
    clase_id = SelectField("Clase", coerce=int)
    ubicacion_id = SelectField("Ubicación", coerce=int)
    estado = SelectField("Estado")

    submit = SubmitField("Filtrar")
