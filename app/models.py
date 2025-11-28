"""
Define los modelos de la base de datos utilizando el ORM de SQLAlchemy.
Cada clase representa una tabla en la base de datos.
"""
import json
from datetime import datetime
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func

# ==============================================================================
# Modelos de Catálogos y Entidades Principales
# ==============================================================================

class User(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column('clave_hash', db.String(256), nullable=False)
    cargo = db.Column(db.String(100))
    area = db.Column(db.String(100))
    rol = db.Column(db.String(20), nullable=False, default='User')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Funcionario(db.Model):
    __tablename__ = 'funcionarios'
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    cargo = db.Column(db.String(100))
    area = db.Column(db.String(100))
    activos = db.relationship('Activo', back_populates='funcionario')

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(150), unique=True, nullable=False)
    nit = db.Column(db.String(20), unique=True)
    direccion = db.Column(db.String(200))
    persona_contacto = db.Column(db.String(100))
    numero_contacto = db.Column(db.String(50))

class ClaseActivo(db.Model):
    __tablename__ = 'clases_activo'
    id = db.Column(db.Integer, primary_key=True)
    nombre_clase = db.Column(db.String(100), unique=True, nullable=False)

# ==============================================================================
# Modelos de Activos
# ==============================================================================

class Activo(db.Model):
    __tablename__ = 'activos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_activo = db.Column(db.String(150), nullable=False)
    placa_codigo_interno = db.Column(db.String(50), unique=True, nullable=False, index=True)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    serie = db.Column(db.String(50), index=True)
    ubicacion = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    valor_comercial = db.Column(db.Float)
    estado = db.Column(db.String(50), nullable=False, default='Operativo')
    created_at = db.Column(db.DateTime, server_default=func.now())
    tipo_propiedad = db.Column(db.String(20), nullable=False, default='Propio')
    origen_adquisicion = db.Column(db.String(50))
    condicion_tenencia = db.Column(db.String(50))
    clase_id = db.Column(db.Integer, db.ForeignKey('clases_activo.id'))
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), index=True)
    atributos_dinamicos_json = db.Column(db.Text) # para JSON
    propietario_ajeno = db.Column(db.String(150))
    contacto_propietario = db.Column(db.String(100))
    fecha_ingreso_ajeno = db.Column(db.Date)
    ruta_orden_compra = db.Column(db.String(255))
    ruta_factura = db.Column(db.String(255))
    ruta_contrato_arriendo = db.Column(db.String(255))
    ruta_foto_activo = db.Column(db.String(255))

    clase = db.relationship('ClaseActivo')
    funcionario = db.relationship('Funcionario', back_populates='activos')
    accesorios = db.relationship('ActivoAccesorio', back_populates='activo', cascade="all, delete-orphan")
    hoja_de_vida = db.relationship('HojaDeVida', back_populates='activo', uselist=False, cascade="all, delete-orphan")

class ActivoAccesorio(db.Model):
    __tablename__ = 'activo_accesorios'
    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), nullable=False)
    descripcion = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    serie = db.Column(db.String(50))
    activo = db.relationship('Activo', back_populates='accesorios')

class HojaDeVida(db.Model):
    __tablename__ = 'hojas_de_vida'
    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), unique=True, nullable=False)
    ruta_pdf_fisica = db.Column(db.String(255))
    ruta_foto_activo = db.Column(db.String(255))
    normativa_aplicable = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    activo = db.relationship('Activo', back_populates='hoja_de_vida')

# ==============================================================================
# Modelos de Movimientos
# ==============================================================================

class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    tipo_movimiento = db.Column(db.String(50), nullable=False, index=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observaciones_generales = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'))

    usuario = db.relationship('User')
    funcionario = db.relationship('Funcionario')
    activos = db.relationship('MovimientoActivo', back_populates='movimiento', cascade="all, delete-orphan")
    documentos_adjuntos = db.relationship('DocumentoAdjunto', back_populates='movimiento', cascade="all, delete-orphan")

    detalle_entrega = db.relationship('DetalleEntrega', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")
    detalle_traslado = db.relationship('DetalleTraslado', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")
    detalle_entrada_salida = db.relationship('DetalleEntradaSalida', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")
    detalle_paz_salvo = db.relationship('DetallePazSalvo', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")

class MovimientoActivo(db.Model):
    __tablename__ = 'movimiento_activos'
    id = db.Column(db.Integer, primary_key=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), nullable=False, index=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), nullable=False, index=True)
    movimiento = db.relationship('Movimiento', back_populates='activos')
    activo = db.relationship('Activo')
    accesorios = db.relationship('Accesorio', back_populates='movimiento_activo', cascade="all, delete-orphan")

class DocumentoAdjunto(db.Model):
    __tablename__ = 'documentos_adjuntos'
    id = db.Column(db.Integer, primary_key=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), nullable=False)
    nombre_documento = db.Column(db.String(150), nullable=False)
    ruta_archivo = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    movimiento = db.relationship('Movimiento', back_populates='documentos_adjuntos')

class Firma(db.Model):
    __tablename__ = 'firmas'
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, nullable=False, index=True)
    tipo_documento = db.Column(db.String(50), nullable=False) # 'movimiento' o 'mantenimiento'
    rol_firma = db.Column(db.String(50), nullable=False)
    firma_base64 = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('documento_id', 'tipo_documento', 'rol_firma'),)

class Accesorio(db.Model):
    __tablename__ = 'accesorios'
    id = db.Column(db.Integer, primary_key=True)
    movimiento_activo_id = db.Column(db.Integer, db.ForeignKey('movimiento_activos.id'), nullable=False, index=True)
    descripcion = db.Column(db.String, nullable=False)
    referencia = db.Column(db.String(100))
    serial = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    observacion = db.Column(db.Text)
    movimiento_activo = db.relationship('MovimientoActivo', back_populates='accesorios')

# ==============================================================================
# Modelos de Detalles de Movimientos (Relación 1 a 1 con Movimiento)
# ==============================================================================

class DetalleEntrega(db.Model):
    __tablename__ = 'detalles_entrega'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    factura = db.Column(db.String(50))
    orden_compra_contrato = db.Column(db.String(50))
    fecha_oc_contrato = db.Column(db.Date)
    objeto_contrato = db.Column(db.Text)
    tipo_elementos = db.Column(db.Text) # JSON
    requiere_montaje = db.Column(db.Boolean)
    requiere_capacitacion = db.Column(db.Boolean)
    tipo_asignacion = db.Column(db.String(50))
    quien_entrega_nombre = db.Column(db.String(150))
    quien_recibe_nombre = db.Column(db.String(150))
    observaciones_acta = db.Column(db.Text)
    movimiento = db.relationship('Movimiento', back_populates='detalle_entrega')
    proveedor = db.relationship('Proveedor')

class DetalleTraslado(db.Model):
    __tablename__ = 'detalles_traslado'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    fecha_traslado = db.Column(db.Date)
    hora_traslado = db.Column(db.Time)
    tipo_traslado_json = db.Column(db.Text) # JSON
    ubicacion_inicial = db.Column(db.String(100))
    ubicacion_final = db.Column(db.String(100))
    origen_responsable_nombre = db.Column(db.String(150))
    origen_responsable_cc = db.Column(db.String(20))
    origen_responsable_cargo = db.Column(db.String(100))
    nuevo_responsable_nombre = db.Column(db.String(150))
    nuevo_responsable_cc = db.Column(db.String(20))
    nuevo_responsable_cargo = db.Column(db.String(100))
    movimiento = db.relationship('Movimiento', back_populates='detalle_traslado')

class DetalleEntradaSalida(db.Model):
    __tablename__ = 'detalles_entrada_salida'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    ciudad = db.Column(db.String(50))
    sede = db.Column(db.String(50))
    solicitante_responsable_nombre = db.Column(db.String(150))
    solicitante_responsable_cc = db.Column(db.String(20))
    solicitante_responsable_cargo_area = db.Column(db.String(100))
    tercero_entidad_persona = db.Column(db.String(150))
    tercero_nit_cc = db.Column(db.String(20))
    tercero_direccion = db.Column(db.String(200))
    tercero_movil = db.Column(db.String(50))
    tipo_operacion = db.Column(db.String(20), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    fecha_retorno_estimada = db.Column(db.Date)
    movimiento = db.relationship('Movimiento', back_populates='detalle_entrada_salida')

class DetallePazSalvo(db.Model):
    __tablename__ = 'detalles_paz_salvo'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    funcionario_desvinculado_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    nombre_funcionario = db.Column(db.String(150))
    cargo_funcionario = db.Column(db.String(100))
    area_funcionario = db.Column(db.String(100))
    observaciones_paz_salvo = db.Column(db.Text)
    movimiento = db.relationship('Movimiento', back_populates='detalle_paz_salvo')
    funcionario_desvinculado = db.relationship('Funcionario')

# ==============================================================================
# Modelos de Mantenimiento (Gestión Biomédica)
# ==============================================================================

class MantenimientoTipo(db.Model):
    __tablename__ = 'mantenimiento_tipos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

class Mantenimiento(db.Model):
    __tablename__ = 'mantenimientos'
    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), nullable=False, index=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('mantenimiento_tipos.id'), nullable=False, index=True)
    fecha_mantenimiento = db.Column(db.Date, nullable=False)
    duracion_minutos = db.Column(db.Integer)
    observaciones = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='Pendiente')
    atributos_reporte_json = db.Column(db.Text) # JSON

    activo = db.relationship('Activo')
    tipo = db.relationship('MantenimientoTipo')
    usuario = db.relationship('User')
    fotos = db.relationship('MantenimientoFoto', back_populates='mantenimiento', cascade="all, delete-orphan")

class MantenimientoFoto(db.Model):
    __tablename__ = 'mantenimiento_fotos'
    id = db.Column(db.Integer, primary_key=True)
    mantenimiento_id = db.Column(db.Integer, db.ForeignKey('mantenimientos.id'), nullable=False, index=True)
    ruta_foto = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    mantenimiento = db.relationship('Mantenimiento', back_populates='fotos')
