import os
from pathlib import Path
from dotenv import load_dotenv

# Define la ruta base del proyecto de forma segura e independiente del SO.
# BASE_DIR apunta al directorio raíz del proyecto (SIG MOVIMIENTOS ACTIVOS FIJOS).
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde el archivo .env
load_dotenv(BASE_DIR / '.env')

class Config:
    """
    Clase de configuración principal para la aplicación Flask.
    Centraliza todas las variables de configuración.
    """
    # --- Configuración de Seguridad ---
    # Clave secreta para proteger sesiones y datos firmados (CSRF).
    # Es CRÍTICO usar una variable de entorno en producción.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'una-clave-secreta-muy-dificil-de-adivinar-para-desarrollo')
    WTF_CSRF_ENABLED = True

    # --- Configuración de Red y Proxy ---
    # Poner en 'True' SOLO si la aplicación se ejecuta detrás de un proxy inverso confiable (nginx, AWS ELB).
    TRUST_X_FORWARDED_FOR = os.environ.get('TRUST_X_FORWARDED_FOR', 'False').lower() in ('true', '1', 't')

    # --- Configuración de Email (SMTP) ---
    # Para notificaciones automáticas (aprobaciones, alertas, etc.)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Email que envía (ej: notificaciones@empresa.com)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Contraseña o App Password
    SUPERVISOR_EMAIL = os.environ.get('SUPERVISOR_EMAIL')  # Email del supervisor para notificaciones

    # --- Configuración de Caché de PDFs ---
    PDF_CACHE_ENABLED = os.environ.get('PDF_CACHE_ENABLED', 'True').lower() in ('true', '1', 't')
    PDF_CACHE_MAX_AGE_DAYS = int(os.environ.get('PDF_CACHE_MAX_AGE_DAYS', 30))  # Días antes de considerar obsoleto

    # --- Configuración de la Base de Datos (MySQL únicamente) ---
    # Formato: mysql+pymysql://usuario:password@host:puerto/nombre_db
    # Las credenciales SIEMPRE deben venir de variables de entorno (.env)
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'jerosmart_activos')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

    # Configuraciones específicas de MySQL para optimizar el rendimiento
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # Número de conexiones en el pool
        'pool_recycle': 3600,  # Reciclar conexiones cada hora
        'pool_pre_ping': True,  # Verificar conexión antes de usar
        'max_overflow': 20,  # Conexiones adicionales si el pool está lleno
        'echo': False  # Cambiar a True para ver las queries SQL (debug)
    }

    # Desactiva una característica de Flask-SQLAlchemy que no se necesita y consume recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Identidad de la Organización ---
    # Datos que encabezan las actas PDF y los reportes. Se configuran por
    # variables de entorno para que la aplicación no quede atada a ningún
    # cliente concreto: antes el nombre, el NIT y el logo estaban escritos
    # directamente en las plantillas.
    ORG_NOMBRE = os.environ.get('ORG_NOMBRE', 'JeroSmart')
    ORG_NIT = os.environ.get('ORG_NIT', '')
    ORG_LOGO = os.environ.get('ORG_LOGO', 'img/logosmartjero.png')
    ORG_SEDE = os.environ.get('ORG_SEDE', '')

    # --- Configuración de Rutas de Archivos ---
    # Se usa pathlib para una gestión de rutas moderna y robusta.
    # Convertidas a strings para compatibilidad con os.path en Windows
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    SIGNATURES_FOLDER = str(BASE_DIR / 'uploads' / 'signatures')
    HOJAS_DE_VIDA_FOLDER = str(BASE_DIR / 'uploads' / 'hojas_de_vida')
    MAINTENANCE_PHOTOS_FOLDER = str(BASE_DIR / 'uploads' / 'maintenance_photos')
    INVOICE_FOLDER = str(BASE_DIR / 'uploads' / 'invoices')
    PURCHASE_ORDER_FOLDER = str(BASE_DIR / 'uploads' / 'purchase_orders')
    LOAN_CONTRACT_FOLDER = str(BASE_DIR / 'uploads' / 'loan_contracts')

    # --- Constantes de la Aplicación ---
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
        """
        Realiza inicializaciones que dependen de la instancia de la aplicación.
        Crea las carpetas necesarias si no existen.
        """
        required_folders = [
            app.config['UPLOAD_FOLDER'], app.config['SIGNATURES_FOLDER'],
            app.config['HOJAS_DE_VIDA_FOLDER'], app.config['MAINTENANCE_PHOTOS_FOLDER'],
            app.config['INVOICE_FOLDER'], app.config['PURCHASE_ORDER_FOLDER'],
            app.config['LOAN_CONTRACT_FOLDER']
        ]

        for folder in required_folders:
            Path(folder).mkdir(parents=True, exist_ok=True)