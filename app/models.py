"""
Define los modelos de la base de datos utilizando el ORM de SQLAlchemy.
Cada clase representa una tabla en la base de datos.
"""
import json
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'usuarios'  # Especifica el nombre exacto de la tabla en la BD.

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Mapea el atributo 'password_hash' a la columna 'clave_hash' de la tabla.
    password_hash = db.Column('clave_hash', db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='user')
    cargo = db.Column(db.String(100))
    area = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Activo(db.Model):
    __tablename__ = 'activos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    placa_codigo_interno = db.Column(db.String, unique=True, nullable=False)
    serie = db.Column(db.String)
    # ... otros campos del activo

class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    tipo_movimiento = db.Column(db.String, nullable=False)
    fecha = db.Column(db.String, nullable=False)
    observaciones_generales = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    usuario = db.relationship('User')
    activos = db.relationship('MovimientoActivo', back_populates='movimiento', cascade="all, delete-orphan")

    # Relaciones para cada tipo de detalle
    detalle_entrega = db.relationship('DetalleEntrega', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")
    detalle_traslado = db.relationship('DetalleTraslado', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")
    detalle_entrada_salida = db.relationship('DetalleEntradaSalida', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")
    detalle_paz_salvo = db.relationship('DetallePazSalvo', back_populates='movimiento', uselist=False, cascade="all, delete-orphan")

class MovimientoActivo(db.Model):
    __tablename__ = 'movimiento_activos'
    id = db.Column(db.Integer, primary_key=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), nullable=False)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), nullable=False)

    movimiento = db.relationship('Movimiento', back_populates='activos')
    activo = db.relationship('Activo')
    accesorios = db.relationship('Accesorio', back_populates='movimiento_activo', cascade="all, delete-orphan")

class Accesorio(db.Model):
    __tablename__ = 'accesorios'
    id = db.Column(db.Integer, primary_key=True)
    movimiento_activo_id = db.Column(db.Integer, db.ForeignKey('movimiento_activos.id'), nullable=False)
    descripcion = db.Column(db.String, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)

    movimiento_activo = db.relationship('MovimientoActivo', back_populates='accesorios')

class DetalleEntrega(db.Model):
    __tablename__ = 'detalles_entrega'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    proveedor_id = db.Column(db.Integer)
    factura = db.Column(db.String)
    orden_compra_contrato = db.Column(db.String)
    fecha_oc_contrato = db.Column(db.String)
    objeto_contrato = db.Column(db.String)
    tipo_elementos = db.Column(db.String) # JSON
    requiere_montaje = db.Column(db.Boolean)
    requiere_capacitacion = db.Column(db.Boolean)
    tipo_asignacion = db.Column(db.String)
    quien_entrega_nombre = db.Column(db.String)
    quien_recibe_nombre = db.Column(db.String)
    observaciones_acta = db.Column(db.Text)

    movimiento = db.relationship('Movimiento', back_populates='detalle_entrega')

class DetalleTraslado(db.Model):
    __tablename__ = 'detalles_traslado'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    fecha_traslado = db.Column(db.String)
    hora_traslado = db.Column(db.String)
    tipo_traslado_json = db.Column(db.String) # JSON
    ubicacion_inicial = db.Column(db.String)
    ubicacion_final = db.Column(db.String)
    origen_responsable_nombre = db.Column(db.String)
    origen_responsable_cc = db.Column(db.String)
    origen_responsable_cargo = db.Column(db.String)
    nuevo_responsable_nombre = db.Column(db.String)
    nuevo_responsable_cc = db.Column(db.String)
    nuevo_responsable_cargo = db.Column(db.String)

    movimiento = db.relationship('Movimiento', back_populates='detalle_traslado')

class DetalleEntradaSalida(db.Model):
    __tablename__ = 'detalles_entrada_salida'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    ciudad = db.Column(db.String)
    sede = db.Column(db.String)
    solicitante_responsable_nombre = db.Column(db.String)
    solicitante_responsable_cc = db.Column(db.String)
    solicitante_responsable_cargo_area = db.Column(db.String)
    tercero_entidad_persona = db.Column(db.String)
    tercero_nit_cc = db.Column(db.String)
    tercero_direccion = db.Column(db.String)
    tercero_movil = db.Column(db.String)
    tipo_operacion = db.Column(db.String, nullable=False)
    motivo = db.Column(db.String, nullable=False)
    fecha_retorno_estimada = db.Column(db.String)

    movimiento = db.relationship('Movimiento', back_populates='detalle_entrada_salida')

class DetallePazSalvo(db.Model):
    __tablename__ = 'detalles_paz_salvo'
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'), primary_key=True)
    funcionario_desvinculado_id = db.Column(db.Integer, nullable=False)
    nombre_funcionario = db.Column(db.String)
    cargo_funcionario = db.Column(db.String)
    area_funcionario = db.Column(db.String)
    observaciones_paz_salvo = db.Column(db.Text)

    movimiento = db.relationship('Movimiento', back_populates='detalle_paz_salvo')
