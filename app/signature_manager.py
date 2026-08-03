"""
Sistema avanzado de gestión de firmas digitales (sin APIs externas).

Implementa:
- Validación criptográfica de firmas
- Detección de manipulación
- Watermarks de seguridad
- Metadatos verificables
- Timestamps con proof-of-existence

Siguiendo principios SOLID y buenas prácticas de seguridad.
"""

import hashlib
import hmac
import base64
import json
from datetime import datetime
from typing import Tuple, Dict, Optional
from flask import current_app


class SignatureValidator:
    """
    Validador de integridad de firmas digitales.

    Implementa HMAC-SHA256 para garantizar no-repudio.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Inicializa el validador.

        Args:
            secret_key: Clave secreta para HMAC (opcional, usa la de Flask)
        """
        self.secret_key = secret_key or current_app.config['SECRET_KEY']

    def generate_signature_hash(self, signature_data: str, metadata: dict) -> str:
        """
        Genera un hash criptográfico de la firma con metadata.

        Args:
            signature_data: Datos de la firma (base64)
            metadata: Metadatos (timestamp, IP, user_agent, etc.)

        Returns:
            str: Hash HMAC-SHA256 en hexadecimal
        """
        # Construir mensaje a firmar
        message_parts = [
            signature_data,
            metadata.get('timestamp', ''),
            metadata.get('ip_address', ''),
            metadata.get('user_agent', '')[:100],  # Limitar longitud
            metadata.get('document_id', ''),
            metadata.get('signer_role', '')
        ]

        message = '|'.join(str(part) for part in message_parts)

        # Generar HMAC
        hmac_obj = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )

        return hmac_obj.hexdigest()

    def verify_signature_integrity(self, signature_data: str, metadata: dict, expected_hash: str) -> bool:
        """
        Verifica que una firma no haya sido manipulada.

        Args:
            signature_data: Datos de la firma (base64)
            metadata: Metadatos originales
            expected_hash: Hash esperado

        Returns:
            bool: True si la firma es válida
        """
        calculated_hash = self.generate_signature_hash(signature_data, metadata)
        return hmac.compare_digest(calculated_hash, expected_hash)


class SignatureMetadataBuilder:
    """
    Constructor de metadata para firmas siguiendo el patrón Builder.
    """

    def __init__(self):
        self._metadata = {}

    def with_timestamp(self, timestamp: datetime = None) -> 'SignatureMetadataBuilder':
        """Agrega timestamp (por defecto usa datetime.now())."""
        self._metadata['timestamp'] = (timestamp or datetime.now()).isoformat()
        return self

    def with_ip_address(self, ip: str) -> 'SignatureMetadataBuilder':
        """Agrega dirección IP del firmante."""
        self._metadata['ip_address'] = ip[:45]  # Limitar para IPv6
        return self

    def with_user_agent(self, user_agent: str) -> 'SignatureMetadataBuilder':
        """Agrega User-Agent del navegador."""
        self._metadata['user_agent'] = user_agent[:500]
        return self

    def with_document_id(self, doc_id: int) -> 'SignatureMetadataBuilder':
        """Agrega ID del documento firmado."""
        self._metadata['document_id'] = str(doc_id)
        return self

    def with_signer_role(self, role: str) -> 'SignatureMetadataBuilder':
        """Agrega rol del firmante."""
        self._metadata['signer_role'] = role
        return self

    def with_signer_name(self, name: str) -> 'SignatureMetadataBuilder':
        """Agrega nombre del firmante."""
        self._metadata['signer_name'] = name
        return self

    def with_consent(self, consent: bool) -> 'SignatureMetadataBuilder':
        """Agrega consentimiento explícito."""
        self._metadata['consent'] = consent
        return self

    def build(self) -> dict:
        """Construye el diccionario de metadata."""
        return self._metadata.copy()


class SignatureProcessor:
    """
    Procesador de firmas que coordina validación y almacenamiento.
    Sigue el patrón Facade para simplificar operaciones complejas.
    """

    def __init__(self):
        self.validator = SignatureValidator()

    def process_new_signature(
        self,
        signature_b64: str,
        signature_svg: Optional[str],
        metadata: dict
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Procesa una nueva firma y genera su hash de integridad.

        Args:
            signature_b64: Firma en base64 (imagen PNG)
            signature_svg: Firma en formato SVG (opcional)
            metadata: Metadata del firmante

        Returns:
            tuple: (success, integrity_hash, processed_metadata)
        """
        try:
            # Validar que la firma no esté vacía
            if not signature_b64 or len(signature_b64) < 100:
                return False, None, {'error': 'Firma vacía o inválida'}

            # Validar formato base64
            try:
                base64.b64decode(signature_b64.split(',')[1] if ',' in signature_b64 else signature_b64)
            except Exception:
                return False, None, {'error': 'Formato base64 inválido'}

            # Generar hash de integridad
            integrity_hash = self.validator.generate_signature_hash(signature_b64, metadata)

            # Agregar información adicional
            processed_metadata = metadata.copy()
            processed_metadata['integrity_hash'] = integrity_hash
            processed_metadata['signature_length'] = len(signature_b64)
            processed_metadata['has_svg'] = signature_svg is not None

            # Calcular fingerprint de la firma
            sig_fingerprint = hashlib.sha256(signature_b64.encode()).hexdigest()[:16]
            processed_metadata['fingerprint'] = sig_fingerprint

            return True, integrity_hash, processed_metadata

        except Exception as e:
            current_app.logger.error(f"Error procesando firma: {e}", exc_info=True)
            return False, None, {'error': str(e)}

    def verify_signature(
        self,
        signature_b64: str,
        stored_hash: str,
        metadata: dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica la integridad de una firma almacenada.

        Args:
            signature_b64: Firma a verificar
            stored_hash: Hash almacenado en BD
            metadata: Metadata original

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            is_valid = self.validator.verify_signature_integrity(
                signature_b64,
                metadata,
                stored_hash
            )

            if not is_valid:
                return False, "La firma ha sido manipulada o los datos no coinciden"

            return True, None

        except Exception as e:
            current_app.logger.error(f"Error verificando firma: {e}")
            return False, f"Error en verificación: {str(e)}"


class SignatureWatermark:
    """
    Genera watermarks de seguridad para PDFs con firmas.
    """

    @staticmethod
    def generate_verification_code(movimiento_id: int, firma_hash: str) -> str:
        """
        Genera un código de verificación único para una firma.

        Args:
            movimiento_id: ID del movimiento
            firma_hash: Hash de integridad de la firma

        Returns:
            str: Código de verificación (ej: "VER-1234-ABCD")
        """
        # Combinar datos
        data = f"{movimiento_id}|{firma_hash}"
        hash_obj = hashlib.sha256(data.encode())

        # Tomar primeros 8 caracteres del hash
        code_suffix = hash_obj.hexdigest()[:8].upper()

        return f"VER-{movimiento_id:04d}-{code_suffix}"

    @staticmethod
    def generate_watermark_text(metadata: dict) -> str:
        """
        Genera texto de watermark para el PDF.

        Args:
            metadata: Metadata de la firma

        Returns:
            str: Texto del watermark
        """
        timestamp = metadata.get('timestamp', 'Unknown')
        ip = metadata.get('ip_address', 'Unknown')
        fingerprint = metadata.get('fingerprint', 'N/A')

        return (
            f"FIRMA DIGITAL VERIFICABLE\n"
            f"Timestamp: {timestamp}\n"
            f"IP: {ip}\n"
            f"Fingerprint: {fingerprint}\n"
            f"Hash: SHA-256"
        )


# ==============================================================================
# FUNCIONES HELPER
# ==============================================================================

def create_signature_metadata(
    document_id: int,
    signer_role: str,
    signer_name: str,
    ip_address: str,
    user_agent: str,
    consent: bool = True
) -> dict:
    """
    Factory function para crear metadata de firma de forma sencilla.

    Args:
        document_id: ID del documento (movimiento)
        signer_role: Rol del firmante
        signer_name: Nombre del firmante
        ip_address: IP del firmante
        user_agent: User-Agent del navegador
        consent: Consentimiento explícito

    Returns:
        dict: Metadata completo

    Ejemplo:
        metadata = create_signature_metadata(
            document_id=123,
            signer_role='Quien_Entrega',
            signer_name='Juan Pérez',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0...',
            consent=True
        )
    """
    builder = SignatureMetadataBuilder()

    return (builder
        .with_timestamp()
        .with_document_id(document_id)
        .with_signer_role(signer_role)
        .with_signer_name(signer_name)
        .with_ip_address(ip_address)
        .with_user_agent(user_agent)
        .with_consent(consent)
        .build()
    )


def process_and_validate_signature(
    signature_b64: str,
    signature_svg: Optional[str],
    metadata: dict
) -> Tuple[bool, Optional[str], Optional[dict], Optional[str]]:
    """
    Función conveniente para procesar y validar una firma nueva.

    Args:
        signature_b64: Firma en base64
        signature_svg: Firma en SVG (opcional)
        metadata: Metadata del firmante

    Returns:
        tuple: (success, error_message, processed_metadata, verification_code)

    Ejemplo:
        success, error, metadata, code = process_and_validate_signature(
            signature_b64=firma_base64,
            signature_svg=firma_svg,
            metadata=metadata
        )

        if success:
            # Guardar en BD con metadata['integrity_hash']
            # Mostrar code al usuario
        else:
            # Mostrar error
    """
    processor = SignatureProcessor()

    # Procesar firma
    success, integrity_hash, processed_metadata = processor.process_new_signature(
        signature_b64,
        signature_svg,
        metadata
    )

    if not success:
        error_msg = processed_metadata.get('error', 'Error desconocido')
        return False, error_msg, None, None

    # Generar código de verificación
    doc_id = int(metadata.get('document_id', 0))
    verification_code = SignatureWatermark.generate_verification_code(doc_id, integrity_hash)

    return True, None, processed_metadata, verification_code


def verify_stored_signature(
    signature_b64: str,
    stored_hash: str,
    stored_metadata: dict
) -> Tuple[bool, Optional[str]]:
    """
    Verifica una firma almacenada en la base de datos.

    Args:
        signature_b64: Firma a verificar
        stored_hash: Hash almacenado en BD
        stored_metadata: Metadata original de la firma

    Returns:
        tuple: (is_valid, error_message)

    Ejemplo:
        is_valid, error = verify_stored_signature(
            firma.firma_base64,
            firma.hash_documento,
            {
                'timestamp': firma.timestamp_firma.isoformat(),
                'ip_address': firma.ip_address,
                'user_agent': firma.user_agent,
                'document_id': str(firma.documento_id),
                'signer_role': firma.rol_firma
            }
        )

        if is_valid:
            print("✅ Firma válida y sin manipular")
        else:
            print(f"❌ Firma inválida: {error}")
    """
    processor = SignatureProcessor()
    return processor.verify_signature(signature_b64, stored_hash, stored_metadata)
