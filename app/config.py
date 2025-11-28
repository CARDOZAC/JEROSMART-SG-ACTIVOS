import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'una-clave-secreta-muy-dificil-de-adivinar-para-desarrollo')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    SIGNATURES_FOLDER = UPLOAD_FOLDER / 'signatures'
    HOJAS_DE_VIDA_FOLDER = UPLOAD_FOLDER / 'hojas_de_vida'
    MAINTENANCE_PHOTOS_FOLDER = UPLOAD_FOLDER / 'maintenance_photos'
    INVOICE_FOLDER = UPLOAD_FOLDER / 'invoices'
    PURCHASE_ORDER_FOLDER = UPLOAD_FOLDER / 'purchase_orders'
    LOAN_CONTRACT_FOLDER = UPLOAD_FOLDER / 'loan_contracts'

    ATRIBUTOS_POR_CLASE = {
        '1': [
            {'name': 'registro_invima', 'label': 'Registro Invima', 'type': 'text', 'required': False},
            {'name': 'clasificacion_riesgo', 'label': 'Clasificación de Riesgo', 'type': 'select',
             'options': ['I', 'IIa', 'IIb', 'III'], 'required': False},
            {'name': 'vida_util', 'label': 'Vida Útil (años)', 'type': 'number', 'required': False},
            {'name': 'ultimo_mantenimiento', 'label': 'Último Mantenimiento', 'type': 'date', 'required': False}
        ],
        '2': [
            {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones Técnicas (Electr.)', 'type': 'textarea', 'required': False}
        ],
        '3': [
            {'name': 'procesador', 'label': 'Procesador', 'type': 'text', 'required': False},
            {'name': 'disco_duro', 'label': 'Disco Duro', 'type': 'text', 'required': False},
            {'name': 'ram', 'label': 'RAM', 'type': 'text', 'required': False},
            {'name': 'sistema_operativo', 'label': 'Sistema Operativo', 'type': 'text', 'required': False},
            {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones Técnicas (TICs)', 'type': 'textarea', 'required': False}
        ],
        '4': [
            {'name': 'tipo_adquisicion', 'label': 'Tipo de Adquisición', 'type': 'select',
             'options': ['Compra', 'Donación', 'Comodato'], 'required': False},
            {'name': 'fecha_ingreso', 'label': 'Fecha de Ingreso', 'type': 'date', 'required': False},
            {'name': 'especificaciones_tecnicas', 'label': 'Especificaciones (Material, Dimensiones, etc.)', 'type': 'textarea', 'required': False}
        ]
    }

    ROLES_POR_MOVIMIENTO = {
        'Entrega': [
            'Quien_Entrega', 'Quien_Recibe', 'Soporte_Lider',
            'VoBo_Activos_Fijos', 'Soporte_Tecnico', 'VoBo_Subdirectora'
        ],
        'Entrada/Salida': [
            'Firma_Solicitante_Responsable', 'Jefe_Inmediato',
            'Soporte_Quien_Recibe_Entrega', 'VoBo_Activos_Fijos'
        ],
        'Traslado': [
            'Responsable_Origen', 'Responsable_Destino',
            'Soporte_Tecnico', 'VoBo_Activos_Fijos'
        ],
        'Paz y Salvo': [
            'Funcionario', 'Jefe_Inmediato', 'VoBo_Activos_Fijos'
        ]
    }

    @staticmethod
    def init_app(app):
        required_folders = [
            app.config['UPLOAD_FOLDER'], app.config['SIGNATURES_FOLDER'],
            app.config['HOJAS_DE_VIDA_FOLDER'], app.config['MAINTENANCE_PHOTOS_FOLDER'],
            app.config['INVOICE_FOLDER'], app.config['PURCHASE_ORDER_FOLDER'],
            app.config['LOAN_CONTRACT_FOLDER']
        ]
        for folder in required_folders:
            Path(folder).mkdir(parents=True, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'activos_fijos_dev.db'}"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{BASE_DIR / 'activos_fijos_prod.db'}"

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
