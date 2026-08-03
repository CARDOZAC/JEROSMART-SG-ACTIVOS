# Especificación Backend JEROSMART ACTIVOS — Transcripción Python → PHP

Este documento describe **toda la lógica del backend** en Python (Flask) del proyecto JEROSMART ACTIVOS, con el nivel de detalle necesario para **transcribir o portar el sistema a PHP** por temas de costos y escalabilidad (hosting PHP más económico).

---

## Índice

1. [Estructura del proyecto](#1-estructura-del-proyecto)
2. [Configuración y entorno](#2-configuración-y-entorno)
3. [Base de datos: tablas y relaciones](#3-base-de-datos-tablas-y-relaciones)
4. [Autenticación y permisos (RBAC)](#4-autenticación-y-permisos-rbac)
5. [Módulos y lógica de negocio por ruta](#5-módulos-y-lógica-de-negocio-por-ruta)
6. [Servicios auxiliares (firmas, auditoría, email, caché, Excel/PDF)](#6-servicios-auxiliares)
7. [Flujos críticos paso a paso](#7-flujos-críticos-paso-a-paso)
8. [Equivalencias Python → PHP](#8-equivalencias-python--php)
9. [Motores gratuitos para transcripción (Sonnet y alternativas)](#9-motores-gratuitos-para-transcripción)

---

## 1. Estructura del proyecto

```
app/
├── __init__.py          # Factory Flask, blueprints, filtros Jinja2, init-db
├── config.py            # Configuración (DB, email, rutas, constantes)
├── models.py            # Modelos SQLAlchemy (todas las tablas)
├── extensions.py        # db, login_manager, migrate
├── permissions.py       # RBAC (permisos por rol, decoradores)
├── audit_helper.py      # Auditoría de movimientos (MovimientoHistorico)
├── email_service.py     # Notificaciones SMTP (aprobación, aprobado, rechazado)
├── excel_export.py      # Exportación Excel (inventario, movimientos, estadísticas)
├── pdf_cache.py         # Caché de PDFs por movimiento (invalidación)
├── signature_manager.py # Firmas digitales (HMAC-SHA256, metadata, verificación)
├── main/routes.py       # Dashboard (/), inventario_ajenos
├── auth/routes.py       # login, logout, forgot_password, reset_password
├── activos/routes.py    # CRUD activos, import/export CSV, Excel/PDF
├── activos_v2/          # Listado v2, detalle, mantenimiento, editar, API DataTables
├── movimientos/         # Dashboard, listado, crear, ver, PDF, firmas, eliminar
├── reportes/            # Depreciación, comodatos, movimientos, mantenimientos
├── proveedores/         # CRUD proveedores, importar CSV, API lista
├── biomedicos/          # Hojas de vida biomédicas, mantenimientos, PDFs
├── mantenimientos/      # Mantenimientos generales por activo
└── funcionarios/        # CRUD funcionarios, importar
```

---

## 2. Configuración y entorno

### 2.1 Variables de entorno (`.env`)

| Variable | Uso | Ejemplo |
|----------|-----|---------|
| `SECRET_KEY` | Sesiones, CSRF, HMAC firmas | Cadena larga aleatoria |
| `DB_TYPE` | `sqlite` o `mysql` | `mysql` |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | Conexión MySQL | — |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` | SMTP | `smtp.gmail.com`, 587 |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | Credenciales correo | — |
| `SUPERVISOR_EMAIL` | Fallback para notificaciones | — |
| `PDF_CACHE_ENABLED`, `PDF_CACHE_MAX_AGE_DAYS` | Caché PDFs | True, 30 |
| `TRUST_X_FORWARDED_FOR` | Proxy (nginx) | False |

### 2.2 Rutas de archivos (config)

- `UPLOAD_FOLDER` → `uploads/`
- `SIGNATURES_FOLDER` → `uploads/signatures`
- `HOJAS_DE_VIDA_FOLDER` → `uploads/hojas_de_vida`
- `MAINTENANCE_PHOTOS_FOLDER` → `uploads/maintenance_photos`
- `INVOICE_FOLDER` → `uploads/invoices`
- `PURCHASE_ORDER_FOLDER` → `uploads/purchase_orders`
- `LOAN_CONTRACT_FOLDER` → `uploads/loan_contracts`

### 2.3 Constantes de aplicación

- **ATRIBUTOS_POR_CLASE**: diccionario por `clase_id` (1=Biomédico, 2=Electrónico, 3=TICs, 4=Otros) con lista de atributos: `name`, `label`, `type`, `options` (si select), `required`.
- **ROLES_POR_MOVIMIENTO**: por tipo de movimiento (Entrega, Traslado, Entrada/Salida, Paz y Salvo) lista de roles de firma. La configuración detallada está en **firmas_requeridas.json**.

### 2.4 Archivo `firmas_requeridas.json`

Contiene por tipo de movimiento (clave normalizada: `entrega`, `traslado`, `entrada_salida`, `comodato`, `reporte_dano_perdida`) la lista de **roles de firma** requeridos y opcionalmente `_labels_spanish` para etiquetas en español. Los roles deben coincidir con las plantillas PDF.

---

## 3. Base de datos: tablas y relaciones

### 3.1 Motor y URI

- **MySQL**: `mysql+pymysql://USER:PASSWORD@HOST:PORT/DB_NAME?charset=utf8mb4`
- **SQLite**: `sqlite:///activos_fijos_v4.db`
- Pool MySQL: `pool_size=10`, `pool_recycle=3600`, `pool_pre_ping=True`, `max_overflow=20`

### 3.2 Tablas principales

| Tabla | Descripción | Columnas clave / FKs |
|-------|-------------|----------------------|
| **usuarios** | Login y roles | id, email (unique), clave_hash, rol, cargo, area |
| **funcionarios** | Empleados | id, nombres, apellidos, cedula (unique), cargo, area, centro_costo, estado |
| **proveedores** | Proveedores | id, razon_social (unique), nit (unique), direccion, persona_contacto, numero_contacto |
| **clases_activo** | Clases (Biomédico, TICs, etc.) | id, nombre_clase (unique) |
| **categoria_activo** | Categorías EAV | id, nombre, etc. |
| **atributo_definicion** | Definición atributos dinámicos | id, categoria_id, nombre, etiqueta, tipo_dato, valor_por_defecto, activo |
| **atributo_valor** | Valores EAV por activo | id, activo_id, atributo_definicion_id, valor, updated_at |
| **activos** | Activo fijo | id, nombre_activo, placa_codigo_interno (unique), marca, modelo, serie, ubicacion, observaciones, valor_comercial, estado, created_at, tipo_propiedad, origen_adquisicion, condicion_tenencia, atributos_dinamicos_json, propietario_ajeno, contacto_propietario, fecha_ingreso_ajeno, ruta_orden_compra, ruta_factura, ruta_contrato_arriendo, ruta_foto_activo, es_ingreso_temporal, fecha_inicio_temporal, fecha_fin_temporal, estado_conciliacion, fecha_ultima_verificacion, usuario_ultima_verificacion_id, notas_verificacion, categoria_id, clase_id, funcionario_id |
| **activo_accesorios** | Accesorios fijos del activo | id, activo_id, descripcion, cantidad |
| **hojas_vida_biomedicos** | Hoja de vida biomédica | id, activo_id (1:1), ... |
| **hojas_vida_equipos** | Hoja de vida equipos | id, activo_id, ... |
| **documentos_adjuntos_biomedicos** | Documentos (hoja_vida, activo, movimiento) | id, hoja_vida_id, activo_id, movimiento_id, ruta, tipo |
| **mantenimientos_biomedicos** | Mantenimientos históricos biomédicos | id, hoja_vida_id, ... |
| **mantenimientos_biomedicos_documentos** | Docs de mant. biomédico | id, mantenimiento_biomedico_id, ... |
| **auditoria_activos** | Auditoría legacy activos | id, activo_id, usuario_id, ... |
| **activo_historico** | Historial cambios en activos | id, activo_id, usuario_id, tipo_cambio, campo_modificado, valor_anterior, valor_nuevo, timestamp |
| **movimiento_historico** | Historial cambios en movimientos | id, movimiento_id, usuario_id, tipo_operacion (CREATE/UPDATE/DELETE/APROBACION/RECHAZO), campo_modificado, valor_anterior, valor_nuevo, ip_address, user_agent, timestamp, observaciones |
| **movimientos** | Cabecera movimiento | id, tipo_movimiento, fecha, usuario_id, funcionario_id, aprobado_por_id, estado_aprobacion (Pendiente/Aprobado/Rechazado), estado_completitud (borrador/completo), requiere_aprobacion, fecha_aprobacion, motivo_rechazo, observaciones_generales |
| **movimiento_activos** | Activos por movimiento + snapshot | id, movimiento_id, activo_id, valor_libros_momento, cantidad, observaciones |
| **accesorios** | Accesorios por movimiento_activo | id, movimiento_activo_id, descripcion, cantidad |
| **firmas** | Firmas digitales | id, documento_id, tipo_documento ('movimiento'), rol_firma, firma_base64, firma_svg, hash_documento, nombre_firmante, ip_address, user_agent, timestamp_firma, consentimiento_aceptado |
| **movimiento_documentos_adjuntos** | Adjuntos del movimiento | id, movimiento_id, ruta, descripcion |
| **detalle_entrega** | Detalle tipo Entrega | id, movimiento_id, proveedor_id, numero_factura, fecha_entrega, ... |
| **detalle_traslado** | Detalle tipo Traslado | id, movimiento_id, ubicacion_origen, ubicacion_destino, ... |
| **detalle_entrada_salida** | Detalle Entrada/Salida | id, movimiento_id, tercero_id, tipo_entrada_salida, ciudad, sede, fecha_retorno, motivo, ... |
| **detalle_paz_salvo** | Detalle Paz y Salvo | id, movimiento_id, funcionario_desvinculado_id, ... |
| **detalle_reporte_dano_perdida** | Detalle Reporte daño/pérdida | id, movimiento_id, descripcion_dano, ... |
| **detalle_comodato** | Detalle Comodato | id, movimiento_id, proveedor_id (opcional), fecha_inicio, fecha_fin, nit_comodante, numero_contrato, comodante, comodatario, objeto_comodato, ubicacion, responsable_interno, ... |
| **terceros** | Terceros (Entrada/Salida) | id, nombre, identificacion, ... |
| **mantenimiento_tipo** | Tipos de mantenimiento | id, nombre, ... |
| **mantenimientos** | Mantenimientos por activo | id, activo_id, tipo_id, usuario_id, fecha, descripcion, tecnico, costo, proximo_mantenimiento, estado |
| **mantenimiento_fotos** | Fotos del mantenimiento | id, mantenimiento_id, ruta |
| **mantenimiento_documentos** | Documentos del mantenimiento | id, mantenimiento_id, ruta, tipo |

### 3.3 Relaciones críticas

- **Movimiento** → una sola tabla de detalle según `tipo_movimiento`: Entrega → detalle_entrega, Traslado → detalle_traslado, etc.
- **Firma**: `tipo_documento='movimiento'`, `documento_id=movimiento.id`.
- **Activo**: depreciación calculada (no almacenada): línea recta, vida útil por clase (Biomédico desde atributo vida_util, TICs 5 años, resto 10). `valor_en_libros = valor_comercial - depreciacion_acumulada`.
- Eliminación **activo**: comprobar que no existan MovimientoActivo, Mantenimiento, AuditoriaActivo, HojaVidaBiomedico; luego borrar archivos y registro.
- Eliminación **movimiento**: primero registrar en movimiento_historico (DELETE), luego borrado en cascada (movimiento_activos, accesorios, detalle_*, firmas, documentos_adjuntos).

---

## 4. Autenticación y permisos (RBAC)

### 4.1 Usuario

- Flask-Login: sesión por `user_id`.
- Columnas: `email`, `clave_hash` (Werkzeug: generate_password_hash / check_password_hash).
- Roles: `Admin`, `Supervisor`, `Operador`, `Auditor`, `User`.

### 4.2 Permisos por rol (`PERMISOS_POR_ROL`)

- **Admin**: crear/editar/eliminar/ver movimiento, aprobar, rechazar, firmar, eliminar_firma, ver_reportes, exportar_datos, gestionar_usuarios, ver_auditoria, eliminar_activos, configurar_sistema.
- **Supervisor**: igual que Admin excepto gestionar_usuarios, eliminar_activos, configurar_sistema.
- **Operador**: crear/editar/ver movimiento, firmar, exportar_datos.
- **Auditor**: ver_movimiento, ver_reportes, exportar_datos, ver_auditoria.
- **User**: ver_movimiento, ver_reportes, exportar_datos.

### 4.3 Funciones de negocio

- **puede_editar_movimiento(movimiento)**: Admin todo; Supervisor propio o “área”; Operador solo propio y estado_completitud=='borrador'.
- **puede_eliminar_movimiento(movimiento)**: Admin todo; Supervisor/Operador solo borradores (Operador solo propios).
- **puede_aprobar_movimiento(movimiento)**: Usuario ≠ creador, estado_aprobacion=='Pendiente', y tiene permiso 'aprobar_movimiento'.

### 4.4 Decoradores

- `@login_required`: redirige a login si no autenticado.
- `@require_permission('permiso')`: 401/403 si no tiene permiso; para JSON devuelve `{ error: '...' }` y 401/403.
- `@require_any_permission('p1','p2')`: al menos uno.
- `@admin_required`: rol debe ser Admin.

### 4.5 Auth: login, logout, reset password

- **Login**: POST email + password; verificar con `check_password_hash`; login_user; redirigir.
- **Logout**: logout_user; redirigir.
- **Forgot password**: generar token con URLSafeTimedSerializer (salt `password-reset-salt`, max_age 3600); enviar enlace por email (si SMTP configurado).
- **Reset password**: GET/POST con token; validar token; actualizar contraseña con `set_password`; commit.

---

## 5. Módulos y lógica de negocio por ruta

### 5.1 Main

- **GET /** Dashboard: totales (activos, funcionarios, movimientos), últimos activos (fecha_ingreso_ajeno no null), activos por clase, movimientos por tipo, alertas activos ajenos (próximos 30 días).
- **GET /inventario_ajenos** Dashboard activos ajenos: lista, KPIs (total, comodato, costo mensual), alertas contratos 90 días, activos por propietario.

### 5.2 Activos (`/activos`)

- **GET /** Listado paginado: filtros `q`, `filtro_tipo`, `filtro_clase`, `filtro_estado`, `filtro_ubicacion`; join ClaseActivo, Funcionario.
- **GET/POST /nuevo** Crear activo (Admin): tipo_propiedad (Propio/Ajeno), archivos (contrato, OC, factura), atributos por clase; validación atributos dinámicos; ajenos: propietario, condicion_tenencia; ingreso temporal con fechas.
- **GET/POST /editar/<id>** Editar (Admin); mismos criterios.
- **POST /eliminar/<id>** (Admin) Comprobar que no existan MovimientoActivo, Mantenimiento, AuditoriaActivo, HojaVidaBiomedico; borrar archivos y registro.
- **GET /detalle/<id>** Detalle + movimientos y mantenimientos recientes, hoja de vida si existe.
- **GET /api/buscar-funcionarios** Parámetros: `q`, `page`, `limit` → JSON.
- **GET /api/clases** Lista clases JSON.
- **GET /api/clase_atributos/<clase_id>** Atributos dinámicos de la clase.
- **GET /descargar-plantilla-csv**, **GET/POST /importar-activos** CSV estándar; placa única; clase_id opcional.
- **GET /descargar-plantilla-ajenos-csv**, **GET/POST /importar-ajenos** CSV activos ajenos.
- **GET /exportar-inventario-excel** Filtros: exportar_todo, fecha_desde, fecha_hasta; usa `excel_export.exportar_inventario_excel`.
- **GET /exportar-inventario-pdf** Mismo filtro; ReportLab, landscape.

### 5.3 Activos V2 (`/activos-v2`)

- **GET /listado** Paginación y filtros: nombre, placa, clase_id, ubicacion_id, estado; estadísticas total/operativos.
- **GET /<id>/detalle** Detalle + mantenimientos + últimos movimientos + formulario mantenimiento.
- **POST /<activo_id>/mantenimiento/nuevo** Alta mantenimiento: tipo, fecha, descripción, técnico, costo, próximo mantenimiento, fotos.
- **GET/POST /<id>/editar** Edición activo; atributos dinámicos; subida orden_compra, factura, documento_soporte.
- **POST /api/datatable** Server-side DataTables: draw, start, length, search, filtros.
- **GET /api/clase/<clase_id>/atributos**, **GET /api/funcionarios/search** q → JSON.
- **POST /<id>/eliminar** Solo Admin.
- **GET /exportar-inventario-excel**, **GET /exportar-inventario-pdf** Igual que en activos.

### 5.4 Movimientos (`/movimientos`)

- **GET /dashboard** Estadísticas: totales, mes actual, pendientes aprobación, aprobados mes, valor total mes, por tipo, tendencia 6 meses, por estado, usuarios más activos, activos más movidos, recientes.
- **GET /** Listado paginado; filtros `q` (observaciones), `tipo`; subconsulta conteo activos por movimiento.
- **GET /<movimiento_id>** Detalle; detalle según tipo; activos con accesorios; firmas; usuario registra.
- **GET/POST /nuevo** Wizard: tipo, fecha/hora, activos_data (JSON), accesorios_data (JSON), firmas_data (JSON); snapshot valor_libros_momento por activo; si valor total > 5.000.000 COP → requiere_aprobacion, estado Pendiente y email a supervisor; crear detalle según tipo; auditoría CREATE; proveedor "No Aplica" opcional.
- **GET /<movimiento_id>/pdf** PDF acta (WeasyPrint); plantillas por tipo; contexto: movimiento, activos, detalles, firmas; usar caché si está habilitado (get_pdf_from_cache_or_generate).
- **GET /plantillas-pdf**, **GET /plantillas-pdf/<tipo>** PDFs de ejemplo.
- **POST /eliminar/<id>** Con permiso; registrar_eliminacion_movimiento; borrado en cascada.
- **GET/POST /firmar/<movimiento_id>** GET: roles desde firmas_requeridas.json, firmas guardadas. POST JSON: rol_firma, nombre_firmante, signature (base64), signature_svg, metadata, consentimiento; IP y User-Agent; signature_manager: create_signature_metadata, process_and_validate_signature; guardar/actualizar Firma; invalidate_movimiento_cache.
- **POST /firmar/<movimiento_id>/<rol_firma>/eliminar** Solo Admin/Supervisor; invalidar caché.
- **GET /firmar/<movimiento_id>/<rol_firma>/verificar** Verificación HMAC; JSON valid y detalles.
- **GET /api/buscar_activos** term → autocompletado activos.
- **GET /api/tercero** id → JSON tercero.

Validaciones Entrada/Salida: ciudad, sede, tercero, fecha retorno si Salida, motivo "Otro". Comodato: fechas, NIT, número contrato, comodante/comodatario, objeto, ubicación, responsable. Sanitizar `q` en búsquedas.

### 5.5 Reportes (`/reportes`)

- **GET /** Índice; gráficos (activos por clase, movimientos por tipo) Chart.js.
- **GET/POST /depreciacion** Reporte depreciación activos propios (valor_comercial > 0); POST action=generate_pdf → WeasyPrint PDF.
- **GET /comodatos/dashboard** Métricas comodatos (vigentes, próximos 30 d, vencidos, valor total, por comodante); alertas.
- **GET /comodatos/listado** Filtros estado, comodante, fecha_desde/hasta, q.
- **GET /comodatos/exportar/excel** Excel 3 hojas: Comodatos, Resumen por Comodante, Alertas.
- **GET /comodatos/exportar/pdf** PDF listado comodatos.
- **GET /comodatos/api/alertas** JSON alertas.
- **GET /movimientos/dashboard** Filtros clase, tipo_movimiento, fecha_desde/hasta; métricas por tipo, clase, estado aprobación.
- **GET /movimientos/exportar/excel** Excel movimientos con mismos filtros.
- **GET /mantenimientos/dashboard** Filtros clase, tipo_mantenimiento, estado, fecha_desde/hasta.
- **GET /mantenimientos/exportar/excel** Excel mantenimientos.

### 5.6 Proveedores (`/proveedores`)

- **GET /** Listado con búsqueda (razon_social, nit, persona_contacto), paginación.
- **GET/POST /nuevo** (Admin) NIT y razón social únicos.
- **GET/POST /editar/<id>** (Admin) Comprobar duplicados al cambiar.
- **POST /eliminar/<id>** (Admin) Si no tiene DetalleEntrega.
- **GET/POST /importar** (Admin) CSV: Nombre Del Proveedor, NIT, Persona De Contacto, Teléfono, Dirección.
- **GET /descargar-plantilla-csv**, **GET /api/lista** JSON id, nombre, nit.

### 5.7 Biomédicos (`/biomedicos`)

- Gestión biomédicos (clase_id=1); mantenimientos pendientes e históricos; wizard mantenimiento; cargar histórico (PDF); detalle mantenimiento; hojas de vida; formatos; PDFs (hoja vida consolidada, actas mantenimiento).

### 5.8 Mantenimientos y Funcionarios

- Mantenimientos: rutas por activo; integración con activos y reportes.
- Funcionarios: CRUD; importación; usado en activos (responsable) y movimientos (Paz y Salvo, búsquedas).

---

## 6. Servicios auxiliares

### 6.1 Firmas digitales (`signature_manager.py`)

- **SignatureValidator**: HMAC-SHA256 con SECRET_KEY. Mensaje: signature_data | timestamp | ip_address | user_agent[:100] | document_id | signer_role. generate_signature_hash(signature_data, metadata) → hex; verify_signature_integrity(signature_data, metadata, expected_hash) → bool (usar compare_digest).
- **SignatureMetadataBuilder**: Builder con with_timestamp, with_ip_address, with_user_agent ([:500]), with_document_id, with_signer_role, with_signer_name, with_consent; build() → dict.
- **SignatureProcessor**: process_new_signature(signature_b64, signature_svg, metadata) → (success, integrity_hash, processed_metadata); validar base64; verify_signature(signature_b64, stored_hash, metadata) → (is_valid, error_message).
- **SignatureWatermark**: generate_verification_code(movimiento_id, firma_hash) → "VER-{id:04d}-{8 chars hex}"; generate_watermark_text(metadata) → texto para PDF.
- **Funciones helper**: create_signature_metadata(document_id, signer_role, signer_name, ip_address, user_agent, consent); process_and_validate_signature(...) → (success, error_msg, processed_metadata, verification_code); verify_stored_signature(signature_b64, stored_hash, stored_metadata) → (is_valid, error_message).

En PHP: equivalente con `hash_hmac('sha256', $message, $secret_key)` y comparación segura de hashes.

### 6.2 Auditoría (`audit_helper.py`)

- **registrar_auditoria_movimiento(movimiento, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, observaciones)**: crea MovimientoHistorico con ip_address (request), user_agent[:500], usuario_id (current_user); db.session.add; sin commit.
- **registrar_creacion_movimiento(movimiento, observaciones)**.
- **registrar_aprobacion_movimiento(movimiento, aprobador, observaciones)**.
- **registrar_rechazo_movimiento(movimiento, motivo, observaciones)**.
- **registrar_eliminacion_movimiento(movimiento_id, tipo_movimiento, usuario_email)**: llamar ANTES de eliminar; flush después de add.
- **obtener_historial_movimiento(movimiento_id, limit=50)** → lista ordenada por timestamp desc.

### 6.3 Email (`email_service.py`)

- **enviar_email(to, subject, html, pdf=None, pdf_filename=None)**: arma MIMEMultipart; envía en Thread con app_context; si no hay MAIL_USERNAME/MAIL_PASSWORD no envía (solo log).
- **notificar_aprobacion_pendiente(movimiento, supervisor_email, url_base)**: template HTML con datos movimiento, valor total, url_aprobacion.
- **notificar_movimiento_aprobado(movimiento, url_base)** al creador.
- **notificar_movimiento_rechazado(movimiento, url_base)** al creador.
- **obtener_email_supervisor()**: User con rol Supervisor o Admin; fallback SUPERVISOR_EMAIL.

### 6.4 Caché PDF (`pdf_cache.py`)

- **PDFCacheManager**: directorio `uploads/pdf_cache`; max_age_days (config); enabled (PDF_CACHE_ENABLED).
- **_generate_cache_key(movimiento)**: dict con id, tipo, fecha, estado_aprobacion, num_activos, observaciones_hash, firmas hashes; JSON sort_keys; SHA256.
- **get_cached_pdf(movimiento)**: si no enabled return None; path por clave; si no existe o antigüedad > max_age_days → eliminar si aplica y return None; sino leer bytes y return.
- **save_pdf_to_cache(movimiento, pdf_content)**.
- **invalidate_cache(movimiento_id)**: glob mov_{id}_*.pdf; unlink; return deleted_count.
- **cleanup_old_files(days)**, **get_cache_stats()**, **clear_all_cache()**.
- **get_pdf_from_cache_or_generate(movimiento, generator_func)**: get_cached_pdf; si no, generator_func(), save_pdf_to_cache, return.
- **invalidate_movimiento_cache(movimiento_id)**.

### 6.5 Excel (`excel_export.py`)

- openpyxl: Workbook, estilos (Font, PatternFill, Alignment, Border), get_column_letter.
- **exportar_movimientos_excel(movimientos, filtros)** → BytesIO; título, fecha gen, filtros, headers, filas por movimiento (valor total por suma valor_libros_momento).
- **exportar_inventario_excel**: similar con columnas de inventario.
- Otras funciones para movimiento detallado y estadísticas. Reportes comodatos/mantenimientos pueden usar openpyxl directo en rutas.

### 6.6 PDF

- Movimientos: WeasyPrint con plantillas HTML por tipo de movimiento.
- Reportes: WeasyPrint (depreciación, comodatos); ReportLab para inventario PDF (landscape).

---

## 7. Flujos críticos paso a paso

### 7.1 Crear movimiento

1. Validar tipo y datos según tipo (detalle Entrega/Traslado/Comodato/Entrada-Salida/Paz y Salvo/Reporte daño).
2. Obtener activos desde activos_data; para cada uno calcular valor_en_libros (snapshot) y guardar en movimiento_activos con valor_libros_momento.
3. Crear cabecera Movimiento (estado_completitud, estado_aprobacion, requiere_aprobacion si valor total > 5M).
4. Crear registro en detalle_* según tipo.
5. Crear accesorios desde accesorios_data por movimiento_activo.
6. registrar_creacion_movimiento(movimiento).
7. Si requiere_aprobacion: obtener_email_supervisor(); notificar_aprobacion_pendiente(movimiento, email, url_base).
8. Commit.

### 7.2 Firmar movimiento

1. GET: cargar movimiento; leer firmas_requeridas.json para tipo; devolver roles requeridos y firmas ya guardadas.
2. POST: recibir rol_firma, nombre_firmante, signature (base64), signature_svg, consentimiento; ip, user_agent.
3. metadata = create_signature_metadata(movimiento.id, rol_firma, nombre_firmante, ip, user_agent, consentimiento).
4. success, error_msg, processed_metadata, verification_code = process_and_validate_signature(signature, signature_svg, metadata).
5. Si no success → JSON error 400.
6. Buscar o crear Firma (documento_id=movimiento.id, tipo_documento='movimiento', rol_firma); asignar firma_base64, firma_svg, hash_documento=integrity_hash, nombre_firmante, ip_address, user_agent, timestamp_firma, consentimiento_aceptado.
7. invalidate_movimiento_cache(movimiento.id).
8. Commit; respuesta JSON success y opcionalmente verification_code.

### 7.3 Generar PDF acta

1. Obtener movimiento con activos, detalle, firmas.
2. pdf_content = get_pdf_from_cache_or_generate(movimiento, lambda: generar_acta_xxx_pdf(movimiento)).
3. Response send_file con pdf_content, mimetype application/pdf, nombre archivo.

### 7.4 Eliminar movimiento

1. Verificar puede_eliminar_movimiento(movimiento).
2. registrar_eliminacion_movimiento(movimiento.id, movimiento.tipo_movimiento, current_user.email).
3. Eliminar en orden (o cascada): firmas, movimiento_documentos_adjuntos, accesorios, movimiento_activos, detalle_*, movimiento.
4. invalidate_movimiento_cache(movimiento.id) si se hace después.
5. Commit.

---

## 8. Equivalencias Python → PHP

| Python (Flask) | PHP |
|----------------|-----|
| Flask app, blueprints | Framework: Laravel / Slim / PHP puro con router |
| SQLAlchemy, db.session | PDO + capa de modelos; o Eloquent (Laravel) |
| request.args, request.form, request.get_json() | $_GET, $_POST, json_decode(file_get_contents('php://input')) |
| request.files | $_FILES |
| redirect(url_for('x')) | header('Location: ...') o helper de framework |
| jsonify({...}) | echo json_encode(...); header Content-Type application/json |
| send_file( BytesIO, mimetype, as_attachment, download_name) | header Content-Type; header Content-Disposition; echo $bytes |
| current_user, login_required | Sesión con user_id; middleware de autenticación |
| render_template | include/require de vistas o motor de plantillas (Twig, Blade) |
| flash('msg','category') | Sesión flash o similar |
| Config from os.environ | getenv() o $_ENV; archivo .env con parse (vlucas/phpdotenv) |
| hashlib, hmac | hash_hmac('sha256', $data, $key), hash('sha256', $data) |
| Werkzeug generate_password_hash / check_password_hash | password_hash(PASSWORD_DEFAULT), password_verify() |
| URLSafeTimedSerializer | Token manual con hash_hmac + timestamp; o librería JWT |
| Thread para email | Encolar correo o enviar con sendmail/PHPMailer en segundo plano (cron o queue) |
| WeasyPrint / ReportLab | TCPDF, Dompdf, o FPDF para PDF; o mantener WeasyPrint vía CLI desde PHP |
| openpyxl | PhpSpreadsheet |

---

## 9. Motores gratuitos para transcripción Python → PHP

Objetivo: usar un motor de IA **gratuito** (o con tier gratis) para que, dado este documento y fragmentos de código Python, genere código PHP equivalente.

### 9.1 Opciones gratuitas recomendadas

| Motor | Gratis / Límite | Uso recomendado |
|-------|------------------|------------------|
| **Claude (Anthropic)** | Cuenta gratuita con límite de mensajes/mes | Muy bueno para código y transcripción; puedes pegar este .md y pedir “traduce este endpoint a PHP”. |
| **Google Gemini** | Tier gratuito generoso (Gemini 1.5 Flash / Pro) | Bueno para código; en Google AI Studio puedes pegar el .md y pedir transcripción a PHP. |
| **OpenAI ChatGPT** | Tier gratuito con límites | Útil para bloques pequeños; para proyectos grandes puede quedarse corto. |
| **Groq** | API gratuita con límites (muy rápida) | Usar con modelo Llama para tareas de código; ideal para muchas solicitudes pequeñas. |
| **Ollama (local)** | 100% gratis, corre en tu PC | Modelos Llama, CodeLlama, etc.; sin costo de API; mejor para fragmentos y no para documentos enormes de una vez. |
| **Mistral** | Tier gratuito en la plataforma | Buen equilibrio para código. |
| **Sonnet (Claude Sonnet)** | Dentro del plan de Anthropic / o vía Cursor/otros | Si tienes acceso a “Sonnet” como motor dentro de una herramienta (p. ej. Cursor con Claude), se elige desde la configuración del chat o del agente. |

“Sonnet” suele referirse a **Claude Sonnet** de Anthropic. Para usarlo **gratis**:

- Crear cuenta en **Anthropic** (console.anthropic.com) y usar los créditos gratuitos que dan al inicio, o  
- Usar **Cursor** (o otro IDE) que integre Claude: en la configuración del chat eliges el modelo “Claude Sonnet” si está disponible en tu plan.  
- **Google Gemini** es una alternativa muy sólida y gratuita: da acceso a modelos potentes para código sin costo.

### 9.2 Paso a paso genérico para usar un motor gratuito en esta tarea

1. **Tener el documento de especificación**  
   Este archivo (`ESPECIFICACION_BACKEND_PYTHON_A_PHP.md`) es la “fuente de verdad”. Guárdalo en la raíz del proyecto (o en una carpeta `docs/`).

2. **Elegir el motor**  
   - **Gemini**: entra a [Google AI Studio](https://aistudio.google.com) → inicia sesión → “Create new prompt” → pega secciones de este .md y pide: “Traduce esta lógica a PHP (Laravel/Slim/PDO)”.  
   - **Claude**: en [Anthropic Console](https://console.anthropic.com) o en Cursor (si tienes Claude disponible) abre un chat, pega el .md o la sección (p. ej. “Servicios auxiliares – Firmas”) y pide la transcripción a PHP.  
   - **Sonnet en Cursor**: en Cursor, en el selector de modelo del chat (donde dice “Claude”, “GPT”, etc.) elige “Claude Sonnet” si aparece; luego pega el fragmento y pide “Traduce a PHP manteniendo la misma lógica”.

3. **Dividir por módulos**  
   No pidas “traduce todo el backend” de una vez. Pide por partes, por ejemplo:  
   - “A partir de la sección 6.1 (Firmas digitales), escribe el equivalente en PHP (funciones y uso de hash_hmac).”  
   - “A partir de la sección 5.4 (Movimientos), traduce el flujo de creación de movimiento a PHP con PDO.”

4. **Incluir contexto**  
   En cada prompt indica: “El backend actual es Flask + SQLAlchemy; en PHP usamos PDO (o Laravel) y MySQL. Mantén nombres de tablas y columnas igual que en el documento.”

5. **Revisar y probar**  
   El motor puede equivocarse en detalles (nombres de variables, orden de commits). Revisa siempre: permisos, transacciones, escape de datos y comparación segura de hashes en firmas.

### 9.3 Si tienes una captura de Gemini (imagen)

Si envías una **captura de pantalla** donde Gemini te indica cómo elegir Sonnet o cómo usar su interfaz, puedo darte un **paso a paso exacto** sobre esa pantalla (por ejemplo: “clic en el menú X → luego en Model → elegir Sonnet”). Mientras tanto, con la cuenta gratuita de **Google AI Studio** puedes usar **Gemini** directamente para esta tarea de transcripción sin pagar.

---

## Resumen final

- Este documento describe **toda la lógica del backend** de JEROSMART ACTIVOS en Python: estructura, config, tablas, RBAC, rutas por módulo, servicios de firmas, auditoría, email, caché y Excel/PDF, y flujos críticos.
- Sirve como **especificación única** para portar el sistema a PHP manteniendo tablas y comportamiento.
- Para la transcripción con IA, usa este .md por secciones en **Gemini**, **Claude (Sonnet)** o **Otro motor gratuito**, indicando siempre “traducir a PHP” y el stack objetivo (PDO, Laravel, etc.).
- Si compartes la imagen de la interfaz de Gemini (o de Cursor/Claude) donde se elige el modelo, se puede detallar el paso a paso exacto en esa pantalla.
