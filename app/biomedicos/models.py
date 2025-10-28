from app.extensions import db
from datetime import datetime

# ===========================
# Hoja de Vida de un Equipo Biomédico
# ===========================
class HojaVidaBiomedico(db.Model):
    __tablename__ = "hojas_vida_biomedicos"

    id = db.Column(db.Integer, primary_key=True)

    # ---------- Datos Generales ----------
    equipo = db.Column(db.String(150), nullable=False)
    permiso_comercializacion = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    serie = db.Column(db.String(100), unique=True)
    inv_activo = db.Column(db.String(100))
    servicio = db.Column(db.String(100))
    ubicacion = db.Column(db.String(150))

    n_factura = db.Column(db.String(100))
    n_orden_compra = db.Column(db.String(100))
    fecha_fabricacion = db.Column(db.Date)
    fecha_instalacion = db.Column(db.Date)

    # ---------- Datos de Adquisición ----------
    distribuidor = db.Column(db.String(150))
    forma_adquisicion = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    correo_electronico = db.Column(db.String(100))
    fecha_ingreso = db.Column(db.Date)
    vencimiento_garantia = db.Column(db.Date)
    costo = db.Column(db.Float)
    vida_util_anios = db.Column(db.Integer)

    # ---------- Datos Técnicos ----------
    voltaje = db.Column(db.String(50))
    frecuencia = db.Column(db.String(50))
    dimensiones = db.Column(db.String(100))
    corriente = db.Column(db.String(50))
    potencia = db.Column(db.String(50))
    peso = db.Column(db.String(50))
    equipo_fijo_movil = db.Column(db.String(20))
    humedad_relativa = db.Column(db.String(50))
    temperatura_trabajo = db.Column(db.String(50))

    manual_usuario = db.Column(db.Boolean, default=False)
    manual_servicio = db.Column(db.Boolean, default=False)

    clasificacion_riesgo = db.Column(db.String(50))
    clasificacion_biomedica = db.Column(db.String(100))

    # ---------- Mantenimiento ----------
    periodicidad_mantenimiento = db.Column(db.String(100))
    requiere_calibracion = db.Column(db.Boolean, default=False)
    periodicidad_metrologia = db.Column(db.String(100))

    # ---------- Archivos Digitales ----------
    foto_url = db.Column(db.String(255))                # Foto del equipo
    hoja_pdf_url = db.Column(db.String(255))            # PDF generado automáticamente
    hoja_pdf_fisica_url = db.Column(db.String(255))     # PDF físico escaneado

    # ---------- Relaciones ----------
    accesorios = db.relationship(
        "AccesorioBiomedico",
        backref="hoja",
        lazy=True,
        cascade="all, delete"
    )
    mantenimientos = db.relationship(
        "MantenimientoHistorico",
        backref="hoja",
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<HojaVidaBiomedico {self.equipo} ({self.serie})>"


# ===========================
# Accesorios del Equipo
# ===========================
class AccesorioBiomedico(db.Model):
    __tablename__ = "accesorios_biomedicos"

    id = db.Column(db.Integer, primary_key=True)
    hoja_id = db.Column(db.Integer, db.ForeignKey("hojas_vida_biomedicos.id"), nullable=False)

    nombre = db.Column(db.String(150))
    marca = db.Column(db.String(100))
    modelo_tipo = db.Column(db.String(100))
    serie_detalle = db.Column(db.String(100))

    def __repr__(self):
        return f"<AccesorioBiomedico {self.nombre} - {self.marca}>"


# ===========================
# Histórico de Mantenimientos
# ===========================
class MantenimientoHistorico(db.Model):
    __tablename__ = "mantenimientos_historicos"

    id = db.Column(db.Integer, primary_key=True)
    hoja_id = db.Column(db.Integer, db.ForeignKey("hojas_vida_biomedicos.id"), nullable=False)

    fecha = db.Column(db.Date, default=datetime.utcnow)
    numero_reporte = db.Column(db.String(50))
    tipo_mtto = db.Column(db.String(100)) 
    actividad_observaciones = db.Column(db.Text)
    firma_responsable = db.Column(db.String(150))

    def __repr__(self):
        return f"<Mantenimiento {self.tipo_mtto} - {self.fecha}>"
