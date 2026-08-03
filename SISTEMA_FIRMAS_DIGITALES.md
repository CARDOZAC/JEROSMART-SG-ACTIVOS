# Sistema Avanzado de Firmas Digitales

## Resumen Ejecutivo

Se ha implementado un sistema completo de gestión de firmas digitales con validación criptográfica **sin necesidad de APIs externas**, siguiendo las mejores prácticas de programación y principios SOLID.

### Características Principales

✅ **Validación Criptográfica**: HMAC-SHA256 para garantizar integridad
✅ **Sin APIs Externas**: Todo el sistema funciona localmente
✅ **Detección de Manipulación**: Identifica si una firma ha sido alterada
✅ **Códigos de Verificación**: Códigos únicos para cada firma
✅ **Watermarks de Seguridad**: Marcas de agua para PDFs
✅ **Metadata Completa**: Timestamp, IP, User-Agent, consentimiento
✅ **Patrones de Diseño**: Builder, Facade, SOLID principles

---

## Arquitectura del Sistema

### Componentes Principales

```
app/
├── signature_manager.py       # Sistema de gestión de firmas
│   ├── SignatureValidator     # Validación HMAC-SHA256
│   ├── SignatureMetadataBuilder  # Constructor de metadata
│   ├── SignatureProcessor     # Procesador de firmas (Facade)
│   └── SignatureWatermark     # Generación de watermarks
│
├── movimientos/routes.py      # Rutas integradas con el sistema
│   ├── firmar_movimiento      # Guardar firma con validación
│   ├── eliminar_firma         # Eliminar firma + invalidar caché
│   └── verificar_firma        # Verificar integridad criptográfica (NUEVO)
│
└── pdf_cache.py              # Caché de PDFs con invalidación
```

---

## Cómo Funciona (Técnicamente)

### 1. Proceso de Firma

Cuando un usuario firma un documento:

```python
# 1. Se crea metadata estructurado
signature_metadata = create_signature_metadata(
    document_id=123,
    signer_role='Quien_Entrega',
    signer_name='Juan Pérez',
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...',
    consent=True
)

# 2. Se procesa y valida la firma
success, error, metadata, code = process_and_validate_signature(
    signature_b64="data:image/svg+xml;base64,...",
    signature_svg="<svg>...</svg>",
    metadata=signature_metadata
)

# 3. Se obtiene:
# - integrity_hash: Hash HMAC-SHA256 único
# - verification_code: Código tipo "VER-0123-A1B2C3D4"
# - fingerprint: Identificador corto de la firma
```

### 2. Generación del Hash de Integridad (HMAC-SHA256)

```python
# Combina datos relevantes en un mensaje único
message = "|".join([
    signature_b64,           # Datos de la firma
    timestamp,               # Hora exacta
    ip_address,              # IP del firmante
    user_agent[:100],        # Navegador
    document_id,             # ID del documento
    signer_role              # Rol del firmante
])

# Genera HMAC usando la SECRET_KEY de Flask
hmac_hash = HMAC-SHA256(SECRET_KEY, message)
# Resultado: "a1b2c3d4e5f6..."
```

**¿Por qué HMAC y no SHA256 simple?**
- SHA256 simple: Cualquiera puede recalcular el hash
- HMAC-SHA256: Solo quien tiene la SECRET_KEY puede generar el hash válido
- Esto garantiza **no-repudio** y **autenticidad**

### 3. Verificación de Integridad

```python
# Al verificar una firma almacenada:
is_valid, error = verify_stored_signature(
    signature_b64=firma.firma_base64,
    stored_hash=firma.hash_documento,
    stored_metadata={
        'timestamp': firma.timestamp_firma.isoformat(),
        'ip_address': firma.ip_address,
        'user_agent': firma.user_agent,
        'document_id': str(firma.documento_id),
        'signer_role': firma.rol_firma
    }
)

# Internamente:
# 1. Recalcula el HMAC con los mismos datos
# 2. Compara usando hmac.compare_digest() (resistente a timing attacks)
# 3. Retorna True solo si los hashes coinciden exactamente
```

---

## Uso del Sistema

### Endpoint 1: Guardar Firma (Mejorado)

**Ruta**: `POST /movimientos/firmar/<movimiento_id>`

**Cambios realizados**:
- Ahora usa `SignatureProcessor` para validación criptográfica
- Genera código de verificación único
- Calcula fingerprint SHA256 de la firma
- Invalida caché de PDFs automáticamente

**Respuesta**:
```json
{
  "success": true,
  "message": "Firma guardada exitosamente con validación criptográfica.",
  "verification_code": "VER-0123-A1B2C3D4",
  "debug_info": {
    "integrity_hash": "a1b2c3d4e5f6...",
    "fingerprint": "1a2b3c4d5e6f7890",
    "ip": "192.168.1.100",
    "timestamp": "2025-12-11T10:30:00",
    "has_svg": true,
    "consentimiento": true
  }
}
```

### Endpoint 2: Verificar Integridad (NUEVO)

**Ruta**: `GET /movimientos/firmar/<movimiento_id>/<rol_firma>/verificar`

**Propósito**: Verificar que una firma no haya sido manipulada

**Ejemplo**:
```bash
GET /movimientos/firmar/123/Quien_Entrega/verificar
```

**Respuesta si es válida**:
```json
{
  "success": true,
  "valid": true,
  "message": "Firma válida: no ha sido manipulada.",
  "details": {
    "firmante": "Juan Pérez",
    "rol": "Quien_Entrega",
    "timestamp": "2025-12-11T10:30:00",
    "ip_address": "192.168.1.100",
    "verification_code": "VER-0123-A1B2C3D4",
    "consentimiento": true,
    "has_svg": true
  }
}
```

**Respuesta si fue manipulada**:
```json
{
  "success": true,
  "valid": false,
  "message": "ADVERTENCIA: La firma ha sido manipulada o los datos no coinciden",
  "details": {
    "firmante": "Juan Pérez",
    "rol": "Quien_Entrega",
    "timestamp": "2025-12-11T10:30:00"
  }
}
```

### Endpoint 3: Eliminar Firma (Mejorado)

**Ruta**: `POST /movimientos/firmar/<movimiento_id>/<rol_firma>/eliminar`

**Cambios**:
- Ahora invalida automáticamente el caché de PDFs
- Logs mejorados con más contexto

---

## Integración en Frontend

### Mostrar Código de Verificación al Firmar

```javascript
// En tu JavaScript del frontend:
fetch(`/movimientos/firmar/${movimientoId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        rol_firma: rol,
        nombre_firmante: nombre,
        signature: signatureBase64,
        signature_svg: signatureSVG,
        consentimiento_aceptado: true
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Mostrar el código de verificación al usuario
        alert(`
            Firma guardada exitosamente

            Código de Verificación: ${data.verification_code}

            Guarde este código para futuras verificaciones.
        `);

        // O mejor, mostrarlo en un modal bonito:
        showVerificationModal(data.verification_code, data.debug_info);
    }
});
```

### Botón de Verificación de Firma

```html
<!-- En ver_movimiento.html o firmar.html -->
<div class="firma-verificacion">
    <button class="btn btn-sm btn-outline-primary"
            onclick="verificarFirma({{ movimiento.id }}, '{{ firma.rol_firma }}')">
        <i class="bi bi-shield-check"></i> Verificar Integridad
    </button>
</div>

<script>
function verificarFirma(movimientoId, rolFirma) {
    fetch(`/movimientos/firmar/${movimientoId}/${rolFirma}/verificar`)
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                Swal.fire({
                    icon: 'success',
                    title: 'Firma Válida',
                    html: `
                        <p>✅ La firma no ha sido manipulada</p>
                        <p><strong>Código de Verificación:</strong> ${data.details.verification_code}</p>
                        <p><small>Firmante: ${data.details.firmante}</small></p>
                        <p><small>Fecha: ${data.details.timestamp}</small></p>
                    `
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Firma Inválida',
                    text: data.message
                });
            }
        });
}
</script>
```

---

## Watermarks para PDFs

### Uso del SignatureWatermark

```python
from app.signature_manager import SignatureWatermark

# Generar código de verificación
verification_code = SignatureWatermark.generate_verification_code(
    movimiento_id=123,
    firma_hash="a1b2c3d4e5f6..."
)
# Resultado: "VER-0123-A1B2C3D4"

# Generar texto para watermark del PDF
watermark_text = SignatureWatermark.generate_watermark_text({
    'timestamp': '2025-12-11T10:30:00',
    'ip_address': '192.168.1.100',
    'fingerprint': '1a2b3c4d5e6f7890'
})
# Resultado:
# FIRMA DIGITAL VERIFICABLE
# Timestamp: 2025-12-11T10:30:00
# IP: 192.168.1.100
# Fingerprint: 1a2b3c4d5e6f7890
# Hash: SHA-256
```

### Integrar en Generación de PDFs

```python
# En tu función de generación de PDFs:
def generar_pdf_con_watermark(movimiento):
    # ... código de generación de PDF ...

    # Agregar watermark con información de firmas
    for firma in movimiento.firmas:
        watermark = SignatureWatermark.generate_watermark_text({
            'timestamp': firma.timestamp_firma.isoformat(),
            'ip_address': firma.ip_address,
            'fingerprint': hashlib.sha256(firma.firma_base64.encode()).hexdigest()[:16]
        })

        # Agregar al PDF (depende de tu librería de PDFs)
        pdf.add_watermark(watermark, opacity=0.3)

    return pdf
```

---

## Seguridad y Consideraciones

### ⚠️ SECRET_KEY es Crítico

El sistema usa la `SECRET_KEY` de Flask para generar los HMAC. **NUNCA**:
- Compartas la SECRET_KEY en código público
- Uses una SECRET_KEY débil en producción
- Cambies la SECRET_KEY sin regenerar firmas (invalidaría todas)

**Recomendación**:
```bash
# En .env (producción)
SECRET_KEY=tu-clave-muy-segura-de-al-menos-64-caracteres-aleatorios-A1B2C3D4E5F6
```

### 🔒 Almacenamiento Seguro

Los hashes HMAC se guardan en `firmas.hash_documento`:
- Son únicos por firma
- No se pueden revertir (one-way)
- Permiten verificación sin exponer datos sensibles

### 📊 Logs de Auditoría

El sistema genera logs detallados:
```
[AUDITORIA_FIRMA_CRYPTO] timestamp=2025-12-11T10:30:00 |
movimiento_id=123 | tipo=Entrega | rol=Quien_Entrega |
firmante=Juan Pérez | ip=192.168.1.100 |
hmac_hash=a1b2c3d4e5f6... | verification_code=VER-0123-A1B2C3D4 |
fingerprint=1a2b3c4d5e6f7890 | consentimiento=True
```

Estos logs son **fundamentales** para cumplimiento legal y auditorías.

---

## Beneficios del Nuevo Sistema

### Antes (Sistema Antiguo)
- ❌ Hash SHA256 simple (cualquiera puede recalcularlo)
- ❌ Sin códigos de verificación
- ❌ No detectaba manipulaciones post-firma
- ❌ Sin validación criptográfica robusta

### Ahora (Sistema Nuevo)
- ✅ HMAC-SHA256 con SECRET_KEY (solo el servidor puede generar hashes válidos)
- ✅ Códigos de verificación únicos por firma
- ✅ Detección inmediata de manipulaciones
- ✅ Metadata completa con Builder pattern
- ✅ Watermarks para PDFs
- ✅ Invalidación automática de caché
- ✅ Endpoint de verificación dedicado
- ✅ Logs de auditoría mejorados

---

## Ejemplos de Uso Completo

### Ejemplo 1: Flujo Completo de Firma

```python
# 1. Usuario firma en el frontend
# 2. POST /movimientos/firmar/123
# 3. Backend procesa:

from app.signature_manager import create_signature_metadata, process_and_validate_signature

# Crear metadata
metadata = create_signature_metadata(
    document_id=123,
    signer_role='Quien_Entrega',
    signer_name='Juan Pérez',
    ip_address=get_client_ip(request),
    user_agent=request.headers.get('User-Agent'),
    consent=True
)

# Validar y procesar
success, error, processed_metadata, verification_code = process_and_validate_signature(
    signature_b64=request.json['signature'],
    signature_svg=request.json['signature_svg'],
    metadata=metadata
)

if success:
    # Guardar en BD
    firma = Firma(
        documento_id=123,
        tipo_documento='movimiento',
        rol_firma='Quien_Entrega',
        nombre_firmante='Juan Pérez',
        firma_base64=request.json['signature'],
        firma_svg=request.json['signature_svg'],
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        timestamp_firma=datetime.utcnow(),
        hash_documento=processed_metadata['integrity_hash'],  # HMAC-SHA256
        consentimiento_aceptado=True
    )
    db.session.add(firma)
    db.session.commit()

    # Invalidar caché
    invalidate_movimiento_cache(123)

    # Retornar código de verificación
    return jsonify({
        'success': True,
        'verification_code': verification_code
    })
```

### Ejemplo 2: Verificación Manual en Consola

```python
# Desde la consola de Flask:
from app.signature_manager import verify_stored_signature
from app.models import Firma

# Obtener firma
firma = Firma.query.filter_by(documento_id=123, rol_firma='Quien_Entrega').first()

# Verificar integridad
is_valid, error = verify_stored_signature(
    signature_b64=firma.firma_base64,
    stored_hash=firma.hash_documento,
    stored_metadata={
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
```

---

## Próximos Pasos Opcionales

### Mejoras Futuras Sugeridas

1. **Portal de Verificación Pública**
   - Página donde usuarios externos pueden verificar firmas
   - Solo con el código de verificación

2. **Blockchain Timestamping**
   - Integrar con blockchain para timestamps inmutables
   - Proof-of-existence sin depender de APIs centralizadas

3. **Certificados Digitales**
   - Permitir firmas con certificados X.509
   - Validación PKI completa

4. **Notificaciones por Email**
   - Enviar código de verificación por email al firmar
   - Recordatorio de firmas pendientes

---

## Soporte Técnico

### Archivos Principales

- `app/signature_manager.py`: Sistema completo de firmas
- `app/movimientos/routes.py`: Integración en rutas
- `app/pdf_cache.py`: Sistema de caché
- `app/models.py`: Modelo `Firma` en BD

### Logs de Depuración

Los logs se encuentran en:
- Logs de aplicación Flask (según configuración)
- Buscar por: `[AUDITORIA_FIRMA_CRYPTO]`

### Testing

```python
# Pruebas unitarias recomendadas:
def test_signature_validation():
    from app.signature_manager import SignatureProcessor
    processor = SignatureProcessor()

    # Test 1: Firma válida
    success, hash, metadata, code = processor.process_new_signature(...)
    assert success == True

    # Test 2: Firma vacía
    success, hash, metadata, code = processor.process_new_signature('', None, {})
    assert success == False
```

---

## Changelog

### v2.0 - Sistema Avanzado de Firmas (2025-12-11)

**Añadido**:
- Sistema completo `signature_manager.py`
- Validación HMAC-SHA256
- Códigos de verificación únicos
- Endpoint `/verificar` para integridad
- Invalidación automática de caché
- Logs de auditoría mejorados
- Watermarks para PDFs
- Patrones de diseño (Builder, Facade)

**Mejorado**:
- `firmar_movimiento`: Integración con SignatureProcessor
- `eliminar_firma`: Invalidación de caché
- Metadata estructurado con Builder pattern

**Seguridad**:
- HMAC-SHA256 en lugar de SHA256 simple
- Detección de manipulación post-firma
- No-repudio garantizado

---

## Conclusión

El nuevo sistema de firmas digitales proporciona una solución **robusta, segura y sin dependencias externas** para la gestión de firmas electrónicas. Cumple con las mejores prácticas de seguridad y arquitectura de software, garantizando la integridad de las firmas a lo largo del tiempo.

**Recuerda**: Este sistema es tan seguro como tu `SECRET_KEY`. Protégela como si fuera la contraseña de tu banco.

---

**Documentación generada automáticamente**
**Fecha**: 2025-12-11
**Versión**: 2.0
**Autor**: Sistema JeroSmart Activos Fijos
