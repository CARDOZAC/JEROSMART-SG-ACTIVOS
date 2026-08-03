"""
Define los modelos de la base de datos utilizando el ORM de SQLAlchemy.
Cada clase representa una tabla en la base de datos.
Este archivo contiene TODOS los modelos de la aplicación, consolidados desde init_db.py.
"""
import json
from datetime import datetime, date # Keep this for general use
from .extensions import db
from flask_login import UserMixin, current_user # Added current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import LONGTEXT


# ==============================================================================
# USUARIOS
# ==============================================================================
class User(db.Model, UserMixin):
    """Usuario del sistema con autenticación."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column('clave_hash', db.String(512), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='User')
    cargo = db.Column(db.String(100))
    area = db.Column(db.String(100))

    # Relaciones
    # Relación para los movimientos CREADOS por el usuario.
    movimientos = db.relationship('Movimiento', foreign_keys='Movimiento.usuario_id', back_populates='usuario', lazy='dynamic')
    # Relación para los movimientos APROBADOS por el usuario.
    movimientos_aprobados = db.relationship('Movimiento', foreign_keys='Movimiento.aprobado_por_id', back_populates='aprobador', lazy='dynamic')
    
    mantenimientos = db.relationship('Mantenimiento', back_populates='usuario', lazy=True, foreign_keys='Mantenimiento.usuario_id')

    def set_password(self, password):
        """Establece la contraseña hasheada."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña es correcta."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.rol})>'


# ==============================================================================
# FUNCIONARIOS
# ==============================================================================
class Funcionario(db.Model):
    """Empleado o funcionario de la organización."""
    __tablename__ = 'funcionarios'

    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    cargo = db.Column(db.String(100))
    area = db.Column(db.String(100))
    centro_costo = db.Column(db.String(100))  # Centro de costo del funcionario
    estado = db.Column(db.String(50), nullable=False, default='Activo', index=True) # Estado del funcionario (Activo, Inactivo)

    # Relaciones
    activos = db.relationship('Activo', back_populates='funcionario', lazy=True)
    detalles_paz_salvo = db.relationship('DetallePazSalvo', back_populates='funcionario_desvinculado', lazy=True)

    @property
    def nombre_completo(self):
        """Nombre y apellidos concatenados para mostrar en UI y reportes."""
        return f"{self.nombres or ''} {self.apellidos or ''}".strip()

    def __repr__(self):
        return f'<Funcionario {self.nombres} {self.apellidos} ({self.cedula})>'


# ==============================================================================
# PROVEEDORES
# ==============================================================================
class Proveedor(db.Model):
    """Proveedores o distribuidores de activos."""
    __tablename__ = 'proveedores'

    id = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(200), unique=True, nullable=False)
    nit = db.Column(db.String(50), unique=True, nullable=False, index=True)
    direccion = db.Column(db.String(200), nullable=False)
    persona_contacto = db.Column(db.String(150))
    numero_contacto = db.Column(db.String(50))

    # Relaciones
    detalles_entrega = db.relationship('DetalleEntrega', back_populates='proveedor', lazy=True)

    def __repr__(self):
        return f'<Proveedor {self.razon_social}>'


# ==============================================================================
# CLASES DE ACTIVO
# ==============================================================================
class ClaseActivo(db.Model):
    """Clasificación de activos (Biomédico, TICs, Muebles, etc.)."""
    __tablename__ = 'clases_activo'

    id = db.Column(db.Integer, primary_key=True)
    nombre_clase = db.Column(db.String(100), unique=True, nullable=False)

    # Relaciones
    activos = db.relationship('Activo', back_populates='clase', lazy=True)

    def __repr__(self):
        return f'<ClaseActivo {self.nombre_clase}>'


# ==============================================================================
# ACTIVOS
# ==============================================================================
class Activo(db.Model):
    """Activo fijo de la organización."""
    __tablename__ = 'activos'

    id = db.Column(db.Integer, primary_key=True)
    nombre_activo = db.Column(db.String(200), nullable=False)
    placa_codigo_interno = db.Column(db.String(100), unique=True, nullable=False, index=True)
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    serie = db.Column(db.String(100), index=True)
    ubicacion = db.Column(db.String(200))
    observaciones = db.Column(db.Text)
    valor_comercial = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(50), nullable=False, default='Operativo')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    tipo_propiedad = db.Column(db.String(20), nullable=False, default='Propio')
    origen_adquisicion = db.Column(db.String(50))
    condicion_tenencia = db.Column(db.String(50))
    atributos_dinamicos_json = db.Column(db.JSON, nullable=True)
    propietario_ajeno = db.Column(db.String(200))
    contacto_propietario = db.Column(db.String(100))
    fecha_ingreso_ajeno = db.Column(db.DateTime, nullable=True)

    # ===== Datos de contrato del activo ajeno (comodato / arriendo / leasing) =====
    # Alimentan el dashboard de activos ajenos: alertas de vencimiento y costo mensual.
    nit_propietario = db.Column(db.String(50))
    telefono_propietario = db.Column(db.String(50))
    email_propietario = db.Column(db.String(100))
    numero_contrato = db.Column(db.String(100))
    fecha_inicio_contrato = db.Column(db.Date, nullable=True)
    fecha_fin_contrato = db.Column(db.Date, nullable=True, index=True)
    observaciones_contrato = db.Column(db.Text)
    costo_mensual = db.Column(db.Float)
    ruta_orden_compra = db.Column(db.String(500))
    ruta_factura = db.Column(db.String(500))
    ruta_contrato_arriendo = db.Column(db.String(500))
    ruta_foto_activo = db.Column(db.String(500))

    # ===== FASE 3: Sistema de Ingreso Temporal de Activos Ajenos =====
    es_ingreso_temporal = db.Column(db.Boolean, default=False, nullable=True)
    fecha_inicio_temporal = db.Column(db.DateTime, nullable=True)
    fecha_fin_temporal = db.Column(db.DateTime, nullable=True)

    # ===== FASE 1.1: Sistema de Conciliación Física (Anti-Activo Fantasma) =====
    # La verdad física como estándar del sistema - Fundamento legal de trazabilidad
    estado_conciliacion = db.Column(db.String(20), default='Pendiente', nullable=False, index=True)
    # Valores posibles: 'Verificado', 'Pendiente', 'No Encontrado'
    fecha_ultima_verificacion = db.Column(db.DateTime, nullable=True)
    usuario_ultima_verificacion_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    notas_verificacion = db.Column(db.Text, nullable=True)  # Observaciones durante la verificación física

    # ===== FASE 2.1: Atributos Dinámicos (EAV Mejorado) =====
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_activo.id', ondelete='SET NULL'), nullable=True, index=True)

    # Foreign Keys
    clase_id = db.Column(db.Integer, db.ForeignKey('clases_activo.id'))
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id', ondelete='SET NULL'))

    # Relaciones
    clase = db.relationship('ClaseActivo', back_populates='activos')
    funcionario = db.relationship('Funcionario', back_populates='activos')
    usuario_verificador = db.relationship('User', foreign_keys=[usuario_ultima_verificacion_id], backref='activos_verificados')
    accesorios_activo = db.relationship('ActivoAccesorio', back_populates='activo',
                                        cascade='all, delete-orphan', lazy=True)
    movimiento_activos = db.relationship('MovimientoActivo', back_populates='activo', lazy=True)
    hoja_vida_biomedico = db.relationship('HojaVidaBiomedico', back_populates='activo',
                                uselist=False, cascade='all, delete-orphan')
    mantenimientos = db.relationship('Mantenimiento', back_populates='activo',
                                    cascade='all, delete-orphan', lazy=True)
    # FASE 1.2: Auditoría histórica completa
    historial = db.relationship('ActivoHistorico', back_populates='activo',
                               cascade='all, delete-orphan', lazy='dynamic', order_by='ActivoHistorico.timestamp.desc()')

    # FASE 2.1: Relaciones para Atributos Dinámicos (EAV)
    categoria = db.relationship('CategoriaActivo', back_populates='activos')
    atributos_valores = db.relationship(
        'AtributoValor',
        back_populates='activo',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='AtributoValor.id'
    )

    @property
    def valor_comercial_safe(self):
        """Retorna el valor comercial, garantizando que nunca sea None."""
        return self.valor_comercial if self.valor_comercial is not None else 0.0

    @property
    def depreciacion_acumulada(self):
        """
        Calcula la depreciación acumulada usando el método de línea recta.
        Esta es una propiedad calculada, no una columna de la BD.
        """
        if not self.valor_comercial or not self.created_at or self.tipo_propiedad != 'Propio':
            return 0

        vida_util_anios = 10  # Vida útil por defecto en años
        if self.clase_id == 1:  # Equipo Biomédico
            try:
                attrs = self.atributos_dinamicos_json or {}
                vida_util_anios = int(attrs.get('vida_util', 10))
            except (TypeError, ValueError):
                vida_util_anios = 10
        elif self.clase_id == 3: # TICs
            vida_util_anios = 5

        try:
            # No need for strptime if created_at is a datetime object
            fecha_compra = self.created_at
            anios_transcurridos = (datetime.now() - fecha_compra).days / 365.25
        except (ValueError, TypeError):
            return 0 # No se puede calcular si la fecha es inválida

        if anios_transcurridos <= 0:
            return 0

        depreciacion_anual = self.valor_comercial / vida_util_anios
        depreciacion_total = depreciacion_anual * anios_transcurridos
        return min(depreciacion_total, self.valor_comercial) # La depreciación no puede superar el valor del activo

    @property
    def valor_en_libros(self):
        """Calcula el valor actual del activo en los libros contables."""
        return (self.valor_comercial or 0) - self.depreciacion_acumulada

    @property
    def dias_para_vencimiento_contrato(self):
        """
        Días restantes hasta el vencimiento del contrato del activo ajeno.
        Negativo si ya venció, None si no hay fecha de fin registrada.
        """
        if not self.fecha_fin_contrato:
            return None
        return (self.fecha_fin_contrato - date.today()).days

    @property
    def contrato_vencido(self):
        """True si el contrato del activo ajeno ya venció."""
        dias = self.dias_para_vencimiento_contrato
        return dias is not None and dias < 0

    def contrato_proximo_a_vencer(self, dias_alerta=30):
        """True si el contrato vence dentro de los próximos `dias_alerta` días."""
        dias = self.dias_para_vencimiento_contrato
        return dias is not None and 0 <= dias <= dias_alerta

    def __repr__(self):
        return f'<Activo {self.nombre_activo} ({self.placa_codigo_interno})>'

    # ========== FASE 2.1: Métodos para gestión de atributos dinámicos ==========

    def get_atributo_valor(self, nombre_atributo):
        """
        Obtiene el valor de un atributo específico por su nombre.

        Args:
            nombre_atributo (str): Nombre snake_case del atributo

        Returns:
            El valor del atributo o None si no existe
        """
        if not self.categoria_id:
            return None

        # Buscar la definición del atributo
        from app.models import AtributoDefinicion, AtributoValor

        definicion = AtributoDefinicion.query.filter_by(
            categoria_id=self.categoria_id,
            nombre=nombre_atributo,
            activo=True
        ).first()

        if not definicion:
            return None

        # Buscar el valor asignado
        valor_obj = self.atributos_valores.filter_by(
            atributo_definicion_id=definicion.id
        ).first()

        return valor_obj.valor if valor_obj else definicion.valor_por_defecto

    def set_atributo_valor(self, nombre_atributo, valor, usuario_id=None):
        """
        Establece el valor de un atributo dinámico.

        Args:
            nombre_atributo (str): Nombre snake_case del atributo
            valor: Valor a asignar (será validado según el tipo de dato)
            usuario_id (int, optional): ID del usuario que realiza el cambio

        Returns:
            tuple: (success: bool, mensaje: str)

        Raises:
            ValueError: Si la validación falla
        """
        if not self.categoria_id:
            return False, "El activo no tiene una categoría asignada"

        from app.models import AtributoDefinicion, AtributoValor

        # Buscar la definición del atributo
        definicion = AtributoDefinicion.query.filter_by(
            categoria_id=self.categoria_id,
            nombre=nombre_atributo,
            activo=True
        ).first()

        if not definicion:
            return False, f"El atributo '{nombre_atributo}' no existe para esta categoría"

        # Validar el valor
        es_valido, mensaje_error = definicion.validar_valor(valor)
        if not es_valido:
            return False, mensaje_error

        # Buscar o crear el valor
        valor_obj = self.atributos_valores.filter_by(
            atributo_definicion_id=definicion.id
        ).first()

        if not valor_obj:
            valor_obj = AtributoValor(
                activo_id=self.id,
                atributo_definicion_id=definicion.id
            )
            db.session.add(valor_obj)

        # Asignar el valor (capturando el valor anterior ANTES de sobrescribirlo)
        try:
            valor_anterior = valor_obj.valor
            valor_obj.valor = valor
            valor_obj.updated_at = datetime.utcnow()
            db.session.commit()

            # FASE 1.2: Registrar cambio en historial si hay usuario
            if usuario_id:
                from app.models import ActivoHistorico
                cambio = ActivoHistorico(
                    activo_id=self.id,
                    usuario_id=usuario_id,
                    tipo_operacion='UPDATE',
                    campo_modificado=nombre_atributo,
                    valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
                    valor_nuevo=str(valor),
                    observaciones=f"Atributo '{definicion.etiqueta}' actualizado"
                )
                db.session.add(cambio)
                db.session.commit()

            return True, "Atributo actualizado correctamente"

        except Exception as e:
            db.session.rollback()
            return False, f"Error al guardar el atributo: {str(e)}"

    def get_atributos_dict(self):
        """
        Retorna todos los atributos del activo como diccionario.

        Returns:
            dict: {nombre_atributo: valor} para todos los atributos definidos
        """
        if not self.categoria_id:
            return {}

        from app.models import AtributoDefinicion

        resultado = {}

        # Obtener todas las definiciones de atributos para esta categoría
        definiciones = AtributoDefinicion.query.filter_by(
            categoria_id=self.categoria_id,
            activo=True
        ).order_by(AtributoDefinicion.orden_visualizacion).all()

        for definicion in definiciones:
            valor = self.get_atributo_valor(definicion.nombre)
            resultado[definicion.nombre] = {
                'etiqueta': definicion.etiqueta,
                'valor': valor,
                'tipo_dato': definicion.tipo_dato,
                'unidad_medida': definicion.unidad_medida,
                'es_requerido': definicion.es_requerido
            }

        return resultado

    def to_dict_completo(self):
        """
        Serializa el activo completo incluyendo atributos dinámicos.

        Returns:
            dict: Representación completa del activo con todos sus atributos
        """
        # Construir diccionario base con campos estándar
        data = {
            'id': self.id,
            'placa_codigo_interno': self.placa_codigo_interno,
            'nombre_activo': self.nombre_activo,
            'marca': self.marca,
            'modelo': self.modelo,
            'serie': self.serie,
            'valor_comercial': float(self.valor_comercial) if self.valor_comercial else 0.0,
            'valor_en_libros': float(self.valor_en_libros),
            'estado': self.estado,
            'fecha_ingreso': self.created_at.isoformat() if self.created_at else None,
            'ubicacion': self.ubicacion,
            'responsable': self.funcionario.nombre_completo if self.funcionario else None,
            'clase': self.clase.nombre_clase if self.clase else None,
            'estado_conciliacion': self.estado_conciliacion,
            'fecha_ultima_verificacion': self.fecha_ultima_verificacion.isoformat() if self.fecha_ultima_verificacion else None,
        }

        # Agregar información de categoría si existe
        if self.categoria:
            data['categoria'] = {
                'id': self.categoria.id,
                'nombre': self.categoria.nombre,
                'codigo': self.categoria.codigo
            }

            # Agregar atributos dinámicos
            data['atributos_dinamicos'] = self.get_atributos_dict()
        else:
            data['categoria'] = None
            data['atributos_dinamicos'] = {}

        return data


# ==============================================================================
# ACCESORIOS DE ACTIVO
# ==============================================================================
class ActivoAccesorio(db.Model):
    """Accesorios asociados permanentemente a un activo."""
    __tablename__ = 'activo_accesorios'

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='CASCADE'), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    serie = db.Column(db.String(100))

    # Relaciones
    activo = db.relationship('Activo', back_populates='accesorios_activo')

    def __repr__(self):
        return f'<ActivoAccesorio {self.descripcion}>'


# ==============================================================================
# HOJA DE VIDA BIOMEDICO
# ==============================================================================
class HojaVidaBiomedico(db.Model):
    __tablename__ = "hojas_vida_biomedicos"

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), nullable=False, unique=True)

    # ---------- Datos Generales ----------
    permiso_comercializacion = db.Column(db.String(100))
    n_factura = db.Column(db.String(100))
    n_orden_compra = db.Column(db.String(100))
    fecha_fabricacion = db.Column(db.DateTime)
    fecha_instalacion = db.Column(db.DateTime)

    # ---------- Datos de Adquisición ----------
    distribuidor = db.Column(db.String(150))
    forma_adquisicion = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    correo_electronico = db.Column(db.String(100))
    fecha_ingreso = db.Column(db.DateTime)
    vencimiento_garantia = db.Column(db.DateTime)
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

    # Archivos Digitales
    foto_url = db.Column(db.String(255))
    hoja_pdf_fisica_url = db.Column(db.String(255))

    # ---------- Relaciones ----------
    activo = db.relationship('Activo', back_populates='hoja_vida_biomedico')
    mantenimientos = db.relationship('MantenimientoBiomedico', back_populates='hoja_vida', lazy=True, cascade="all, delete")
    documentos = db.relationship('DocumentoAdjunto', back_populates='hoja_vida', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<HojaVidaBiomedico para activo_id={self.activo_id}>"

class HojaVidaEquipo(db.Model):
    """Hoja de vida para equipos no biomédicos (TICs, Electro-Industrial, Muebles y Enseres)."""
    __tablename__ = "hojas_vida_equipos"

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id'), nullable=False, unique=True)

    # ---------- Características Comerciales ----------
    proveedor_nombre = db.Column(db.String(200))
    fecha_adquisicion = db.Column(db.DateTime)
    costo_adquisicion = db.Column(db.Float)
    numero_factura = db.Column(db.String(100))
    numero_orden_compra = db.Column(db.String(100))
    garantia_meses = db.Column(db.Integer)
    fecha_vencimiento_garantia = db.Column(db.DateTime)
    vida_util_anios = db.Column(db.Integer)

    # ---------- Características Técnicas ----------
    voltaje = db.Column(db.String(50))
    potencia = db.Column(db.String(50))
    corriente = db.Column(db.String(50))
    frecuencia = db.Column(db.String(50))
    dimensiones = db.Column(db.String(100))
    peso = db.Column(db.String(50))
    color = db.Column(db.String(50))
    material = db.Column(db.String(100))

    # Manuales disponibles
    manual_usuario = db.Column(db.Boolean, default=False)
    manual_servicio = db.Column(db.Boolean, default=False)
    manual_instalacion = db.Column(db.Boolean, default=False)

    # ---------- Características Específicas (JSON para flexibilidad) ----------
    # Almacena atributos específicos según el tipo de equipo
    caracteristicas_especificas_json = db.Column(db.JSON, nullable=True)
    # Ejemplos:
    # TICs: {"sistema_operativo": "Windows 11", "procesador": "Intel i7", "ram": "16GB", "disco": "512GB SSD"}
    # Electro-Industrial: {"capacidad": "10 KVA", "tipo_combustible": "Diesel", "tipo_motor": "4 tiempos"}
    # Muebles: {"tipo_mueble": "Escritorio", "numero_cajones": "3", "acabado": "Melamina"}

    # ---------- Observaciones y Notas ----------
    observaciones_tecnicas = db.Column(db.Text)
    condiciones_uso = db.Column(db.Text)
    restricciones = db.Column(db.Text)

    # ---------- Archivos ----------
    foto_url = db.Column(db.String(500))
    foto_2_url = db.Column(db.String(500))
    foto_3_url = db.Column(db.String(500))

    # ---------- Auditoría ----------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    updated_by = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))

    # ---------- Relaciones ----------
    activo = db.relationship('Activo', backref=db.backref('hoja_vida_equipo', uselist=False, cascade='all, delete-orphan'))
    usuario_creador = db.relationship('User', foreign_keys=[created_by])
    usuario_actualizador = db.relationship('User', foreign_keys=[updated_by])

    def __repr__(self):
        return f"<HojaVidaEquipo para activo_id={self.activo_id}>"


class DocumentoAdjunto(db.Model):
    """
    FASE 1.3: Documentos adjuntos con integridad criptográfica.
    Ampliado para soportar documentos en activos, movimientos y hojas de vida biomédicas.
    """
    __tablename__ = 'documentos_adjuntos_biomedicos'

    id = db.Column(db.Integer, primary_key=True)

    # Relaciones polimórficas - el documento puede estar asociado a diferentes entidades
    hoja_vida_id = db.Column(db.Integer, db.ForeignKey('hojas_vida_biomedicos.id'), nullable=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='CASCADE'), nullable=True, index=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'), nullable=True, index=True)

    # Información del documento
    tipo_documento = db.Column(db.String(100), nullable=False, index=True)
    # Ejemplos: 'factura', 'calibracion', 'orden_compra', 'contrato', 'certificado', 'otro'
    ruta_archivo = db.Column(db.String(500), nullable=False)
    nombre_archivo_original = db.Column(db.String(200), nullable=True)  # Nombre original del archivo subido

    # FASE 1.3: Integridad criptográfica (No-repudiación del archivo)
    checksum_sha256 = db.Column(db.String(64), nullable=True, index=True)
    # El checksum garantiza que el archivo no ha sido modificado desde su carga
    # Crucial para auditorías legales y cumplimiento NIIF

    # Metadatos
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_carga_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    tamano_bytes = db.Column(db.Integer, nullable=True)  # Tamaño del archivo
    mime_type = db.Column(db.String(100), nullable=True)  # Tipo MIME del archivo

    # Relaciones
    hoja_vida = db.relationship('HojaVidaBiomedico', back_populates='documentos')
    usuario_carga = db.relationship('User', foreign_keys=[usuario_carga_id], backref='documentos_cargados')

    # Constraint: al menos una de las FK debe estar presente
    __table_args__ = (
        db.CheckConstraint(
            '(hoja_vida_id IS NOT NULL) OR (activo_id IS NOT NULL) OR (movimiento_id IS NOT NULL)',
            name='check_al_menos_una_relacion'
        ),
    )

    def __repr__(self):
        entidad = f"hoja_vida_id={self.hoja_vida_id}" if self.hoja_vida_id else \
                  f"activo_id={self.activo_id}" if self.activo_id else \
                  f"movimiento_id={self.movimiento_id}"
        return f'<DocumentoAdjunto {self.tipo_documento} para {entidad}>'

    def verificar_integridad(self, archivo_path):
        """
        Verifica que el checksum del archivo actual coincida con el almacenado.
        Retorna True si el archivo no ha sido modificado.
        """
        import hashlib
        if not self.checksum_sha256:
            return None  # No hay checksum para verificar

        sha256_hash = hashlib.sha256()
        try:
            with open(archivo_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest() == self.checksum_sha256
        except FileNotFoundError:
            return False

class MantenimientoBiomedico(db.Model):
    """Mantenimientos históricos específicos de una hoja de vida biomédica."""
    __tablename__ = 'mantenimientos_biomedicos'

    id = db.Column(db.Integer, primary_key=True)
    hoja_vida_id = db.Column(db.Integer, db.ForeignKey('hojas_vida_biomedicos.id'), nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    numero_reporte = db.Column(db.String(50))
    tipo_mtto = db.Column(db.String(100))
    actividad_observaciones = db.Column(db.Text)
    firma_responsable = db.Column(db.String(150))
    hoja_vida = db.relationship('HojaVidaBiomedico', back_populates='mantenimientos')
    documentos = db.relationship('MantenimientoBiomedicoDocumento', back_populates='mantenimiento',
                                 cascade='all, delete-orphan', lazy='dynamic',
                                 order_by='MantenimientoBiomedicoDocumento.uploaded_at.desc()')

    def __repr__(self):
        return f'<MantenimientoBiomedico {self.tipo_mtto} - {self.fecha}>'


class MantenimientoBiomedicoDocumento(db.Model):
    """Documentos escaneados para mantenimientos de equipos biomédicos."""
    __tablename__ = 'mantenimientos_biomedicos_documentos'

    id = db.Column(db.Integer, primary_key=True)
    mantenimiento_biomedico_id = db.Column(db.Integer, db.ForeignKey('mantenimientos_biomedicos.id', ondelete='CASCADE'),
                                           nullable=False, index=True)

    # Información del archivo
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    tipo_documento = db.Column(db.Enum('pdf', 'imagen', 'excel', 'word', 'otro', name='tipo_doc_biomedico_enum'),
                               default='pdf', nullable=False, index=True)
    tamano_archivo = db.Column(db.Integer)  # Bytes

    # Metadatos
    fecha_documento = db.Column(db.Date, index=True)
    descripcion = db.Column(db.Text)

    # Auditoría
    uploaded_by = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relaciones
    mantenimiento = db.relationship('MantenimientoBiomedico', back_populates='documentos')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def __repr__(self):
        return f'<MantenimientoBiomedicoDocumento id={self.id} mantenimiento_biomedico_id={self.mantenimiento_biomedico_id}>'




# ==============================================================================
# AUDITORÍA DE ACTIVOS (Legacy - Mantener por compatibilidad)
# ==============================================================================
class AuditoriaActivo(db.Model):
    """Registra todos los cambios de estado de activos."""
    __tablename__ = 'auditoria_activos'

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='CASCADE'), nullable=False)
    campo_modificado = db.Column(db.String(100), nullable=False)
    valor_anterior = db.Column(db.Text)
    valor_nuevo = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    fecha_cambio = db.Column(db.DateTime, server_default=db.func.now())

    # Relaciones
    activo = db.relationship('Activo', backref='historial_auditoria')
    usuario = db.relationship('User', backref='cambios_auditoria')

    def __repr__(self):
        return f'<AuditoriaActivo Activo:{self.activo_id} Campo:{self.campo_modificado} Fecha:{self.fecha_cambio}>'


# ==============================================================================
# FASE 1.2: AUDITORÍA HISTÓRICA COMPLETA (Trazabilidad Legal)
# ==============================================================================
class ActivoHistorico(db.Model):
    """
    Registro completo de auditoría para todos los cambios en activos.
    Cumple con NIIF para PYMES Sección 27 (Control Interno sobre Activos).
    Proporciona trazabilidad legal completa con información del usuario y timestamp.
    """
    __tablename__ = 'activo_historico'

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='CASCADE'),
                         nullable=False, index=True)

    # Información del cambio
    campo_modificado = db.Column(db.String(100), nullable=False, index=True)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_nuevo = db.Column(db.Text, nullable=True)

    # Auditoría de usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Información técnica de auditoría
    ip_address = db.Column(db.String(45), nullable=True)  # Soporta IPv4 e IPv6
    user_agent = db.Column(db.String(500), nullable=True)  # Navegador/dispositivo

    # Contexto del cambio
    tipo_operacion = db.Column(db.String(50), nullable=True)  # 'CREATE', 'UPDATE', 'DELETE', 'VERIFICACION'
    observaciones = db.Column(db.Text, nullable=True)

    # Relaciones
    activo = db.relationship('Activo', back_populates='historial')
    usuario = db.relationship('User', foreign_keys=[usuario_id], backref='historial_cambios_activos')

    # Índice compuesto para consultas eficientes por activo y fecha
    __table_args__ = (
        db.Index('idx_activo_timestamp', 'activo_id', 'timestamp'),
        db.Index('idx_campo_timestamp', 'campo_modificado', 'timestamp'),
    )

    def __repr__(self):
        return f'<ActivoHistorico Activo:{self.activo_id} Campo:{self.campo_modificado} {self.timestamp}>'

    def to_dict(self):
        """Serializa el registro de auditoría para API/reportes."""
        return {
            'id': self.id,
            'activo_id': self.activo_id,
            'campo_modificado': self.campo_modificado,
            'valor_anterior': self.valor_anterior,
            'valor_nuevo': self.valor_nuevo,
            'usuario': self.usuario.email if self.usuario else 'Sistema',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'tipo_operacion': self.tipo_operacion,
            'observaciones': self.observaciones
        }


# ==============================================================================
# AUDITORÍA DE MOVIMIENTOS
# ==============================================================================
class MovimientoHistorico(db.Model):
    """
    Registro completo de auditoría para todos los cambios en movimientos.
    Proporciona trazabilidad legal completa con información del usuario y timestamp.
    """
    __tablename__ = 'movimiento_historico'

    id = db.Column(db.Integer, primary_key=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             nullable=False, index=True)

    # Información del cambio
    campo_modificado = db.Column(db.String(100), nullable=False, index=True)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_nuevo = db.Column(db.Text, nullable=True)

    # Auditoría de usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Información técnica de auditoría
    ip_address = db.Column(db.String(45), nullable=True)  # Soporta IPv4 e IPv6
    user_agent = db.Column(db.String(500), nullable=True)  # Navegador/dispositivo

    # Contexto del cambio
    tipo_operacion = db.Column(db.String(50), nullable=True)  # 'CREATE', 'UPDATE', 'DELETE', 'APROBACION', 'RECHAZO'
    observaciones = db.Column(db.Text, nullable=True)

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='historial')
    usuario = db.relationship('User', foreign_keys=[usuario_id], backref='historial_cambios_movimientos')

    # Índice compuesto para consultas eficientes
    __table_args__ = (
        db.Index('idx_movimiento_timestamp', 'movimiento_id', 'timestamp'),
        db.Index('idx_campo_timestamp', 'campo_modificado', 'timestamp'),
    )

    def __repr__(self):
        return f'<MovimientoHistorico Movimiento:{self.movimiento_id} Campo:{self.campo_modificado} {self.timestamp}>'

    def to_dict(self):
        """Serializa el registro de auditoría para API/reportes."""
        return {
            'id': self.id,
            'movimiento_id': self.movimiento_id,
            'campo_modificado': self.campo_modificado,
            'valor_anterior': self.valor_anterior,
            'valor_nuevo': self.valor_nuevo,
            'usuario': self.usuario.email if self.usuario else 'Sistema',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'tipo_operacion': self.tipo_operacion,
            'observaciones': self.observaciones
        }


# ==============================================================================
# MOVIMIENTOS
# ==============================================================================
class Movimiento(db.Model):
    """Movimiento o acta de activos (Entrega, Traslado, Entrada/Salida, Paz y Salvo)."""
    __tablename__ = 'movimientos'

    id = db.Column(db.Integer, primary_key=True)
    tipo_movimiento = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, index=True)
    observaciones_generales = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id', ondelete='SET NULL'))

    # Estado de completitud del movimiento
    # Permite guardar movimientos incompletos como borradores
    estado_completitud = db.Column(db.String(20), default='completo', nullable=False, index=True)
    # Estados posibles: 'borrador', 'completo'

    # NIIF/NIC Compliance: Sistema de Aprobación y Segregación de Funciones
    # NIIF para PYMES, Sección 27: Control interno sobre activos
    estado_aprobacion = db.Column(db.String(20), default='Pendiente', nullable=False, index=True)
    # Estados posibles: 'Pendiente', 'Aprobado', 'Rechazado'
    aprobado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)
    motivo_rechazo = db.Column(db.Text)
    requiere_aprobacion = db.Column(db.Boolean, default=True, nullable=False)

    # --- RELACIONES ---
    # SQLAlchemy necesita que seamos explícitos cuando hay múltiples Foreign Keys a la misma tabla.
    # Relaciones
    usuario = db.relationship('User', foreign_keys=[usuario_id], back_populates='movimientos')
    aprobador = db.relationship('User', foreign_keys=[aprobado_por_id], back_populates='movimientos_aprobados')
    activos = db.relationship('MovimientoActivo', back_populates='movimiento',
                             cascade='all, delete-orphan', lazy=True)
    documentos_adjuntos = db.relationship('MovimientoDocumentoAdjunto', back_populates='movimiento',
                                         cascade='all, delete-orphan', lazy=True)
    firmas = db.relationship('Firma', cascade='all, delete-orphan', lazy=True,
                           foreign_keys='Firma.documento_id',
                           primaryjoin="and_(Movimiento.id==Firma.documento_id, Firma.tipo_documento=='movimiento')",
                           overlaps="firmas")

    # Auditoría histórica completa
    historial = db.relationship('MovimientoHistorico', back_populates='movimiento',
                               cascade='all, delete-orphan', lazy='dynamic',
                               order_by='MovimientoHistorico.timestamp.desc()')

    # Relaciones uno a uno con los detalles por tipo de movimiento
    detalle_entrega = db.relationship('DetalleEntrega', back_populates='movimiento',
                                     uselist=False, cascade='all, delete-orphan')
    detalle_traslado = db.relationship('DetalleTraslado', back_populates='movimiento',
                                      uselist=False, cascade='all, delete-orphan')
    detalle_entrada_salida = db.relationship('DetalleEntradaSalida', back_populates='movimiento',
                                            uselist=False, cascade='all, delete-orphan')
    detalle_paz_salvo = db.relationship('DetallePazSalvo', back_populates='movimiento',
                                       uselist=False, cascade='all, delete-orphan')
    detalle_reporte_dano_perdida = db.relationship('DetalleReporteDanoPerdida', back_populates='movimiento',
                                                   uselist=False, cascade='all, delete-orphan')
    detalle_comodato = db.relationship('DetalleComodato', back_populates='movimiento',
                                       uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Movimiento {self.tipo_movimiento} ({self.fecha})>'

    @classmethod
    def crear_desde_form(cls, data, getlist_func, usuario_actual):
        """
        Crea un nuevo movimiento y todos sus detalles asociados desde datos de formulario.
        Encapsula toda la lógica de negocio, lanzando excepciones en caso de error.
        """
        from flask import current_app
        import json
        from datetime import datetime
        from sqlalchemy import select, func

        try:
            tipo_movimiento_form = data.get('tipo_movimiento')
            if not tipo_movimiento_form:
                raise ValueError("El tipo de movimiento es requerido.")

            tipo_movimiento_db = 'Entrada/Salida' if tipo_movimiento_form in ['Entrada', 'Salida'] else tipo_movimiento_form

            fecha_form = data.get(f'fecha_{tipo_movimiento_form.lower()}')
            hora_form = data.get(f'hora_{tipo_movimiento_form.lower()}')
            fecha_movimiento_dt = datetime.now()
            if fecha_form and hora_form:
                fecha_movimiento_dt = datetime.strptime(f'{fecha_form} {hora_form}', '%Y-%m-%d %H:%M')
            elif fecha_form:
                fecha_movimiento_dt = datetime.strptime(fecha_form, '%Y-%m-%d')

            nuevo_movimiento = Movimiento(
                tipo_movimiento=tipo_movimiento_db,
                fecha=fecha_movimiento_dt,
                usuario_id=usuario_actual.id,
                observaciones_generales=data.get('observaciones_generales')
            )
            db.session.add(nuevo_movimiento)
            db.session.flush()
            movimiento_id = nuevo_movimiento.id
            
            activos_data = json.loads(data.get('activos_data', '[]'))
            accesorios_data = json.loads(data.get('accesorios_data', '{}'))
            firmas_data = json.loads(data.get('firmas_data', '{}'))

            valor_total_movimiento = 0.0
            for activo_info in activos_data:
                activo_id = activo_info.get('id')
                activo_obj = db.session.get(Activo, activo_id)
                if not activo_obj:
                    raise ValueError(f"Activo con ID {activo_id} no encontrado.")
                
                valor_total_movimiento += activo_obj.valor_en_libros
                movimiento_activo = MovimientoActivo(
                    movimiento_id=movimiento_id,
                    activo_id=activo_id,
                    valor_comercial_momento=activo_obj.valor_comercial_safe,
                    valor_libros_momento=activo_obj.valor_en_libros,
                    depreciacion_acumulada_momento=activo_obj.depreciacion_acumulada,
                    ubicacion_origen=activo_obj.ubicacion
                )
                db.session.add(movimiento_activo)
                db.session.flush()

                if str(activo_id) in accesorios_data:
                    for acc_info in accesorios_data[str(activo_id)]:
                        db.session.add(Accesorio(
                            movimiento_activo_id=movimiento_activo.id,
                            descripcion=acc_info.get('descripcion'),
                            cantidad=acc_info.get('cantidad')
                        ))

            UMBRAL_APROBACION = 5000000
            if valor_total_movimiento > UMBRAL_APROBACION:
                nuevo_movimiento.requiere_aprobacion = True
                nuevo_movimiento.estado_aprobacion = 'Pendiente'
            else:
                nuevo_movimiento.requiere_aprobacion = False
                nuevo_movimiento.estado_aprobacion = 'Aprobado'
                nuevo_movimiento.aprobado_por_id = usuario_actual.id
                nuevo_movimiento.fecha_aprobacion = datetime.now()

            # Lógica de detalles
            if tipo_movimiento_form == 'Entrega':
                fecha_oc_dt = None
                if data.get('entrega_contrato_fecha'):
                    fecha_oc_dt = datetime.strptime(data.get('entrega_contrato_fecha'), '%Y-%m-%d').date()
                
                proveedor_id_raw = data.get('proveedor_id')
                proveedor_id_final = None
                if proveedor_id_raw and proveedor_id_raw.strip():
                    if proveedor_id_raw.isdigit():
                        proveedor_id_final = int(proveedor_id_raw)
                    elif proveedor_id_raw.upper() == 'NO APLICA':
                        proveedor_id_final = db.session.scalar(select(Proveedor.id).filter(func.upper(Proveedor.razon_social) == 'NO APLICA'))

                detalle = DetalleEntrega(
                    movimiento_id=movimiento_id,
                    proveedor_id=proveedor_id_final,
                    factura=data.get('entrega_factura'),
                    orden_compra_contrato=data.get('entrega_contrato_nro'),
                    fecha_oc_contrato=fecha_oc_dt,
                    tipo_contrato=data.get('tipo_contrato'),
                    valor_contrato=float(data.get('valor_contrato')) if data.get('valor_contrato') and str(data.get('valor_contrato')).replace('.', '', 1).replace('-', '').isdigit() else None,
                    objeto_contrato=data.get('entrega_objeto_contrato'),
                    tipo_elementos=json.dumps(getlist_func('entrega_tipo_elementos')),
                    requiere_montaje='requiere_montaje' in data,
                    requiere_capacitacion='requiere_capacitacion' in data,
                    incluye_accesorios='incluye_accesorios' in data,
                    tipo_transporte=data.get('tipo_transporte'),
                    tipo_asignacion=data.get('tipo_asignacion'),
                    lugar_entrega_actual=data.get('lugar_entrega_actual'),
                    quien_entrega_nombre=data.get('entrega_responsable_nombre'),
                    quien_entrega_cedula=data.get('entrega_responsable_cc'),
                    quien_entrega_cargo=data.get('entrega_responsable_cargo'),
                    quien_entrega_area=data.get('entrega_responsable_area'),
                    quien_entrega_centro_costo=data.get('quien_entrega_centro_costo'),
                    quien_recibe_nombre=data.get('recibe_responsable_nombre'),
                    quien_recibe_cedula=data.get('recibe_responsable_cc'),
                    quien_recibe_cargo=data.get('recibe_responsable_cargo'),
                    quien_recibe_area=data.get('recibe_responsable_area'),
                    quien_recibe_centro_costo=data.get('recibe_responsable_centro_costo'),
                    garantia_meses=int(data.get('garantia_meses')) if data.get('garantia_meses') and data.get('garantia_meses').isdigit() else None
                )
                db.session.add(detalle)
            # Add other detail types here... (elif DetalleTraslado, etc.)
            
            for rol, firma_b64 in firmas_data.items():
                if firma_b64:
                    db.session.add(Firma(
                        documento_id=movimiento_id,
                        tipo_documento='movimiento',
                        rol_firma=rol,
                        firma_base64=firma_b64
                    ))

            db.session.commit()
            return nuevo_movimiento
        
        except (ValueError, json.JSONDecodeError) as e:
            db.session.rollback()
            current_app.logger.error(f"Error de validación o JSON creando movimiento: {e}")
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos creando movimiento: {e}")
            raise



# ==============================================================================
# MOVIMIENTO_ACTIVOS (Tabla intermedia)
# ==============================================================================
class MovimientoActivo(db.Model):
    """Relación entre un movimiento y los activos involucrados."""
    __tablename__ = 'movimiento_activos'

    id = db.Column(db.Integer, primary_key=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='RESTRICT'),
                         nullable=False, index=True)

    # NIIF/NIC Compliance: Snapshot del valor contable al momento del movimiento
    # NIC 16, párrafo 50: Debe revelarse el valor en libros en cada período
    valor_comercial_momento = db.Column(db.Float, default=0.0)
    valor_libros_momento = db.Column(db.Float, default=0.0)
    depreciacion_acumulada_momento = db.Column(db.Float, default=0.0)
    ubicacion_origen = db.Column(db.String(200))
    ubicacion_destino = db.Column(db.String(200))
    observaciones_contables = db.Column(db.Text)

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='activos')
    activo = db.relationship('Activo', back_populates='movimiento_activos')
    accesorios = db.relationship('Accesorio', back_populates='movimiento_activo',
                                cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<MovimientoActivo mov={self.movimiento_id} activo={self.activo_id}>'


# ==============================================================================
# ACCESORIOS (en un movimiento/acta)
# ==============================================================================
class Accesorio(db.Model):
    """Accesorios registrados en un movimiento específico."""
    __tablename__ = 'accesorios'

    id = db.Column(db.Integer, primary_key=True)
    movimiento_activo_id = db.Column(db.Integer,
                                    db.ForeignKey('movimiento_activos.id', ondelete='CASCADE'),
                                    nullable=False, index=True)
    descripcion = db.Column(db.String(200), nullable=False)
    referencia = db.Column(db.String(100))
    serial = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    observacion = db.Column(db.Text)

    # Relaciones
    movimiento_activo = db.relationship('MovimientoActivo', back_populates='accesorios')

    def __repr__(self):
        return f'<Accesorio {self.descripcion} (cant={self.cantidad})>'


# ==============================================================================
# FIRMAS
# ==============================================================================
class Firma(db.Model):
    """Firma digital asociada a documentos (movimientos o mantenimientos)."""
    __tablename__ = 'firmas'

    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, nullable=False, index=True)
    tipo_documento = db.Column(db.String(20), nullable=False)
    rol_firma = db.Column(db.String(50), nullable=False)
    firma_base64 = db.Column(LONGTEXT, nullable=False)  # Ahora guardará data:image/svg+xml

    # ✅ NUEVAS COLUMNAS DE AUDITORÍA - Implementación Firma Electrónica Simple
    # Conforme a Ley 527/1999 y Decreto 2364/2012 (Colombia)
    nombre_firmante = db.Column(db.String(200), nullable=True)  # ✅ NUEVO 2025-11-22: Nombre completo del firmante
    firma_svg = db.Column(db.Text, nullable=True)  # SVG como texto XML (firma vectorial)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 o IPv6 del firmante
    user_agent = db.Column(db.String(500), nullable=True)  # Navegador y dispositivo
    timestamp_firma = db.Column(db.DateTime, default=datetime.utcnow)  # Hora exacta de firma
    hash_documento = db.Column(db.String(64), nullable=True)  # SHA256 del documento
    consentimiento_aceptado = db.Column(db.Boolean, default=False)  # Consentimiento legal expreso

    # Constraint única compuesta
    __table_args__ = (
        db.UniqueConstraint('documento_id', 'tipo_documento', 'rol_firma',
                          name='_documento_tipo_rol_uc'),
    )

    # Relaciones polimórficas - sin back_populates para evitar conflictos
    # Las relaciones se definen desde Movimiento y Mantenimiento hacia Firma

    def __repr__(self):
        return f'<Firma {self.tipo_documento}:{self.documento_id} rol={self.rol_firma}>'


# ==============================================================================
# DOCUMENTOS ADJUNTOS
# ==============================================================================
class MovimientoDocumentoAdjunto(db.Model):
    """Documentos PDF adjuntos a movimientos."""
    __tablename__ = 'movimiento_documentos_adjuntos'

    id = db.Column(db.Integer, primary_key=True)
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                           nullable=False)
    nombre_documento = db.Column(db.String(200), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='documentos_adjuntos')

    def __repr__(self):
        return f'<MovimientoDocumentoAdjunto {self.nombre_documento}>'


# ==============================================================================
# DETALLES DE ENTREGA
# ==============================================================================
class DetalleEntrega(db.Model):
    """Detalles específicos de un movimiento tipo Entrega."""
    __tablename__ = 'detalles_entrega'

    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             primary_key=True, index=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id', ondelete='SET NULL'))
    factura = db.Column(db.String(100))
    orden_compra_contrato = db.Column(db.String(100))
    fecha_oc_contrato = db.Column(db.DateTime, nullable=True)
    tipo_contrato = db.Column(db.String(100))  # OPTIMIZADO: Tipo de contrato (Compra, Comodato, Arriendo, etc.)
    valor_contrato = db.Column(db.Float)  # OPTIMIZADO: Valor del contrato/factura
    objeto_contrato = db.Column(db.Text)
    tipo_elementos = db.Column(db.JSON, nullable=True)  # JSON - checkboxes de tipo de elemento
    requiere_montaje = db.Column(db.Boolean)
    requiere_capacitacion = db.Column(db.Boolean)
    incluye_accesorios = db.Column(db.Boolean)
    tipo_transporte = db.Column(db.String(100))  # OPTIMIZADO: Permanente u otro
    tipo_asignacion = db.Column(db.String(100))

    # Información de quien entrega
    lugar_entrega_actual = db.Column(db.String(200)) # OPTIMIZADO
    quien_entrega_nombre = db.Column(db.String(150))
    quien_entrega_cedula = db.Column(db.String(50))
    quien_entrega_cargo = db.Column(db.String(100))
    quien_entrega_area = db.Column(db.String(100))
    quien_entrega_centro_costo = db.Column(db.String(100))

    # Información de quien recibe
    quien_recibe_nombre = db.Column(db.String(150))
    quien_recibe_cedula = db.Column(db.String(50))
    quien_recibe_cargo = db.Column(db.String(100))
    quien_recibe_area = db.Column(db.String(100))
    quien_recibe_centro_costo = db.Column(db.String(100))
    garantia_meses = db.Column(db.Integer)

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='detalle_entrega')
    proveedor = db.relationship('Proveedor', back_populates='detalles_entrega')

    def __repr__(self):
        return f'<DetalleEntrega mov_id={self.movimiento_id}>'


# ==============================================================================
# DETALLES DE TRASLADO
# ==============================================================================
class DetalleTraslado(db.Model):
    """Detalles específicos de un movimiento tipo Traslado."""
    __tablename__ = 'detalles_traslado'

    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             primary_key=True, index=True)
    fecha_traslado = db.Column(db.DateTime, nullable=True)
    hora_traslado = db.Column(db.String(20))
    caracteristica = db.Column(db.String(100))
    lugar_destino = db.Column(db.String(200))
    tipo_traslado_json = db.Column(db.JSON, nullable=True)  # JSON array
    accesorios_generales_json = db.Column(db.JSON, nullable=True)  # Nuevo: JSON para accesorios generales
    ubicacion_inicial = db.Column(db.String(200))
    ubicacion_final = db.Column(db.String(200))
    origen_responsable_nombre = db.Column(db.String(150))
    origen_responsable_cc = db.Column(db.String(50))
    origen_responsable_cargo = db.Column(db.String(100))
    origen_area = db.Column(db.String(150))  # Nuevo
    origen_codigo_costo = db.Column(db.String(100))  # Nuevo
    origen_centro_costo = db.Column(db.String(150))  # Nuevo
    nuevo_responsable_nombre = db.Column(db.String(150))
    nuevo_responsable_cc = db.Column(db.String(50))
    nuevo_responsable_cargo = db.Column(db.String(100))
    destino_area = db.Column(db.String(150))  # Nuevo
    destino_codigo_costo = db.Column(db.String(100))  # Nuevo
    destino_centro_costo = db.Column(db.String(150))  # Nuevo
    estado_activo = db.Column(db.String(50))

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='detalle_traslado')

    def __repr__(self):
        return f'<DetalleTraslado mov_id={self.movimiento_id}>'


# ==============================================================================
# TERCEROS (Para Movimientos de Entrada/Salida)
# ==============================================================================
class Tercero(db.Model):
    """
    Terceros (personas o entidades) para movimientos de entrada/salida.
    Permite reutilizar datos de terceros frecuentes (pacientes, empresas, etc.)
    """
    __tablename__ = 'terceros'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False, index=True)
    # Tipos: "Persona Natural", "Paciente", "Empresa", "Institución"
    nombre_completo = db.Column(db.String(200), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    # Tipos: "CC", "NIT", "CE", "Pasaporte"
    numero_documento = db.Column(db.String(50), nullable=False)
    direccion = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Serializa el tercero para JSON/API"""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'nombre_completo': self.nombre_completo,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'observaciones': self.observaciones,
            'activo': self.activo
        }

    def __repr__(self):
        return f'<Tercero {self.nombre_completo} ({self.numero_documento})>'


# ==============================================================================
# DETALLES DE ENTRADA/SALIDA
# ==============================================================================
class DetalleEntradaSalida(db.Model):
    """Detalles específicos de un movimiento tipo Entrada/Salida."""
    __tablename__ = 'detalles_entrada_salida'

    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             primary_key=True, index=True)

    # FK opcional a Tercero (si se usa un tercero registrado)
    tercero_id = db.Column(db.Integer, db.ForeignKey('terceros.id', ondelete='SET NULL'), nullable=True, index=True)

    ciudad = db.Column(db.String(100), nullable=True)
    sede = db.Column(db.String(100), nullable=True)
    solicitante_responsable_nombre = db.Column(db.String(150), nullable=True)
    solicitante_responsable_cc = db.Column(db.String(50), nullable=True)
    solicitante_responsable_cargo_area = db.Column(db.String(150))

    # Datos del tercero (pueden venir de Tercero o ser ingresados manualmente)
    tercero_entidad_persona = db.Column(db.String(200))
    tercero_nit_cc = db.Column(db.String(50))
    tercero_direccion = db.Column(db.String(200))
    tercero_movil = db.Column(db.String(50))

    tipo_operacion = db.Column(db.String(20), nullable=True)  # Nullable para borradores
    motivo = db.Column(db.Text, nullable=True)  # Nullable para borradores
    motivo_otro = db.Column(db.Text)  # Nuevo
    fecha_retorno_estimada = db.Column(db.DateTime, nullable=True)
    accesorios_generales = db.Column(db.String(200), nullable=True)  # Campo de texto para describir accesorios
    autorizado_por_nombre = db.Column(db.String(150))
    autorizado_por_cargo = db.Column(db.String(100))

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='detalle_entrada_salida')
    tercero = db.relationship('Tercero', backref='movimientos_entrada_salida')

    def __repr__(self):
        return f'<DetalleEntradaSalida mov_id={self.movimiento_id} tipo={self.tipo_operacion}>'


# ==============================================================================
# DETALLES DE PAZ Y SALVO
# ==============================================================================
class DetallePazSalvo(db.Model):
    """Detalles específicos de un movimiento tipo Paz y Salvo."""
    __tablename__ = 'detalles_paz_salvo'

    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             primary_key=True, index=True)
    funcionario_desvinculado_id = db.Column(db.Integer,
                                           db.ForeignKey('funcionarios.id', ondelete='RESTRICT'),
                                           nullable=False)
    observaciones_paz_salvo = db.Column(db.Text)

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='detalle_paz_salvo')
    funcionario_desvinculado = db.relationship('Funcionario', back_populates='detalles_paz_salvo')

    def __repr__(self):
        return f'<DetallePazSalvo mov_id={self.movimiento_id}>'


class DetalleReporteDanoPerdida(db.Model):
    """Detalles específicos de un movimiento tipo Reporte de Daño o Pérdida."""
    __tablename__ = 'detalles_reporte_dano_perdida'

    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             primary_key=True, index=True)

    # Tipo de reporte
    reporte_tipo = db.Column(db.String(50), nullable=False)  # 'Daño' o 'Pérdida'

    # Fecha y ubicación del incidente
    fecha_incidente = db.Column(db.Date, nullable=False)
    hora_incidente = db.Column(db.String(10))
    area_incidente = db.Column(db.String(200), nullable=False)
    ubicacion_especifica = db.Column(db.String(200))

    # Descripción del incidente
    descripcion_incidente = db.Column(db.Text, nullable=False)
    causas_incidente = db.Column(db.Text)  # Almacena las causas separadas por comas

    # Estado del activo
    estado_activo = db.Column(db.String(50), nullable=False)
    requiere_reparacion = db.Column(db.String(10))

    # Información adicional
    costo_estimado = db.Column(db.Numeric(15, 2))
    garantia_vigente = db.Column(db.String(10))

    # Datos de quien reporta
    responsable_reporte_nombre = db.Column(db.String(200), nullable=False)
    responsable_reporte_cc = db.Column(db.String(50), nullable=False)
    responsable_reporte_cargo = db.Column(db.String(100), nullable=False)
    responsable_reporte_area = db.Column(db.String(100), nullable=False)
    responsable_reporte_telefono = db.Column(db.String(50))
    responsable_reporte_email = db.Column(db.String(100))

    # Acciones y observaciones
    acciones_tomadas = db.Column(db.Text)
    observaciones_adicionales = db.Column(db.Text)

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='detalle_reporte_dano_perdida')

    def __repr__(self):
        return f'<DetalleReporteDanoPerdida mov_id={self.movimiento_id} tipo={self.reporte_tipo}>'


# ==============================================================================
# DETALLES DE COMODATO
# ==============================================================================
class DetalleComodato(db.Model):
    """
    Detalles específicos de un movimiento tipo Comodato.

    FUNDAMENTO LEGAL Y CONTABLE:
    - Contrato de préstamo gratuito (Art. 2200 Código Civil Colombiano)
    - No genera propiedad ni depreciación en libros del comodatario
    - Revelación en notas a estados financieros (NIIF para PYMES, Sección 20)
    - Control y custodia bajo responsabilidad del comodatario
    - Obligación de devolución en las mismas condiciones
    """
    __tablename__ = 'detalles_comodato'

    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id', ondelete='CASCADE'),
                             primary_key=True, index=True)

    # ===== DATOS DEL COMODANTE (Quien presta) =====
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id', ondelete='SET NULL'),
                            nullable=True, index=True)
    comodante_nombre = db.Column(db.String(200), nullable=False)
    comodante_nit = db.Column(db.String(50), nullable=False)
    comodante_direccion = db.Column(db.String(200))
    comodante_telefono = db.Column(db.String(50))
    comodante_email = db.Column(db.String(100))
    comodante_representante = db.Column(db.String(200))  # Representante legal
    comodante_cedula_representante = db.Column(db.String(50))

    # ===== DATOS DEL COMODATARIO (Quien recibe - La Institución) =====
    comodatario_nombre = db.Column(db.String(200), nullable=False)  # Nombre institución
    comodatario_nit = db.Column(db.String(50), nullable=False)
    comodatario_direccion = db.Column(db.String(200))
    comodatario_representante = db.Column(db.String(200))  # Representante legal
    comodatario_cedula_representante = db.Column(db.String(50))

    # ===== INFORMACIÓN DEL CONTRATO =====
    numero_contrato = db.Column(db.String(100), nullable=False, index=True)
    fecha_inicio = db.Column(db.Date, nullable=False, index=True)
    fecha_fin = db.Column(db.Date, nullable=False, index=True)
    plazo_meses = db.Column(db.Integer)  # Duración en meses (calculado)
    renovacion_automatica = db.Column(db.Boolean, default=False)  # ¿Se renueva automáticamente?
    objeto_comodato = db.Column(db.Text, nullable=False)  # Descripción detallada del objeto

    # ===== CONDICIONES DEL COMODATO =====
    uso_permitido = db.Column(db.Text)  # Uso específico permitido del bien
    restricciones = db.Column(db.Text)  # Restricciones de uso
    mantenimiento_cargo = db.Column(db.String(100))  # "Comodante", "Comodatario", "Compartido"
    seguros_cargo = db.Column(db.String(100))  # "Comodante", "Comodatario", "Compartido"

    # ===== CONDICIONES DE DEVOLUCIÓN =====
    condiciones_devolucion = db.Column(db.Text)
    lugar_devolucion = db.Column(db.String(200))
    requiere_verificacion_tecnica = db.Column(db.Boolean, default=False)

    # ===== VALOR REFERENCIAL (para seguros) =====
    valor_comercial_referencial = db.Column(db.Float)  # Valor estimado del bien (no contable)

    # ===== UBICACIÓN Y RESPONSABLE =====
    ubicacion_bien = db.Column(db.String(200), nullable=False)  # Dónde se ubicará físicamente
    responsable_interno_nombre = db.Column(db.String(150), nullable=False)
    responsable_interno_cedula = db.Column(db.String(50), nullable=False)
    responsable_interno_cargo = db.Column(db.String(100))
    responsable_interno_area = db.Column(db.String(100))
    responsable_interno_telefono = db.Column(db.String(50))
    responsable_interno_email = db.Column(db.String(100))

    # ===== INFORMACIÓN ADICIONAL =====
    incluye_capacitacion = db.Column(db.Boolean, default=False)
    incluye_mantenimiento_preventivo = db.Column(db.Boolean, default=False)
    incluye_soporte_tecnico = db.Column(db.Boolean, default=False)
    observaciones_adicionales = db.Column(db.Text)

    # ===== ESTADO DEL COMODATO =====
    estado_comodato = db.Column(db.String(50), default='Vigente', nullable=False, index=True)
    # Estados posibles: 'Vigente', 'Vencido', 'Renovado', 'Terminado anticipadamente', 'Devuelto'

    # ===== RENOVACIONES (Historial) =====
    renovaciones_json = db.Column(db.JSON, nullable=True)
    # Almacena historial de renovaciones: [{"fecha": "2024-01-01", "fecha_fin": "2025-01-01"}]

    # Relaciones
    movimiento = db.relationship('Movimiento', back_populates='detalle_comodato')
    proveedor = db.relationship('Proveedor', foreign_keys=[proveedor_id])

    def __repr__(self):
        return f'<DetalleComodato mov_id={self.movimiento_id} contrato={self.numero_contrato}>'

    @property
    def dias_para_vencimiento(self):
        """Calcula los días restantes hasta el vencimiento del comodato."""
        from datetime import date
        if self.fecha_fin:
            delta = self.fecha_fin - date.today()
            return delta.days
        return None

    @property
    def esta_vencido(self):
        """Verifica si el comodato está vencido."""
        from datetime import date
        if self.fecha_fin:
            return date.today() > self.fecha_fin
        return False

    @property
    def esta_proximo_a_vencer(self, dias_alerta=30):
        """Verifica si el comodato está próximo a vencer (dentro de los próximos N días)."""
        dias = self.dias_para_vencimiento
        if dias is not None:
            return 0 < dias <= dias_alerta
        return False


# TIPOS DE MANTENIMIENTO

class MantenimientoTipo(db.Model):
    """Tipos de mantenimiento (Preventivo, Correctivo, Calibración, etc.)."""
    __tablename__ = 'mantenimiento_tipos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

    # Relaciones
    mantenimientos = db.relationship('Mantenimiento', back_populates='tipo', lazy=True)

    def __repr__(self):
        return f'<MantenimientoTipo {self.nombre}>'



# MANTENIMIENTOS

class Mantenimiento(db.Model):
    """Registro de mantenimiento de un activo."""
    __tablename__ = 'mantenimientos'

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('mantenimiento_tipos.id'),
                       nullable=False, index=True)
    fecha_mantenimiento = db.Column(db.DateTime, nullable=False)
    duracion_minutos = db.Column(db.Integer)
    observaciones = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='Pendiente')
    atributos_reporte_json = db.Column(db.JSON, nullable=True)

    # Relaciones
    activo = db.relationship('Activo', back_populates='mantenimientos')
    tipo = db.relationship('MantenimientoTipo', back_populates='mantenimientos')
    usuario = db.relationship('User', back_populates='mantenimientos')
    fotos = db.relationship('MantenimientoFoto', back_populates='mantenimiento',
                           cascade='all, delete-orphan', lazy=True)
    documentos = db.relationship('MantenimientoDocumento', back_populates='mantenimiento',
                                cascade='all, delete-orphan', lazy=True,
                                order_by='MantenimientoDocumento.uploaded_at.desc()')
    firmas = db.relationship('Firma', cascade='all, delete-orphan', lazy=True,
                           foreign_keys='Firma.documento_id',
                           primaryjoin="and_(Mantenimiento.id==Firma.documento_id, Firma.tipo_documento=='mantenimiento')",
                           overlaps="firmas")

    def __repr__(self):
        return f'<Mantenimiento activo={self.activo_id} fecha={self.fecha_mantenimiento}>'


# ==============================================================================
# FOTOS DE MANTENIMIENTO
# ==============================================================================
class MantenimientoFoto(db.Model):
    """Fotos adjuntas a un mantenimiento."""
    __tablename__ = 'mantenimiento_fotos'

    id = db.Column(db.Integer, primary_key=True)
    mantenimiento_id = db.Column(db.Integer,
                                db.ForeignKey('mantenimientos.id', ondelete='CASCADE'),
                                nullable=False, index=True)
    ruta_foto = db.Column(db.String(500), nullable=False)
    descripcion = db.Column(db.String(200))

    # Relaciones
    mantenimiento = db.relationship('Mantenimiento', back_populates='fotos')

    def __repr__(self):
        return f'<MantenimientoFoto mantenimiento={self.mantenimiento_id}>'


# ==============================================================================
# DOCUMENTOS DE MANTENIMIENTO (PDFs ESCANEADOS)
# ==============================================================================
class MantenimientoDocumento(db.Model):
    """
    Documentos escaneados de mantenimientos físicos realizados.
    Compatible con módulos de mantenimientos no biomédicos y biomédicos.
    """
    __tablename__ = 'mantenimientos_documentos'

    id = db.Column(db.Integer, primary_key=True)
    mantenimiento_id = db.Column(db.Integer,
                                 db.ForeignKey('mantenimientos.id', ondelete='CASCADE'),
                                 nullable=False, index=True)

    # Información del archivo
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    tipo_documento = db.Column(db.Enum('pdf', 'imagen', 'excel', 'word', 'otro', name='tipo_documento_enum'),
                               default='pdf', nullable=False, index=True)
    tamano_archivo = db.Column(db.Integer)  # Bytes

    # Metadatos del mantenimiento escaneado
    fecha_documento = db.Column(db.Date, index=True,
                               comment='Fecha del mantenimiento físico escaneado')
    tecnico_responsable = db.Column(db.String(200),
                                   comment='Técnico que realizó el mantenimiento')
    descripcion = db.Column(db.Text)

    # Auditoría
    uploaded_by = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    mantenimiento = db.relationship('Mantenimiento', back_populates='documentos')
    # uploader = db.relationship('User', foreign_keys=[uploaded_by])  # Activar después de crear la tabla en BD

    def __repr__(self):
        return f'<MantenimientoDocumento id={self.id} mantenimiento={self.mantenimiento_id} tipo={self.tipo_documento}>'

    @property
    def extension(self):
        """Retorna la extensión del archivo."""
        return self.nombre_archivo.rsplit('.', 1)[-1].lower() if '.' in self.nombre_archivo else ''

    @property
    def tamano_mb(self):
        """Retorna el tamaño en MB."""
        return round(self.tamano_archivo / (1024 * 1024), 2) if self.tamano_archivo else 0

    @property
    def es_pdf(self):
        """Verifica si es un PDF."""
        return self.tipo_documento == 'pdf' or self.extension == 'pdf'

    @property
    def es_imagen(self):
        """Verifica si es una imagen."""
        return self.tipo_documento == 'imagen' or self.extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']


# ==============================================================================
# FASE 2.1: ATRIBUTOS DINÁMICOS (EAV MEJORADO)
# ==============================================================================
"""
Sistema Entity-Attribute-Value (EAV) Mejorado para gestión de atributos
personalizados por categoría de activo.

Permite definir plantillas de atributos con validación de tipos para diferentes
categorías (Biomédicos, Informáticos, Mobiliario, etc.)
"""

class CategoriaActivo(db.Model):
    """
    Categorías de activos para agrupar por tipo y asociar plantillas de atributos.

    Ejemplos: Equipos Biomédicos, Equipos Informáticos, Mobiliario, Vehículos.
    """
    __tablename__ = 'categoria_activo'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    icono = db.Column(db.String(50), nullable=True)  # FontAwesome icon name
    activa = db.Column(db.Boolean, default=True, nullable=False, index=True)
    orden_visualizacion = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    activos = db.relationship('Activo', back_populates='categoria', lazy='dynamic')
    atributos_definicion = db.relationship(
        'AtributoDefinicion',
        back_populates='categoria',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='AtributoDefinicion.orden_visualizacion'
    )

    def __repr__(self):
        return f'<CategoriaActivo {self.codigo}: {self.nombre}>'

    def to_dict(self):
        """Serializa la categoría para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'icono': self.icono,
            'activa': self.activa,
            'orden_visualizacion': self.orden_visualizacion,
            'total_activos': self.activos.count(),
            'total_atributos': self.atributos_definicion.filter_by(activo=True).count()
        }

    @staticmethod
    def get_activas():
        """Retorna categorías activas ordenadas"""
        return CategoriaActivo.query.filter_by(activa=True).order_by(
            CategoriaActivo.orden_visualizacion,
            CategoriaActivo.nombre
        ).all()


class AtributoDefinicion(db.Model):
    """
    Definición de atributos personalizados para categorías de activos.

    Define qué atributos están disponibles para cada categoría,
    su tipo de dato, validaciones y opciones.
    """
    __tablename__ = 'atributo_definicion'

    # Tipos de datos soportados
    TIPO_TEXTO = 'texto'
    TIPO_NUMERO = 'numero'
    TIPO_FECHA = 'fecha'
    TIPO_BOOLEANO = 'booleano'
    TIPO_LISTA = 'lista'
    TIPO_TEXTO_LARGO = 'texto_largo'

    TIPOS_DATOS = [
        TIPO_TEXTO,
        TIPO_NUMERO,
        TIPO_FECHA,
        TIPO_BOOLEANO,
        TIPO_LISTA,
        TIPO_TEXTO_LARGO
    ]

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_activo.id', ondelete='CASCADE'), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)  # snake_case
    etiqueta = db.Column(db.String(150), nullable=False)  # Para UI
    descripcion = db.Column(db.Text, nullable=True)
    tipo_dato = db.Column(db.String(20), nullable=False)
    es_requerido = db.Column(db.Boolean, default=False, nullable=False)
    unidad_medida = db.Column(db.String(50), nullable=True)
    opciones_json = db.Column(db.Text, nullable=True)  # JSON string
    valor_por_defecto = db.Column(db.String(255), nullable=True)
    orden_visualizacion = db.Column(db.Integer, default=0, index=True)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    validacion_regex = db.Column(db.String(255), nullable=True)
    mensaje_ayuda = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    categoria = db.relationship('CategoriaActivo', back_populates='atributos_definicion')
    valores = db.relationship(
        'AtributoValor',
        back_populates='definicion',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # Constraint único
    __table_args__ = (
        db.UniqueConstraint('categoria_id', 'nombre', name='uk_categoria_nombre'),
    )

    def __repr__(self):
        return f'<AtributoDefinicion {self.nombre} ({self.tipo_dato})>'

    @property
    def opciones(self):
        """Retorna opciones parseadas desde JSON"""
        if self.opciones_json and self.tipo_dato == self.TIPO_LISTA:
            try:
                return json.loads(self.opciones_json)
            except:
                return []
        return None

    @opciones.setter
    def opciones(self, value):
        """Guarda opciones como JSON"""
        if value:
            self.opciones_json = json.dumps(value, ensure_ascii=False)
        else:
            self.opciones_json = None

    def validar_valor(self, valor):
        """
        Valida que un valor sea compatible con el tipo de dato definido.

        Args:
            valor: El valor a validar

        Returns:
            tuple: (es_valido: bool, mensaje_error: str or None)
        """
        if valor is None or valor == '':
            if self.es_requerido:
                return False, f'El campo {self.etiqueta} es requerido'
            return True, None

        # Validación por tipo
        if self.tipo_dato == self.TIPO_NUMERO:
            try:
                float(valor)
            except (ValueError, TypeError):
                return False, f'{self.etiqueta} debe ser un número válido'

        elif self.tipo_dato == self.TIPO_FECHA:
            if not isinstance(valor, (date, datetime)):
                try:
                    datetime.strptime(str(valor), '%Y-%m-%d')
                except ValueError:
                    return False, f'{self.etiqueta} debe ser una fecha válida (YYYY-MM-DD)'

        elif self.tipo_dato == self.TIPO_BOOLEANO:
            if not isinstance(valor, bool) and valor not in ['true', 'false', '1', '0', 1, 0]:
                return False, f'{self.etiqueta} debe ser verdadero o falso'

        elif self.tipo_dato == self.TIPO_LISTA:
            opciones = self.opciones
            if opciones and valor not in opciones:
                return False, f'{self.etiqueta} debe ser una de las opciones válidas: {", ".join(opciones)}'

        # Validación regex adicional
        if self.validacion_regex and self.tipo_dato in [self.TIPO_TEXTO, self.TIPO_TEXTO_LARGO]:
            import re
            if not re.match(self.validacion_regex, str(valor)):
                return False, f'{self.etiqueta} no cumple el formato requerido'

        return True, None

    def to_dict(self, incluir_valores=False):
        """Serializa la definición para JSON"""
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'etiqueta': self.etiqueta,
            'descripcion': self.descripcion,
            'tipo_dato': self.tipo_dato,
            'es_requerido': self.es_requerido,
            'unidad_medida': self.unidad_medida,
            'opciones': self.opciones,
            'valor_por_defecto': self.valor_por_defecto,
            'orden_visualizacion': self.orden_visualizacion,
            'activo': self.activo,
            'mensaje_ayuda': self.mensaje_ayuda
        }

        if incluir_valores:
            data['total_valores'] = self.valores.count()

        return data


class AtributoValor(db.Model):
    """
    Valores concretos de atributos personalizados para activos específicos.

    Implementa patrón EAV (Entity-Attribute-Value) con columnas tipadas
    para optimizar búsquedas y almacenamiento.
    """
    __tablename__ = 'atributo_valor'

    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activos.id', ondelete='CASCADE'), nullable=False, index=True)
    atributo_definicion_id = db.Column(
        db.Integer,
        db.ForeignKey('atributo_definicion.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )

    # Columnas tipadas para valores (solo una debe tener valor según tipo_dato)
    valor_texto = db.Column(db.String(500), nullable=True)
    valor_numerico = db.Column(db.Numeric(15, 4), nullable=True, index=True)
    valor_fecha = db.Column(db.Date, nullable=True, index=True)
    valor_booleano = db.Column(db.Boolean, nullable=True, index=True)
    valor_texto_largo = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)

    # Relaciones
    activo = db.relationship('Activo', back_populates='atributos_valores')
    definicion = db.relationship('AtributoDefinicion', back_populates='valores')
    usuario = db.relationship('User', foreign_keys=[updated_by])

    # Constraint único: un activo solo puede tener un valor por atributo
    __table_args__ = (
        db.UniqueConstraint('activo_id', 'atributo_definicion_id', name='uk_activo_atributo'),
        db.Index('idx_definicion_numero', 'atributo_definicion_id', 'valor_numerico'),
        db.Index('idx_definicion_booleano', 'atributo_definicion_id', 'valor_booleano'),
    )

    def __repr__(self):
        return f'<AtributoValor activo={self.activo_id} atributo={self.definicion.nombre if self.definicion else "?"}>'

    @property
    def valor(self):
        """Retorna el valor apropiado según el tipo de dato de la definición"""
        if not self.definicion:
            return None

        tipo = self.definicion.tipo_dato

        if tipo == AtributoDefinicion.TIPO_NUMERO:
            return float(self.valor_numerico) if self.valor_numerico is not None else None
        elif tipo == AtributoDefinicion.TIPO_FECHA:
            return self.valor_fecha
        elif tipo == AtributoDefinicion.TIPO_BOOLEANO:
            return self.valor_booleano
        elif tipo == AtributoDefinicion.TIPO_TEXTO_LARGO:
            return self.valor_texto_largo
        else:  # TIPO_TEXTO o TIPO_LISTA
            return self.valor_texto

    @valor.setter
    def valor(self, nuevo_valor):
        """Asigna el valor a la columna apropiada según el tipo de dato"""
        if not self.definicion:
            raise ValueError("Debe establecer definicion antes de asignar valor")

        tipo = self.definicion.tipo_dato

        # Limpiar todas las columnas primero
        self.valor_texto = None
        self.valor_numerico = None
        self.valor_fecha = None
        self.valor_booleano = None
        self.valor_texto_largo = None

        # Asignar a la columna correcta
        if nuevo_valor is None or nuevo_valor == '':
            return

        if tipo == AtributoDefinicion.TIPO_NUMERO:
            self.valor_numerico = float(nuevo_valor)
        elif tipo == AtributoDefinicion.TIPO_FECHA:
            if isinstance(nuevo_valor, str):
                self.valor_fecha = datetime.strptime(nuevo_valor, '%Y-%m-%d').date()
            else:
                self.valor_fecha = nuevo_valor
        elif tipo == AtributoDefinicion.TIPO_BOOLEANO:
            if isinstance(nuevo_valor, str):
                self.valor_booleano = nuevo_valor.lower() in ['true', '1', 'yes', 'si']
            else:
                self.valor_booleano = bool(nuevo_valor)
        elif tipo == AtributoDefinicion.TIPO_TEXTO_LARGO:
            self.valor_texto_largo = str(nuevo_valor)
        else:  # TIPO_TEXTO o TIPO_LISTA
            self.valor_texto = str(nuevo_valor)

    def to_dict(self):
        """Serializa el valor para JSON"""
        return {
            'id': self.id,
            'atributo_nombre': self.definicion.nombre if self.definicion else None,
            'atributo_etiqueta': self.definicion.etiqueta if self.definicion else None,
            'tipo_dato': self.definicion.tipo_dato if self.definicion else None,
            'valor': self.valor,
            'unidad_medida': self.definicion.unidad_medida if self.definicion else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.usuario.email if self.usuario else None
        }


# ==============================================================================
# TRIGGERS COMO SQLAlchemy EVENTS
# ==============================================================================
"""
SQLAlchemy Events actúan como triggers de base de datos a nivel de aplicación.
Estos eventos se ejecutan automáticamente cuando ocurren ciertos cambios.
"""
from sqlalchemy import event, inspect
from sqlalchemy.orm.attributes import PASSIVE_NO_RESULT, flag_modified # Import here for use in trigger
from sqlalchemy.orm.base import LoaderCallableStatus

# TRIGGER 1: Actualizar estado y responsable de activo al entregarlo
# ==============================================================================
@event.listens_for(DetalleEntrega, 'after_insert')
def actualizar_estado_activo_entrega(mapper, connection, target):
    """
    Cuando se crea un DetalleEntrega, actualizar el estado de los activos
    involucrados a 'Operativo' y asignarlos al funcionario receptor si aplica.
    """
    from sqlalchemy.orm import Session
    session = Session(bind=connection)

    try:
        # Obtener movimiento y funcionario responsable del movimiento general
        movimiento = session.get(Movimiento, target.movimiento_id)
        if not movimiento:
            return

        funcionario_id_receptor = movimiento.funcionario_id

        # Actualizar estado y responsable de todos los activos involucrados
        for ma in movimiento.activos:
            activo = session.get(Activo, ma.activo_id)
            if activo:
                # Cambia el estado a 'Operativo' o 'Asignado' según la lógica de negocio
                activo.estado = 'Operativo'
                if funcionario_id_receptor:
                    activo.funcionario_id = funcionario_id_receptor

        session.commit()
    except Exception as e:
        print(f"[TRIGGER ERROR] actualizar_estado_activo_entrega: {e}")
        session.rollback()
    finally:
        session.close()


# TRIGGER 1: Actualizar ubicación de activo al trasladarlo
# ==============================================================================
@event.listens_for(DetalleTraslado, 'after_insert')
def actualizar_ubicacion_activo_traslado(mapper, connection, target):
    """
    Cuando se crea un DetalleTraslado, actualizar la ubicación de los activos
    a la ubicación final del traslado.
    """
    from sqlalchemy.orm import Session
    session = Session(bind=connection)

    try:
        # Obtener movimiento
        movimiento = session.get(Movimiento, target.movimiento_id)
        if not movimiento or not target.ubicacion_final:
            return

        # Buscar el ID del nuevo funcionario responsable si se proporcionó un CC
        nuevo_responsable_id = None
        if target.nuevo_responsable_cc:
            funcionario = session.query(Funcionario).filter_by(cedula=target.nuevo_responsable_cc).first()
            if funcionario:
                nuevo_responsable_id = funcionario.id

        # Actualizar ubicación y responsable de todos los activos involucrados
        for ma in movimiento.activos:
            activo = session.get(Activo, ma.activo_id)
            if activo:
                activo.ubicacion = target.ubicacion_final
                if nuevo_responsable_id:
                    activo.funcionario_id = nuevo_responsable_id
                # Si no se encuentra por CC pero el movimiento tiene un funcionario_id general, usar ese
                elif movimiento.funcionario_id:
                    activo.funcionario_id = movimiento.funcionario_id

        session.commit()
    except Exception as e:
        print(f"[TRIGGER ERROR] actualizar_ubicacion_activo_traslado: {e}")
        session.rollback()
    finally:
        session.close()


# TRIGGER 2: Actualizar último mantenimiento en Activo
# ==============================================================================
@event.listens_for(Mantenimiento, 'after_insert')
@event.listens_for(Mantenimiento, 'after_update')
def actualizar_ultimo_mantenimiento_activo(mapper, connection, target):
    """
    Cuando se crea o actualiza un Mantenimiento completado, actualizar el campo
    de último mantenimiento en los atributos dinámicos del activo.
    """
    if target.estado != 'Completado':
        return

    from sqlalchemy.orm import Session
    session = Session(bind=connection)

    try:
        activo = session.get(Activo, target.activo_id)
        if activo:
            # Obtener el usuario actual para la auditoría
            usuario_id = None
            try:
                if current_user and current_user.is_authenticated:
                    usuario_id = current_user.id
            except: # Fuera de un contexto de request
                pass

            # Usar el método del modelo que ya incluye validación y auditoría
            # Esto actualiza el sistema EAV nuevo
            activo.set_atributo_valor('ultimo_mantenimiento', target.fecha_mantenimiento, usuario_id=usuario_id)

            # --- Mantenimiento del sistema JSON legado (transitorio) ---
            # Aunque el objetivo es eliminarlo, se mantiene sincronizado por ahora.
            # Nota: El método set_atributo_valor ya realiza un commit para el EAV.
            # La lógica JSON se ejecuta dentro de la misma transacción del trigger.
            if not activo.atributos_dinamicos_json:
                activo.atributos_dinamicos_json = {}
            
            # Convertir a string para asegurar serialización JSON
            fecha_str = target.fecha_mantenimiento.isoformat() if hasattr(target.fecha_mantenimiento, 'isoformat') else str(target.fecha_mantenimiento)
            activo.atributos_dinamicos_json['ultimo_mantenimiento'] = fecha_str
            
            # Marcar el campo JSON como modificado
            flag_modified(activo, "atributos_dinamicos_json")
            
            session.commit()

    except Exception as e:
        print(f"[TRIGGER ERROR] actualizar_ultimo_mantenimiento_activo: {e}")
        session.rollback()
    finally:
        session.close()


# TRIGGER 3: Auditoría de cambios de estado de activo
# ==============================================================================
@event.listens_for(Activo.estado, 'set')
def auditar_cambio_estado_activo(target, value, oldvalue, initiator):
    """
    Cuando cambia el estado de un activo, registrar en logs.
    """
    # La forma correcta de evitar que este evento se dispare durante la carga inicial
    # (como en init_db.py) es verificar si el valor anterior era 'PASSIVE_NO_RESULT'.
    # Esto indica que el atributo no tenía un valor previo.
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        from datetime import datetime
        # Usamos inspect para obtener el valor anterior de forma segura, aunque oldvalue ya lo tiene.
        history = inspect(target).attrs.estado.history
        print(f"[AUDIT] {datetime.now()} - Activo {target.placa_codigo_interno or '(nuevo)'}: "
              f"Estado cambió de '{history.deleted[0] if history.deleted else 'Inicial'}' a '{value}'")
        # Aquí podrías guardar en una tabla de auditoría


# TRIGGER 4: Prevenir eliminación de activo con mantenimientos pendientes
# ==============================================================================
@event.listens_for(Activo, 'before_delete')
def validar_eliminar_activo(mapper, connection, target):
    """
    Antes de eliminar un activo, verificar que no tenga mantenimientos pendientes.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import select

    session = Session(bind=connection)

    try:
        # Verificar mantenimientos pendientes
        stmt = (
            select(Mantenimiento)
            .where(
                Mantenimiento.activo_id == target.id,
                Mantenimiento.estado == 'Pendiente'
            )
        )

        mantenimientos_pendientes = session.execute(stmt).scalars().all()

        if mantenimientos_pendientes:
            raise ValueError(
                f"No se puede eliminar el activo {target.placa_codigo_interno}. "
                f"Tiene {len(mantenimientos_pendientes)} mantenimiento(s) pendiente(s). "
                f"Complete o cancele los mantenimientos antes de eliminar."
            )
    except ValueError:
        raise
    except Exception as e:
        print(f"[TRIGGER ERROR] validar_eliminar_activo: {e}")
    finally:
        session.close()


# TRIGGER 5: Validar que activo no esté en movimiento de salida activo
# ==============================================================================
@event.listens_for(MovimientoActivo, 'before_insert')
def validar_activo_disponible(mapper, connection, target):
    """
    Antes de insertar un MovimientoActivo, verificar que el activo
    no esté ya en otro movimiento de tipo 'Entrada/Salida' con estado 'Salida'.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import select

    session = Session(bind=connection)

    try:
        # Verificar si el activo está en un movimiento de Entrada/Salida tipo Salida
        stmt = (
            select(Movimiento)
            .join(MovimientoActivo)
            .join(DetalleEntradaSalida)
            .where(
                MovimientoActivo.activo_id == target.activo_id,
                DetalleEntradaSalida.tipo_operacion == 'Salida',
                Movimiento.id != target.movimiento_id  # No el mismo movimiento
            )
        )

        movimiento_existente = session.execute(stmt).scalar_one_or_none()

        if movimiento_existente:
            activo = session.get(Activo, target.activo_id)
            raise ValueError(
                f"El activo {activo.placa_codigo_interno if activo else target.activo_id} "
                f"está actualmente en salida según el movimiento #{movimiento_existente.id}. "
                f"Debe registrarse su entrada antes de asignarlo nuevamente."
            )
    except ValueError:
        raise
    except Exception as e:
        print(f"[TRIGGER ERROR] validar_activo_disponible: {e}")
    finally:
        session.close()


# TRIGGER 6: Log de creación de firmas
# ==============================================================================
@event.listens_for(Firma, 'after_insert')
def log_firma_creada(mapper, connection, target):
    """
    Registrar en log cuando se crea una firma digital.
    """
    from datetime import datetime
    print(f"[FIRMA] {datetime.now()} - Nueva firma: {target.tipo_documento} #{target.documento_id} "
          f"por rol '{target.rol_firma}'")


# ==============================================================================
# FASE 1.2: EVENT LISTENERS PARA AUDITORÍA AUTOMÁTICA DE ACTIVOS
# ==============================================================================
"""
Estos event listeners implementan el sistema de auditoría histórica completa.
Registran automáticamente todos los cambios en campos críticos de los activos.
Cumple con NIIF para PYMES Sección 27 (Control Interno sobre Activos).
"""

def obtener_ip_y_user_agent():
    """
    Helper para obtener IP y User-Agent del request actual.
    """
    try:
        from flask import request, has_request_context
        if has_request_context():
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')[:500]
            return ip, user_agent
    except:
        pass
    return None, None


def obtener_usuario_actual():
    """
    Helper para obtener el ID del usuario actual si está autenticado.
    """
    try:
        if current_user and current_user.is_authenticated:
            return current_user.id
    except:
        pass
    return None


def es_valor_centinela(valor):
    """
    Indica si `valor` es un centinela interno de SQLAlchemy y no un dato real.

    Los eventos 'set' entregan como valor anterior un miembro de
    LoaderCallableStatus (NO_VALUE, PASSIVE_NO_RESULT, NEVER_SET...) cuando el
    atributo nunca tuvo valor, que es justo lo que ocurre al construir un objeto
    nuevo. Comprobar solo PASSIVE_NO_RESULT dejaba pasar NO_VALUE, y eso
    provocaba dos fallos: `json.dumps(NO_VALUE)` lanzaba TypeError al crear un
    activo con atributos dinámicos, y el resto de listeners guardaban la cadena
    "LoaderCallableStatus.NO_VALUE" como valor anterior en la auditoría.
    """
    return isinstance(valor, LoaderCallableStatus)


def registrar_cambio_activo(activo, campo, valor_anterior, valor_nuevo, tipo_operacion='UPDATE', observaciones=None):
    """
    Registra un cambio en el historial de auditoría del activo.
    """
    from sqlalchemy.orm import Session

    # Alta del objeto: no hay valor anterior que auditar. La creación ya queda
    # registrada por el listener 'after_insert'.
    if es_valor_centinela(valor_anterior):
        return

    # Convertir valores a string para almacenar en TEXT
    valor_anterior_str = str(valor_anterior) if valor_anterior is not None else None
    valor_nuevo_str = str(valor_nuevo) if valor_nuevo is not None else None

    # No registrar si los valores son idénticos
    if valor_anterior_str == valor_nuevo_str:
        return

    ip_address, user_agent = obtener_ip_y_user_agent()
    usuario_id = obtener_usuario_actual()

    # Crear registro de auditoría
    historial = ActivoHistorico(
        activo_id=activo.id,
        campo_modificado=campo,
        valor_anterior=valor_anterior_str,
        valor_nuevo=valor_nuevo_str,
        usuario_id=usuario_id,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        tipo_operacion=tipo_operacion,
        observaciones=observaciones
    )

    # Obtener la sesión del activo
    session = Session.object_session(activo)
    if session:
        session.add(historial)


# TRIGGER 7: Auditoría de cambios en placa_codigo_interno
# ==============================================================================
@event.listens_for(Activo.placa_codigo_interno, 'set')
def auditar_cambio_placa(target, value, oldvalue, initiator):
    """
    Registra cambios en la placa/código interno del activo.
    Campo CRÍTICO para trazabilidad legal.
    """
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        registrar_cambio_activo(
            target, 'placa_codigo_interno', oldvalue, value,
            tipo_operacion='UPDATE',
            observaciones='Cambio en identificador único del activo'
        )


# TRIGGER 8: Auditoría de cambios en funcionario_id
# ==============================================================================
@event.listens_for(Activo.funcionario_id, 'set')
def auditar_cambio_funcionario(target, value, oldvalue, initiator):
    """
    Registra cambios en el funcionario responsable del activo.
    Campo CRÍTICO para trazabilidad de responsabilidades.
    """
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        registrar_cambio_activo(
            target, 'funcionario_id', oldvalue, value,
            tipo_operacion='UPDATE',
            observaciones='Cambio de responsable del activo'
        )


# TRIGGER 9: Auditoría de cambios en ubicación
# ==============================================================================
@event.listens_for(Activo.ubicacion, 'set')
def auditar_cambio_ubicacion(target, value, oldvalue, initiator):
    """
    Registra cambios en la ubicación física del activo.
    Campo CRÍTICO para inventario físico y conciliación.
    """
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        registrar_cambio_activo(
            target, 'ubicacion', oldvalue, value,
            tipo_operacion='UPDATE',
            observaciones='Cambio de ubicación física'
        )


# TRIGGER 10: Auditoría de cambios en estado
# ==============================================================================
@event.listens_for(Activo.estado, 'set')
def auditar_cambio_estado_activo_historico(target, value, oldvalue, initiator):
    """
    Registra cambios en el estado del activo.
    Campo CRÍTICO para ciclo de vida del activo.
    """
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        registrar_cambio_activo(
            target, 'estado', oldvalue, value,
            tipo_operacion='UPDATE',
            observaciones='Cambio de estado operativo'
        )


# TRIGGER 11: Auditoría de cambios en estado_conciliacion
# ==============================================================================
@event.listens_for(Activo.estado_conciliacion, 'set')
def auditar_cambio_conciliacion(target, value, oldvalue, initiator):
    """
    Registra cambios en el estado de conciliación física.
    Campo CRÍTICO para sistema anti-activos fantasma.
    """
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        registrar_cambio_activo(
            target, 'estado_conciliacion', oldvalue, value,
            tipo_operacion='VERIFICACION',
            observaciones='Cambio en estado de verificación física'
        )


# TRIGGER 12: Auditoría de cambios en atributos_dinamicos_json
# ==============================================================================
@event.listens_for(Activo.atributos_dinamicos_json, 'set')
def auditar_cambio_atributos_dinamicos(target, value, oldvalue, initiator):
    """
    Registra cambios en los atributos dinámicos JSON del activo.
    Campo CRÍTICO para propiedades específicas por clase de activo.
    """
    if not es_valor_centinela(oldvalue) and oldvalue != value:
        import json
        # Convertir a string formateado para comparación legible
        valor_anterior_str = json.dumps(oldvalue, sort_keys=True) if oldvalue else None
        valor_nuevo_str = json.dumps(value, sort_keys=True) if value else None

        if valor_anterior_str != valor_nuevo_str:
            registrar_cambio_activo(
                target, 'atributos_dinamicos_json', valor_anterior_str, valor_nuevo_str,
                tipo_operacion='UPDATE',
                observaciones='Modificación de atributos específicos de clase'
            )


# TRIGGER 13: Auditoría de creación de activos
# ==============================================================================
@event.listens_for(Activo, 'after_insert')
def auditar_creacion_activo(mapper, connection, target):
    """
    Registra la creación de un nuevo activo en el sistema.
    """
    from sqlalchemy.orm import Session
    session = Session(bind=connection)

    try:
        ip_address, user_agent = obtener_ip_y_user_agent()
        usuario_id = obtener_usuario_actual()

        historial = ActivoHistorico(
            activo_id=target.id,
            campo_modificado='ACTIVO_COMPLETO',
            valor_anterior=None,
            valor_nuevo=f'Creado: {target.nombre_activo} ({target.placa_codigo_interno})',
            usuario_id=usuario_id,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            tipo_operacion='CREATE',
            observaciones='Activo registrado en el sistema'
        )

        session.add(historial)
        session.commit()
    except Exception as e:
        print(f"[AUDIT ERROR] auditar_creacion_activo: {e}")
        session.rollback()
    finally:
        session.close()


# TRIGGER 14: Auditoría de eliminación de activos
# ==============================================================================
@event.listens_for(Activo, 'before_delete')
def auditar_eliminacion_activo(mapper, connection, target):
    """
    Registra la eliminación de un activo del sistema.
    IMPORTANTE: Este registro se crea ANTES de eliminar para que quede en historial.
    """
    from sqlalchemy.orm import Session
    session = Session(bind=connection)

    try:
        ip_address, user_agent = obtener_ip_y_user_agent()
        usuario_id = obtener_usuario_actual()

        historial = ActivoHistorico(
            activo_id=target.id,
            campo_modificado='ACTIVO_COMPLETO',
            valor_anterior=f'Eliminado: {target.nombre_activo} ({target.placa_codigo_interno})',
            valor_nuevo=None,
            usuario_id=usuario_id,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            tipo_operacion='DELETE',
            observaciones='Activo eliminado del sistema'
        )

        session.add(historial)
        session.commit()
    except Exception as e:
        print(f"[AUDIT ERROR] auditar_eliminacion_activo: {e}")
        session.rollback()
    finally:
        session.close()
