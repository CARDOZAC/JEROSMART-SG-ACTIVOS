import os
from pathlib import Path

# Define la ruta base del proyecto de forma segura e independiente del SO.
# BASE_DIR apunta al directorio raíz del proyecto (SIG MOVIMIENTOS ACTIVOS FIJOS).
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """
    Clase de configuración principal para la aplicación Flask.
    Centraliza todas las variables de configuración.
    """

    # --- Configuración de Seguridad ---
    # Clave secreta para proteger sesiones y datos firmados (CSRF).
    # Es CRÍTICO usar una variable de entorno en producción.
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "una-clave-secreta-muy-dificil-de-adivinar-para-desarrollo"
    )
    WTF_CSRF_ENABLED = True

    # --- Configuración de la Base de Datos ---
    # URI de la base de datos, configurada exclusivamente para SQLite.
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'activos_fijos_v4.db'}"
    # Desactiva una característica de Flask-SQLAlchemy que no se necesita y consume recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configuración de Rutas de Archivos ---
    # Se usa pathlib para una gestión de rutas moderna y robusta.
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    SIGNATURES_FOLDER = UPLOAD_FOLDER / "signatures"
    HOJAS_DE_VIDA_FOLDER = UPLOAD_FOLDER / "hojas_de_vida"
    MAINTENANCE_PHOTOS_FOLDER = UPLOAD_FOLDER / "maintenance_photos"
    INVOICE_FOLDER = UPLOAD_FOLDER / "invoices"
    PURCHASE_ORDER_FOLDER = UPLOAD_FOLDER / "purchase_orders"
    LOAN_CONTRACT_FOLDER = UPLOAD_FOLDER / "loan_contracts"

    # --- Constantes de la Aplicación ---
    ATRIBUTOS_POR_CLASE = {
        "1": [
            {
                "name": "registro_invima",
                "label": "Registro Invima",
                "type": "text",
                "required": False,
            },
            {
                "name": "clasificacion_riesgo",
                "label": "Clasificación de Riesgo",
                "type": "select",
                "options": ["I", "IIa", "IIb", "III"],
                "required": False,
            },
            {
                "name": "vida_util",
                "label": "Vida Útil (años)",
                "type": "number",
                "required": False,
            },
            {
                "name": "ultimo_mantenimiento",
                "label": "Último Mantenimiento",
                "type": "date",
                "required": False,
            },
        ],
        "2": [
            {
                "name": "especificaciones_tecnicas",
                "label": "Especificaciones Técnicas (Electr.)",
                "type": "textarea",
                "required": False,
            }
        ],
        "3": [
            {
                "name": "procesador",
                "label": "Procesador",
                "type": "text",
                "required": False,
            },
            {
                "name": "disco_duro",
                "label": "Disco Duro",
                "type": "text",
                "required": False,
            },
            {"name": "ram", "label": "RAM", "type": "text", "required": False},
            {
                "name": "sistema_operativo",
                "label": "Sistema Operativo",
                "type": "text",
                "required": False,
            },
            {
                "name": "especificaciones_tecnicas",
                "label": "Especificaciones Técnicas (TICs)",
                "type": "textarea",
                "required": False,
            },
        ],
        "4": [
            {
                "name": "tipo_adquisicion",
                "label": "Tipo de Adquisición",
                "type": "select",
                "options": ["Compra", "Donación", "Comodato"],
                "required": False,
            },
            {
                "name": "fecha_ingreso",
                "label": "Fecha de Ingreso",
                "type": "date",
                "required": False,
            },
            {
                "name": "especificaciones_tecnicas",
                "label": "Especificaciones (Material, Dimensiones, etc.)",
                "type": "textarea",
                "required": False,
            },
        ],
    }

    ROLES_POR_MOVIMIENTO = {
        "Entrega": [
            "Quien_Entrega",
            "Quien_Recibe",
            "Soporte_Lider",
            "VoBo_Activos_Fijos",
            "Soporte_Tecnico",
            "VoBo_Subdirectora",
        ],
        "Entrada/Salida": [
            "Firma_Solicitante_Responsable",
            "Jefe_Inmediato",
            "Soporte_Quien_Recibe_Entrega",
            "VoBo_Activos_Fijos",
        ],
        "Traslado": [
            "Responsable_Origen",
            "Responsable_Destino",
            "Soporte_Tecnico",
            "VoBo_Activos_Fijos",
        ],
        "Paz y Salvo": ["Funcionario", "Jefe_Inmediato", "VoBo_Activos_Fijos"],
    }

    @staticmethod
    def init_app(app):
        """
        Realiza inicializaciones que dependen de la instancia de la aplicación.
        Crea las carpetas necesarias si no existen.
        """
        required_folders = [
            app.config["UPLOAD_FOLDER"],
            app.config["SIGNATURES_FOLDER"],
            app.config["HOJAS_DE_VIDA_FOLDER"],
            app.config["MAINTENANCE_PHOTOS_FOLDER"],
            app.config["INVOICE_FOLDER"],
            app.config["PURCHASE_ORDER_FOLDER"],
            app.config["LOAN_CONTRACT_FOLDER"],
        ]

        for folder in required_folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
