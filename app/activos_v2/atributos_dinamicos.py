"""
Definición de atributos dinámicos por clase de activo.
Estos atributos se cargan dinámicamente según la clase seleccionada.
"""

ATRIBUTOS_POR_CLASE = {
    "1": [  # EQUIPO BIOMÉDICO
        {
            "name": "registro_invima",
            "label": "Registro Sanitario INVIMA",
            "type": "text",
            "required": True,
            "placeholder": "Ej: 2024DM-0012345",
        },
        {
            "name": "clasificacion_riesgo",
            "label": "Clasificación de Riesgo (Res. 4725/2011)",
            "type": "select",
            "options": ["I", "IIa", "IIb", "III"],
            "required": True,
        },
        {
            "name": "clasificacion_biomedica",
            "label": "Clasificación Biomédica",
            "type": "select",
            "options": [
                "Diagnóstico",
                "Tratamiento y Mantenimiento de la Vida",
                "Prevención",
                "Rehabilitación",
                "Análisis de Laboratorio",
            ],
            "required": True,
        },
        {"name": "fabricante", "label": "Fabricante", "type": "text", "required": True},
        {
            "name": "pais_origen",
            "label": "País de Origen",
            "type": "text",
            "required": False,
        },
        {
            "name": "vida_util",
            "label": "Vida Útil según Fabricante (años)",
            "type": "number",
            "required": True,
            "min": 1,
            "max": 30,
        },
        {
            "name": "frecuencia_mantenimiento",
            "label": "Frecuencia Mantenimiento Preventivo",
            "type": "select",
            "options": ["Mensual", "Trimestral", "Semestral", "Anual"],
            "required": True,
        },
        {
            "name": "requiere_calibracion",
            "label": "¿Requiere Calibración?",
            "type": "select",
            "options": ["Sí", "No"],
            "required": True,
        },
        {
            "name": "voltaje_operacion",
            "label": "Voltaje de Operación (V)",
            "type": "text",
            "required": False,
            "placeholder": "Ej: 110V AC",
        },
        {
            "name": "potencia",
            "label": "Potencia (W)",
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
    "2": [  # ELECTROINDUSTRIAL
        {
            "name": "voltaje_nominal",
            "label": "Voltaje Nominal (V)",
            "type": "text",
            "required": True,
            "placeholder": "Ej: 220V AC",
        },
        {
            "name": "corriente_nominal",
            "label": "Corriente Nominal (A)",
            "type": "number",
            "required": False,
            "step": 0.1,
        },
        {
            "name": "potencia_nominal",
            "label": "Potencia Nominal (W/kW)",
            "type": "text",
            "required": False,
        },
        {
            "name": "cumple_retie",
            "label": "¿Cumple RETIE?",
            "type": "select",
            "options": ["Sí", "No", "No Aplica"],
            "required": True,
        },
        {
            "name": "certificado_conformidad",
            "label": "Certificado de Conformidad",
            "type": "text",
            "required": False,
            "placeholder": "Número de certificado",
        },
        {
            "name": "especificaciones_tecnicas",
            "label": "Especificaciones Técnicas",
            "type": "textarea",
            "required": False,
            "rows": 3,
        },
    ],
    "3": [  # TECNOLOGÍA DE COMUNICACIÓN E INFORMACIÓN (TICs)
        {
            "name": "tipo_equipo",
            "label": "Tipo de Equipo",
            "type": "select",
            "options": [
                "Computador de Escritorio",
                "Portátil",
                "Servidor",
                "Impresora",
                "Scanner",
                "Router/Switch",
                "Tablet",
                "Otro",
            ],
            "required": True,
        },
        {
            "name": "procesador",
            "label": "Procesador",
            "type": "text",
            "required": False,
            "placeholder": "Ej: Intel Core i7 10ma Gen",
        },
        {
            "name": "ram",
            "label": "Memoria RAM",
            "type": "text",
            "required": False,
            "placeholder": "Ej: 16GB DDR4",
        },
        {
            "name": "almacenamiento",
            "label": "Almacenamiento",
            "type": "text",
            "required": False,
            "placeholder": "Ej: SSD 512GB",
        },
        {
            "name": "sistema_operativo",
            "label": "Sistema Operativo",
            "type": "text",
            "required": False,
            "placeholder": "Ej: Windows 11 Pro",
        },
        {
            "name": "licencia_software",
            "label": "Licencia de Software",
            "type": "text",
            "required": False,
            "placeholder": "Número de licencia o tipo",
        },
        {
            "name": "direccion_ip",
            "label": "Dirección IP Asignada",
            "type": "text",
            "required": False,
            "placeholder": "Ej: 192.168.1.100",
        },
        {
            "name": "direccion_mac",
            "label": "Dirección MAC",
            "type": "text",
            "required": False,
            "placeholder": "Ej: 00:1A:2B:3C:4D:5E",
        },
        {
            "name": "vida_util_estimada",
            "label": "Vida Útil Estimada (años)",
            "type": "select",
            "options": ["3", "5", "7", "10"],
            "required": True,
        },
        {
            "name": "especificaciones_tecnicas",
            "label": "Otras Especificaciones",
            "type": "textarea",
            "required": False,
            "rows": 3,
        },
    ],
    "4": [  # MUEBLES Y ENSERES
        {
            "name": "tipo_mueble",
            "label": "Tipo de Mueble",
            "type": "select",
            "options": [
                "Escritorio",
                "Silla",
                "Archivador",
                "Estantería",
                "Mesa",
                "Locker",
                "Vitrina",
                "Otro",
            ],
            "required": True,
        },
        {
            "name": "material",
            "label": "Material Principal",
            "type": "select",
            "options": ["Madera", "Metal", "Plástico", "Vidrio", "Mixto"],
            "required": True,
        },
        {
            "name": "dimensiones",
            "label": "Dimensiones (Alto x Ancho x Fondo)",
            "type": "text",
            "required": False,
            "placeholder": "Ej: 75cm x 120cm x 60cm",
        },
        {"name": "color", "label": "Color", "type": "text", "required": False},
        {
            "name": "estado_fisico",
            "label": "Estado Físico",
            "type": "select",
            "options": ["Excelente", "Bueno", "Regular", "Malo"],
            "required": True,
        },
        {
            "name": "tipo_adquisicion",
            "label": "Tipo de Adquisición",
            "type": "select",
            "options": ["Compra", "Donación", "Comodato", "Fabricación Propia"],
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
            "label": "Descripción Adicional",
            "type": "textarea",
            "required": False,
            "rows": 3,
        },
    ],
}


def get_atributos_por_clase(clase_id):
    """
    Obtiene los atributos dinámicos para una clase específica.

    Args:
        clase_id: ID de la clase de activo (puede ser int o str)

    Returns:
        Lista de atributos o lista vacía si no hay atributos definidos
    """
    return ATRIBUTOS_POR_CLASE.get(str(clase_id), [])
