from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DateField, FloatField, IntegerField,
    BooleanField, FileField, SelectField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, Email

# ===========================
# Formulario Hoja de Vida Biomédico
# ===========================
class HojaVidaBiomedicoForm(FlaskForm):
    # ---------- Datos Generales ----------
    equipo = StringField("Equipo", validators=[DataRequired(), Length(max=150)])
    permiso_comercializacion = StringField("Permiso de Comercialización", validators=[Optional()])
    marca = StringField("Marca", validators=[Optional()])
    modelo = StringField("Modelo", validators=[Optional()])
    serie = StringField("Serie", validators=[Optional()])
    inv_activo = StringField("Inventario Activo", validators=[Optional()])
    servicio = StringField("Servicio", validators=[Optional()])
    ubicacion = StringField("Ubicación", validators=[Optional()])

    n_factura = StringField("No. Factura", validators=[Optional()])
    n_orden_compra = StringField("No. Orden de Compra", validators=[Optional()])
    fecha_fabricacion = DateField("Fecha de Fabricación", format="%Y-%m-%d", validators=[Optional()])
    fecha_instalacion = DateField("Fecha de Instalación", format="%Y-%m-%d", validators=[Optional()])

    # ---------- Datos de Adquisición ----------
    distribuidor = StringField("Distribuidor", validators=[Optional()])
    forma_adquisicion = StringField("Forma de Adquisición", validators=[Optional()])
    telefono = StringField("Teléfono", validators=[Optional()])
    correo_electronico = StringField("Correo Electrónico", validators=[Optional(), Email()])
    fecha_ingreso = DateField("Fecha de Ingreso", format="%Y-%m-%d", validators=[Optional()])
    vencimiento_garantia = DateField("Vencimiento Garantía", format="%Y-%m-%d", validators=[Optional()])
    costo = FloatField("Costo", validators=[Optional()])
    vida_util_anios = IntegerField("Vida Útil (años)", validators=[Optional()])

    # ---------- Datos Técnicos ----------
    voltaje = StringField("Voltaje", validators=[Optional()])
    frecuencia = StringField("Frecuencia", validators=[Optional()])
    dimensiones = StringField("Dimensiones", validators=[Optional()])
    corriente = StringField("Corriente", validators=[Optional()])
    potencia = StringField("Potencia", validators=[Optional()])
    peso = StringField("Peso", validators=[Optional()])
    equipo_fijo_movil = SelectField("Fijo/Móvil", choices=[("fijo", "Fijo"), ("movil", "Móvil")], validators=[Optional()])
    humedad_relativa = StringField("Humedad Relativa", validators=[Optional()])
    temperatura_trabajo = StringField("Temperatura de Trabajo", validators=[Optional()])

    manual_usuario = BooleanField("Manual de Usuario")
    manual_servicio = BooleanField("Manual de Servicio")

    clasificacion_riesgo = StringField("Clasificación de Riesgo", validators=[Optional()])
    clasificacion_biomedica = StringField("Clasificación Biomédica", validators=[Optional()])

    # ---------- Mantenimiento ----------
    periodicidad_mantenimiento = StringField("Periodicidad Mantenimiento", validators=[Optional()])
    requiere_calibracion = BooleanField("Requiere Calibración")
    periodicidad_metrologia = StringField("Periodicidad Metrología", validators=[Optional()])

    # ---------- Archivos Digitales ----------
    foto_url = FileField("Subir Foto del Equipo", validators=[Optional()])
    hoja_pdf_fisica_url = FileField("Subir Hoja de Vida Física (PDF)", validators=[Optional()])

    submit = SubmitField("Guardar Hoja de Vida")


# ===========================
# Formulario Accesorios
# ===========================
class AccesorioBiomedicoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    marca = StringField("Marca", validators=[Optional()])
    modelo_tipo = StringField("Modelo/Tipo", validators=[Optional()])
    serie_detalle = StringField("Serie", validators=[Optional()])
    submit = SubmitField("Agregar Accesorio")


# ===========================
# Formulario Mantenimiento Histórico
# ===========================
class MantenimientoHistoricoForm(FlaskForm):
    fecha = DateField("Fecha", format="%Y-%m-%d", validators=[DataRequired()])
    numero_reporte = StringField("Número de Reporte", validators=[Optional()])
    tipo_mtto = SelectField("Tipo de Mantenimiento", choices=[
        ("preventivo", "Preventivo"),
        ("correctivo", "Correctivo"),
        ("calibracion", "Calibración")
    ], validators=[DataRequired()])
    actividad_observaciones = TextAreaField("Actividades / Observaciones", validators=[Optional()])
    firma_responsable = StringField("Firma Responsable", validators=[Optional()])
    evidencias = FileField("Subir Evidencias (PDF, imágenes, etc.)", validators=[Optional()])
    submit = SubmitField("Registrar Mantenimiento")
