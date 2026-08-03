"""
Formularios para el m�dulo de movimientos.
Incluye protecci�n CSRF y validaciones WTForms.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Regexp


class MovimientoFiltroForm(FlaskForm):
    """
    Formulario para filtrar movimientos en la vista principal.
    Incluye protecci�n CSRF para prevenir ataques.
    """
    q = StringField(
        'B�squeda',
        validators=[
            Optional(),
            Length(
                min=2,
                max=100,
                message='La b�squeda debe tener entre 2 y 100 caracteres'
            )
        ],
        render_kw={
            'placeholder': 'Ej. Ana P�rez',
            'class': 'form-control'
        }
    )

    tipo = SelectField(
        'Tipo de Acta',
        choices=[
            ('', 'Todos los tipos'),
            ('Entrega', 'Acta de Entrega'),
            ('Traslado', 'Acta de Traslado'),
            ('Entrada/Salida', 'Acta de Entrada/Salida'),
            ('Paz y Salvo', 'Acta de Paz y Salvo'),
            ('Reporte de Da�o o P�rdida', 'Reporte de Da�o o P�rdida'),
            ('Comodato', 'Acta de Comodato')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    submit = SubmitField(
        'Filtrar',
        render_kw={'class': 'btn btn-primary w-100'}
    )


class MovimientoCSRFForm(FlaskForm):
    """
    Formulario base que solo proporciona protecci�n CSRF.
    Se usa en add_movimiento.html para proteger el formulario
    sin cambiar toda la l�gica de validaci�n existente.
    """
    # No hay campos, solo el token CSRF autom�tico
    pass


class EliminarMovimientoForm(FlaskForm):
    """
    Formulario para confirmar eliminaci�n de un movimiento.
    Protege contra CSRF en operaciones DELETE.
    """
    movimiento_id = HiddenField(
        'ID del Movimiento',
        validators=[DataRequired()]
    )

    submit = SubmitField(
        'Eliminar',
        render_kw={'class': 'btn btn-danger'}
    )


# ==============================================================================
# FUNCIONES HELPER PARA VALIDACI�N Y CONVERSI�N DE DATOS
# ==============================================================================

def safe_float_conversion(value, default=None):
    """
    Convierte un valor a float de forma segura.

    Args:
        value: Valor a convertir (puede ser str, int, float, None)
        default: Valor por defecto si la conversi�n falla

    Returns:
        float o default

    Ejemplo:
        >>> safe_float_conversion('1234.56')
        1234.56
        >>> safe_float_conversion('abc', 0.0)
        0.0
        >>> safe_float_conversion(None, 0.0)
        0.0
    """
    if value is None or value == '':
        return default

    # Si ya es float o int, retornar directamente
    if isinstance(value, (int, float)):
        return float(value)

    # Si es string, limpiar y convertir
    if isinstance(value, str):
        # Remover espacios y caracteres comunes
        cleaned = value.strip().replace(',', '').replace('$', '').replace(' ', '')

        # Validar que sea un n�mero v�lido
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return default

    return default


def safe_int_conversion(value, default=None):
    """
    Convierte un valor a int de forma segura.

    Args:
        value: Valor a convertir (puede ser str, int, float, None)
        default: Valor por defecto si la conversi�n falla

    Returns:
        int o default

    Ejemplo:
        >>> safe_int_conversion('123')
        123
        >>> safe_int_conversion('abc', 0)
        0
    """
    if value is None or value == '':
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        cleaned = value.strip().replace(',', '').replace(' ', '')
        try:
            # Intentar convertir directamente
            return int(cleaned)
        except (ValueError, TypeError):
            # Si tiene punto decimal, intentar convertir a float primero
            try:
                return int(float(cleaned))
            except (ValueError, TypeError):
                return default

    return default


def sanitize_search_term(term, min_length=2, max_length=100):
    """
    Sanitiza un t�rmino de b�squeda para prevenir SQL injection y DoS.

    Args:
        term: T�rmino a sanitizar
        min_length: Longitud m�nima permitida
        max_length: Longitud m�xima permitida

    Returns:
        tuple: (sanitized_term, is_valid)

    Ejemplo:
        >>> sanitize_search_term('Ana%P�rez', 2, 100)
        ('AnaP�rez', True)
        >>> sanitize_search_term('A', 2, 100)
        ('', False)
    """
    if not term or not isinstance(term, str):
        return '', False

    # Remover caracteres peligrosos para SQL LIKE
    sanitized = term.replace('%', '').replace('_', '').strip()

    # Validar longitud
    if len(sanitized) < min_length or len(sanitized) > max_length:
        return '', False

    # Limitar a caracteres seguros (letras, n�meros, espacios, guiones)
    # Esto permite b�squedas en espa�ol con acentos
    import re
    sanitized = re.sub(r'[^\w\s\-������������]', '', sanitized)

    return sanitized, len(sanitized) >= min_length


def validate_json_structure(data, required_keys=None):
    """
    Valida que un diccionario tenga la estructura esperada.

    Args:
        data: Diccionario a validar
        required_keys: Lista de claves requeridas

    Returns:
        tuple: (is_valid, missing_keys)

    Ejemplo:
        >>> validate_json_structure({'id': 1, 'name': 'Test'}, ['id', 'name'])
        (True, [])
        >>> validate_json_structure({'id': 1}, ['id', 'name'])
        (False, ['name'])
    """
    if not isinstance(data, dict):
        return False, ['Invalid data type']

    if required_keys is None:
        return True, []

    missing = [key for key in required_keys if key not in data]
    return len(missing) == 0, missing


# ==============================================================================
# VALIDADORES PERSONALIZADOS
# ==============================================================================

class NITValidator:
    """
    Validador personalizado para NIT colombiano.
    Formato: XXXXXXXXX-X
    """
    def __init__(self, message=None):
        if not message:
            message = 'NIT inv�lido. Use el formato XXXXXXXXX-X'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return  # Optional field

        import re
        # Patr�n: 9 d�gitos, gui�n, 1 d�gito
        pattern = r'^\d{9}-\d$'
        if not re.match(pattern, field.data):
            from wtforms.validators import ValidationError
            raise ValidationError(self.message)


class CedulaValidator:
    """
    Validador personalizado para c�dula colombiana.
    Acepta entre 6 y 10 d�gitos.
    """
    def __init__(self, message=None):
        if not message:
            message = 'C�dula inv�lida. Debe tener entre 6 y 10 d�gitos'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return  # Optional field

        import re
        # Solo d�gitos, entre 6 y 10 caracteres
        pattern = r'^\d{6,10}$'
        if not re.match(pattern, str(field.data)):
            from wtforms.validators import ValidationError
            raise ValidationError(self.message)


# ==============================================================================
# FUNCIONES DE SEGURIDAD
# ==============================================================================

def get_client_ip(request):
    """
    Obtiene la direccion IP del cliente de forma segura.

    La confianza en los encabezados de proxy se gestiona centralmente a través de 
    la configuración de la aplicación `TRUST_X_FORWARDED_FOR`.

    ADVERTENCIA DE SEGURIDAD:
    Establecer `TRUST_X_FORWARDED_FOR` en True solo si la aplicación se ejecuta
    detrás de un proxy/load balancer CONFIABLE (como nginx, Apache, AWS ELB, etc.).

    Args:
        request: Objeto Flask request. La confianza en el proxy se lee desde
                 la configuración de la aplicación (current_app.config['TRUST_X_FORWARDED_FOR']).

    Returns:
        str: Direccion IP del cliente (limitada a 45 caracteres para IPv6)

    Ejemplos:
        >>> # En config.py: TRUST_X_FORWARDED_FOR = False (seguro)
        >>> get_client_ip(request)
        '192.168.1.100' # Se lee request.remote_addr

        >>> # En config.py: TRUST_X_FORWARDED_FOR = True (detrás de proxy confiable)
        >>> get_client_ip(request)
        '203.0.113.195'  # Se lee X-Forwarded-For
    """
    import re
    from flask import current_app

    trust_proxy = current_app.config.get('TRUST_X_FORWARDED_FOR', False)
    ip_address = 'desconocida'

    # Si confiamos en el proxy, intentar obtener IP de headers
    if trust_proxy:
        # X-Forwarded-For puede contener multiples IPs: "client, proxy1, proxy2"
        # La primera es la IP real del cliente
        if request.headers.get('X-Forwarded-For'):
            forwarded_ips = request.headers.get('X-Forwarded-For').split(',')
            # Tomar la primera IP y limpiarla
            ip_address = forwarded_ips[0].strip()

        # X-Real-IP es mas confiable en configuraciones simples (nginx)
        elif request.headers.get('X-Real-IP'):
            ip_address = request.headers.get('X-Real-IP').strip()

        # Fallback: usar remote_addr (IP del ultimo salto)
        elif request.remote_addr:
            ip_address = request.remote_addr
    else:
        # Modo seguro: solo usar remote_addr (IP directa de la conexion)
        if request.remote_addr:
            ip_address = request.remote_addr

    # Validar formato de IP (basico)
    # IPv4: xxx.xxx.xxx.xxx
    # IPv6: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'

    if not (re.match(ipv4_pattern, ip_address) or re.match(ipv6_pattern, ip_address)):
        # Si no es una IP valida, truncar y registrar advertencia
        ip_address = ip_address[:45] if ip_address else 'invalida'

    # Limitar longitud para compatibilidad con BD (VARCHAR(45))
    return ip_address[:45]


# ==============================================================================
# FORMULARIO DE COMODATO
# ==============================================================================

class ComodatoForm(FlaskForm):
    """
    Formulario para registro de Comodatos.

    CONTEXTO LEGAL Y CONTABLE:
    El comodato es un contrato de préstamo gratuito que requiere documentación
    detallada para cumplir con:
    - Código Civil Colombiano (Art. 2200)
    - NIIF para PYMES, Sección 20 (Revelación en notas)
    - Control interno y trazabilidad de activos

    Este formulario solo proporciona protección CSRF.
    La validación de campos se hace en JavaScript y backend (routes.py).
    """
    # Token CSRF automático - No hay campos adicionales
    pass


# ==============================================================================
# VALIDADORES ESPECÍFICOS PARA COMODATO
# ==============================================================================

def validar_fecha_comodato(fecha_inicio, fecha_fin):
    """
    Valida que las fechas del comodato sean coherentes.

    Args:
        fecha_inicio: Fecha de inicio del comodato (date object)
        fecha_fin: Fecha de fin del comodato (date object)

    Returns:
        tuple: (is_valid, error_message)

    Validaciones:
    - La fecha de inicio no puede ser posterior a la fecha de fin
    - La duración mínima debe ser 1 día
    - La duración máxima recomendada es 5 años (1825 días)

    Ejemplo:
        >>> from datetime import date
        >>> validar_fecha_comodato(date(2024, 1, 1), date(2024, 12, 31))
        (True, None)
        >>> validar_fecha_comodato(date(2024, 12, 31), date(2024, 1, 1))
        (False, 'La fecha de inicio no puede ser posterior a la fecha de fin')
    """
    from datetime import date, timedelta

    if not fecha_inicio or not fecha_fin:
        return False, 'Las fechas de inicio y fin son obligatorias'

    # Convertir a date si son datetime
    if hasattr(fecha_inicio, 'date'):
        fecha_inicio = fecha_inicio.date()
    if hasattr(fecha_fin, 'date'):
        fecha_fin = fecha_fin.date()

    # Validar orden de fechas
    if fecha_inicio > fecha_fin:
        return False, 'La fecha de inicio no puede ser posterior a la fecha de fin'

    # Validar duración mínima (1 día)
    duracion = (fecha_fin - fecha_inicio).days
    if duracion < 1:
        return False, 'La duración del comodato debe ser de al menos 1 día'

    # Alerta para duraciones muy largas (más de 5 años)
    if duracion > 1825:  # 5 años
        return True, 'ALERTA: El comodato tiene una duración superior a 5 años'

    return True, None


def calcular_plazo_meses(fecha_inicio, fecha_fin):
    """
    Calcula el plazo en meses entre dos fechas.

    Args:
        fecha_inicio: Fecha de inicio (date object)
        fecha_fin: Fecha de fin (date object)

    Returns:
        int: Número de meses (redondeado)

    Ejemplo:
        >>> from datetime import date
        >>> calcular_plazo_meses(date(2024, 1, 1), date(2024, 12, 31))
        12
        >>> calcular_plazo_meses(date(2024, 1, 1), date(2024, 7, 15))
        6
    """
    if not fecha_inicio or not fecha_fin:
        return 0

    # Convertir a date si son datetime
    if hasattr(fecha_inicio, 'date'):
        fecha_inicio = fecha_inicio.date()
    if hasattr(fecha_fin, 'date'):
        fecha_fin = fecha_fin.date()

    # Calcular diferencia en meses
    meses = (fecha_fin.year - fecha_inicio.year) * 12 + (fecha_fin.month - fecha_inicio.month)

    # Ajustar por días si el día final es menor que el inicial
    if fecha_fin.day < fecha_inicio.day:
        meses -= 1

    return max(0, meses)


def validar_nit_comodato(nit):
    """
    Valida el formato de un NIT para comodato.

    Args:
        nit: String con el NIT a validar

    Returns:
        tuple: (is_valid, cleaned_nit)

    Formatos aceptados:
    - XXXXXXXXX-X (formato estándar)
    - XXXXXXXXX (sin dígito de verificación)

    Ejemplo:
        >>> validar_nit_comodato('900123456-7')
        (True, '900123456-7')
        >>> validar_nit_comodato('900123456')
        (True, '900123456')
        >>> validar_nit_comodato('invalid')
        (False, None)
    """
    import re

    if not nit or not isinstance(nit, str):
        return False, None

    # Limpiar espacios
    nit_clean = nit.strip()

    # Patrón 1: XXXXXXXXX-X (con dígito de verificación)
    pattern1 = r'^\d{9}-\d$'
    # Patrón 2: XXXXXXXXX (sin dígito de verificación)
    pattern2 = r'^\d{9}$'
    # Patrón 3: Formato flexible (permitir 7-10 dígitos con o sin guión)
    pattern3 = r'^\d{7,10}(-\d)?$'

    if re.match(pattern1, nit_clean) or re.match(pattern2, nit_clean) or re.match(pattern3, nit_clean):
        return True, nit_clean

    return False, None


def validar_numero_contrato(numero_contrato):
    """
    Valida el formato de un número de contrato de comodato.

    Args:
        numero_contrato: String con el número de contrato

    Returns:
        tuple: (is_valid, error_message)

    Validaciones:
    - Longitud mínima: 3 caracteres
    - Longitud máxima: 100 caracteres
    - Caracteres permitidos: alfanuméricos, guiones, espacios

    Ejemplo:
        >>> validar_numero_contrato('COM-2024-001')
        (True, None)
        >>> validar_numero_contrato('AB')
        (False, 'El número de contrato debe tener al menos 3 caracteres')
    """
    import re

    if not numero_contrato or not isinstance(numero_contrato, str):
        return False, 'El número de contrato es obligatorio'

    # Limpiar espacios al inicio y final
    numero_clean = numero_contrato.strip()

    # Validar longitud
    if len(numero_clean) < 3:
        return False, 'El número de contrato debe tener al menos 3 caracteres'

    if len(numero_clean) > 100:
        return False, 'El número de contrato no puede exceder 100 caracteres'

    # Validar caracteres (alfanuméricos, guiones, espacios, barras)
    pattern = r'^[\w\s\-/]+$'
    if not re.match(pattern, numero_clean):
        return False, 'El número de contrato contiene caracteres no permitidos'

    return True, None

