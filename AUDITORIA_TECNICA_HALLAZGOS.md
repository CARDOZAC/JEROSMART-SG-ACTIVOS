# Auditoría Técnica — JeroSmart Activos

**Fecha:** 2026-08-03
**Stack auditado:** Python 3.12 · Flask 3.0 · SQLAlchemy (Flask-SQLAlchemy) · MySQL 8 (PyMySQL) · WeasyPrint · Jinja2
**Alcance:** `app/` completo (modelos, 10 blueprints, helpers), configuración, migración SQLite→MySQL.

Cada hallazgo tiene un ID (`FIX-xx` = ya corregido en esta sesión, `TASK-xx` = pendiente, para hacer parte por parte). Severidad: 🔴 Crítico · 🟠 Alto · 🟡 Medio · 🔵 Bajo.

---

## 1. Migración SQLite → MySQL (solicitado)

### ✅ FIX-01 🟠 — Eliminado `app/database.py` (código SQLite muerto)
- **Archivo:** `app/database.py` (ELIMINADO)
- Contenía una clase `Database` basada en `import sqlite3` + `sqlite3.connect(config['DATABASE_PATH'])` + `sqlite3.Row`. **Nadie lo importaba** (verificado con grep en todo `app/`): era código muerto de la era SQLite. `DATABASE_PATH` ni siquiera existe en `Config`.

### ✅ FIX-02 🟠 — `app/config.py`: eliminada la rama SQLite, MySQL es ahora el único motor
- **Archivo:** `app/config.py:41-69` (antes)
- Antes: `DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')` con fallback a `sqlite:///activos_fijos_v4.db`. Si el `.env` no cargaba (p. ej. ejecutando desde otro directorio de trabajo), la app arrancaba **silenciosamente contra SQLite** creando una BD paralela vacía — causa clásica de "mis datos desaparecieron".
- Ahora: `SQLALCHEMY_DATABASE_URI` se construye siempre como `mysql+pymysql://...?charset=utf8mb4` con pool (`pool_pre_ping`, `pool_recycle=3600`). La variable `DB_TYPE` del `.env` ya no se usa (puedes borrarla del `.env`).

### Estado de compatibilidad MySQL del resto del código (verificado, sin cambios necesarios)
- No hay SQL crudo con sintaxis SQLite (`strftime`, `julianday`, `PRAGMA`, `AUTOINCREMENT`, `IFNULL`, `GROUP_CONCAT`): todos los `strftime` encontrados son de Python (`datetime.strftime`), no de SQL. ✔
- `app/models.py:11` usa `from sqlalchemy.dialects.mysql import LONGTEXT` para `Firma.firma_base64` — correcto ahora que el motor es solo MySQL. ✔
- Columnas `db.JSON` mapean al tipo nativo `JSON` de MySQL 5.7+. ✔
- `db.CheckConstraint` en `DocumentoAdjunto` requiere **MySQL ≥ 8.0.16** (antes se ignora silenciosamente). ✔ si tu servidor es 8.x.

### ✅ TASK-01 🔴 — Credenciales reales de MySQL versionadas en git *(resuelto a nivel de repo)*
- **Archivo:** `.env` (estaba trackeado en git)
- Contenía `DB_USER=root` con la contraseña de root en texto plano (aquí redactada) y un `SECRET_KEY` placeholder (`cambia-por-clave-segura-...`). Con ese placeholder, **cualquiera que leyera el repo podía firmar cookies de sesión válidas** y suplantar a un Admin: era tan grave como la contraseña expuesta.
- ⚠️ La misma contraseña de root aparece en texto plano en otros archivos **versionados**: `.env.ejemplo`, `actualizar_ubicaciones.bat`, `eliminar_activos_ajenos.bat` y `.claude/settings.local.json`. Al rotar la credencial hay que limpiarlos todos, no solo el `.env`.
- **Aplicado:**
  - `git rm --cached .env` — el archivo sigue en disco pero ya no se versiona (`.env` ya figuraba en `.gitignore`, por eso nunca debió estar trackeado).
  - `SECRET_KEY` real de 64 hex generado con `secrets.token_hex(32)` y escrito en `.env`. *(Efecto esperado: las sesiones abiertas se invalidan, hay que volver a iniciar sesión.)*
  - `DB_TYPE` eliminado del `.env` (ya no se lee tras FIX-02).
  - Nuevo **`.env.example`** versionado, con la plantilla de variables y el SQL para crear un usuario MySQL dedicado.
  - `.gitignore` ampliado: `uploads/`, `temp_migrate*.py`, `query`, `nul`, `*.db`.
- **Pendiente (requiere tu acción, no la puedo hacer yo):**
  1. **Rotar la contraseña de MySQL** y migrar de `root` a un usuario dedicado:
     ```sql
     CREATE USER 'jerosmart'@'localhost' IDENTIFIED BY '<password-fuerte>';
     GRANT ALL PRIVILEGES ON jerosmart_activos.* TO 'jerosmart'@'localhost';
     FLUSH PRIVILEGES;
     ```
     y actualizar `DB_USER`/`DB_PASSWORD` en `.env`.
  2. **Purgar el `.env` del historial** con `git filter-repo` o BFG — sigue siendo recuperable en commits anteriores. Mientras no se purgue, la contraseña vieja debe considerarse comprometida.

### ✅ TASK-02 🟡 — Esquema MySQL sincronizado con los modelos
- **Diagnóstico real (MySQL 8.0.44, 36 tablas):**
  - La BD estaba en la revisión Alembic `052bdc72c29f` con **una migración sin aplicar**. Faltaba por completo la tabla **`movimiento_historico`** → todo el módulo `audit_helper.py` fallaba en silencio (sus `except` tragaban el error): **no se estaba registrando ninguna auditoría de movimientos**, ni creación, ni aprobación, ni eliminación.
  - `Funcionario.estado` **sí existe** en la BD (`SHOW COLUMNS` lo confirma). El comentario de `app/funcionarios/routes.py:133` que afirmaba lo contrario era obsoleto y despistaba; se corrigió. Los endpoints `/funcionarios/api/lista` y `/api/search` funcionan.
- **Aplicado:** `flask db upgrade` → `052bdc72c29f` → `a1b2c3d4e5f6` (tabla `movimiento_historico` + 5 índices) y luego → `b58456050078` (TASK-03). Head actual: **`b58456050078`**.
- **Deriva restante (verificada con `alembic.autogenerate.compare_metadata`, toda cosmética, sin impacto funcional):**
  - 3 tablas huérfanas en la BD que ningún modelo declara: `activos_legacy_historial`, `activos_fotos`, `activos_legacy_temporal`. **Las 3 están vacías (0 filas).** No las borré: eliminar tablas es irreversible y podrían usarlas scripts externos. Decisión tuya.
  - Diferencias de nombres de índices/FK y comentarios en `hojas_vida_equipos` y `mantenimientos_biomedicos_documentos` (creadas con SQL a mano vs. definición del modelo), y una columna extra inofensiva `mantenimientos_biomedicos_documentos.updated_at`.
  - ⚠️ **No ejecutes `flask db migrate` a ciegas:** el autogenerate propone `DROP TABLE` sobre esas 3 tablas legacy. Por eso la migración de TASK-03 se escribió a mano.

---

## 2. Bugs corregidos en esta sesión

### ✅ FIX-03 🔴 — Módulo biomédico completo SIN autenticación
- **Archivo:** `app/biomedicos/routes.py` (1496 líneas, ~30 rutas)
- **Ninguna** ruta tenía `@login_required` (grep: 0 ocurrencias). Cualquier persona sin sesión podía ver hojas de vida, crear/editar/borrar mantenimientos y descargar documentos accediendo a `/biomedicos/...`.
- **Fix aplicado:** guard a nivel de blueprint `@biomedicos_bp.before_request` que exige `current_user.is_authenticated` para todas las rutas del módulo (JSON → 401, HTML → redirect a login).

### ✅ FIX-04 🔴 — PDF de "Reporte de Daño o Pérdida" siempre devolvía error 501
- **Archivo:** `app/movimientos/routes.py` (`generar_acta_pdf`, PASO 5)
- El mapeo de plantillas (líneas ~1114-1129) solo cubría Traslado/Entrega/Entrada-Salida/Paz y Salvo. Para "Reporte de Daño o Pérdida", `template_name` quedaba `None` y la función retornaba `501` en la línea ~1131 **antes** de llegar al bloque `elif tipo == 'Reporte de Daño o Pérdida'` de PASO 7 (línea ~1253), que era código inalcanzable. "Comodato" ni siquiera tenía plantilla asignada.
- **Fix aplicado:** se agregaron ambos tipos al mapeo de PASO 5 (`acta_reporte_dano_perdida.html`, `acta_comodato.html`).
- ⚠️ **Verificar** que exista `app/templates/pdf_templates/acta_comodato.html` (la ruta de plantillas de ejemplo ya lo referenciaba).

### ✅ FIX-05 🔴 — Asistente de firmas roto para "Paz y Salvo" y "Reporte de Daño o Pérdida"
- **Archivo:** `app/movimientos/routes.py` (`firmar_movimiento`, GET) y `firmas_requeridas.json`
- Dos bugs encadenados:
  1. La clave se calculaba como `tipo.lower().replace('/', '_')` → `"paz y salvo"` y `"reporte de daño o pérdida"` (con espacios y tildes). El JSON usa `paz_y_salvo`/`reporte_dano_perdida`, y además **no existía la entrada `paz_y_salvo`** → `roles_requeridos = []`, el wizard de firmas no mostraba ningún rol.
  2. `getattr(movimiento, f"detalle_{tipo.lower().replace('/','_')}")` generaba nombres de atributo inválidos (`detalle_paz y salvo`) → `detalles` siempre `None` en la vista de firmas.
- **Fix aplicado:** mapeo explícito `TIPO_MOV_KEY_MAP` y `DETALLE_ATTR_MAP_FIRMAS`; se agregó la sección `"paz_y_salvo"` a `firmas_requeridas.json` (roles: `Funcionario`, `Jefe_Inmediato`, `VoBo_Activos_Fijos`, coherentes con `Config.ROLES_POR_MOVIMIENTO`) y su etiqueta en `_labels_spanish`.

### ✅ FIX-06 🟠 — `Activo.to_dict_completo()` lanzaba `AttributeError`
- **Archivo:** `app/models.py:389-391`
- Referenciaba `self.fecha_ingreso` (columna inexistente en `Activo`; la real es `created_at`) y `self.funcionario.nombre_completo` (propiedad que `Funcionario` no tenía).
- **Fix aplicado:** usa `created_at` y se añadió `@property nombre_completo` a `Funcionario` (reutilizable en plantillas y reportes).

### ✅ FIX-07 🟠 — Auditoría EAV registraba mal e incluso crasheaba
- **Archivo:** `app/models.py` (`Activo.set_atributo_valor`)
- Dos bugs:
  1. `valor_anterior=str(valor_obj.valor)` se capturaba **después** de sobrescribir `valor_obj.valor = valor` → el historial siempre guardaba `valor_anterior == valor_nuevo`.
  2. Se construía `ActivoHistorico(tipo_cambio=..., descripcion_cambio=...)` con kwargs que **no son columnas** del modelo (`ActivoHistorico` tiene `tipo_operacion` y `observaciones`) → `TypeError` en runtime cada vez que se pasaba `usuario_id`.
- **Fix aplicado:** captura de `valor_anterior` antes de la asignación y kwargs correctos (`tipo_operacion='UPDATE'`, `observaciones=...`).

### ✅ FIX-08 🟠 — `AtributoDefinicion.validar_valor` con `isinstance` inválido para fechas
- **Archivo:** `app/models.py:1802`
- `isinstance(valor, datetime.date)` — como `datetime` es la **clase** (importada con `from datetime import datetime`), `datetime.date` es un method descriptor, no un tipo → `TypeError: isinstance() arg 2 must be a type` al validar cualquier atributo tipo fecha con valor `date`.
- **Fix aplicado:** `from datetime import datetime, date` + `isinstance(valor, (date, datetime))`.

### ✅ FIX-09 🟠 — Detalle de activo nunca mostraba los atributos dinámicos
- **Archivo:** `app/activos/routes.py` (`detalle_activo`)
- `json.loads(activo.atributos_dinamicos_json)`: la columna es `db.JSON`, SQLAlchemy ya entrega un `dict`; `json.loads(dict)` lanza `TypeError`, el `except` lo tragaba y `atributos_dinamicos` quedaba `{}` **siempre**. El mismo patrón estaba en `app/biomedicos/routes.py:229` (`editar_mantenimiento` → el wizard de edición cargaba el reporte técnico vacío).
- **Fix aplicado (ambos archivos):** detección de tipo — si es `dict` se usa directo, si es `str` (datos legados) se parsea.

### ✅ FIX-10 🟠 — `editar_mantenimiento` biomédico crasheaba con `AttributeError`
- **Archivo:** `app/biomedicos/routes.py:240`
- `mantenimiento.tipo_mantenimiento_id` no existe; la FK del modelo `Mantenimiento` se llama `tipo_id` (`app/models.py:1526`). Error 500 al abrir el wizard de edición.
- **Fix aplicado:** `mantenimiento.tipo_id`.

### ✅ FIX-11 🟡 — Dashboard: "Últimos activos" filtraba casi todo
- **Archivo:** `app/main/routes.py:30`
- El widget de últimos 5 activos tenía `.filter(Activo.fecha_ingreso_ajeno.isnot(None))` — esa columna solo se llena para activos ajenos, así que el panel salía vacío teniendo cientos de activos propios. El comentario (*"filter out NULL values"*) delata que fue un parche mal orientado.
- **Fix aplicado:** filtro eliminado; muestra los últimos 5 activos reales.

### ✅ FIX-12 🟡 — Vista de movimiento sin detalles para Comodato
- **Archivo:** `app/movimientos/routes.py` (`ver_movimiento`, `DETALLE_ATTR_MAP`)
- El mapa no incluía `'Comodato': 'detalle_comodato'` → al ver un comodato, `detalles=None` y la plantilla no mostraba el contrato. **Fix aplicado.**

### ✅ FIX-13 🔵 — Estado inconsistente `'operativo'` vs `'Operativo'`
- **Archivo:** `app/activos/routes.py` (`importar_activos_ajenos`)
- La importación masiva de ajenos creaba activos con `estado='operativo'` (minúscula) mientras todo el sistema usa `'Operativo'`. Los filtros con `==` en Python y los conteos (`filter_by(estado='Operativo')`) los excluían. **Fix aplicado.** *(Nota: los registros ya insertados en minúscula requieren un `UPDATE activos SET estado='Operativo' WHERE estado='operativo';`).*

---

## 3. Bugs pendientes (hacer parte por parte)

### ✅ TASK-03 🔴 — `edit_activo` escribía en columnas inexistentes → pérdida silenciosa de datos *(resuelto)*
- **Archivos:** `app/models.py`, `app/activos/routes.py`, `app/main/routes.py`, migración `b58456050078`
- **El bug:** el formulario de contrato del activo ajeno hacía `setattr(activo, field, ...)` sobre 8 nombres que no eran columnas de `Activo`. `setattr` sobre un atributo no mapeado crea un atributo de instancia que SQLAlchemy ignora: el usuario llenaba NIT, teléfono, fechas y costo del contrato, veía *"Activo actualizado exitosamente"* y **los datos no llegaban nunca a la base de datos**.
- **Consecuencia en cadena:** el dashboard de activos ajenos leía esos campos con `hasattr(...)` envuelto en `except: pass`, así que las **alertas de vencimiento de contrato salían siempre vacías** y el KPI de costo mensual caía siempre al estimado del 10% del valor comercial. Los `except` mudos son la razón de que el bug llevara tanto tiempo sin detectarse.
- **Aplicado:**
  1. **8 columnas reales** en el modelo `Activo`: `nit_propietario`, `telefono_propietario`, `email_propietario`, `numero_contrato`, `fecha_inicio_contrato` (Date), `fecha_fin_contrato` (Date, indexada), `observaciones_contrato`, `costo_mensual`.
  2. **Migración `b58456050078`** escrita a mano (no autogenerada, ver TASK-02) y **aplicada**.
  3. **Parseo real en `edit_activo`:** las fechas se convierten con `strptime(...).date()` en vez de asignar el string crudo del formulario a una columna `Date`; se valida que `fecha_fin >= fecha_inicio` y que `costo_mensual` sea numérico, con mensaje de error al usuario en vez de fallo silencioso.
  4. **Dashboard reescrito** (`main/routes.py`): las alertas ahora se filtran **en SQL** sobre la columna `Date` indexada (`WHERE fecha_fin_contrato BETWEEN hoy AND hoy+30`) en lugar de traer todos los activos ajenos y parsear strings en Python con 3 formatos y `except: pass`. Se eliminaron 4 bare-except de paso.
  5. **Propiedades nuevas** en `Activo`: `dias_para_vencimiento_contrato`, `contrato_vencido`, `contrato_proximo_a_vencer(dias_alerta=30)`.
- **Verificado end-to-end:** escritura → `commit` → `expire_all` → relectura devuelve los valores correctos; `dias_para_vencimiento_contrato = 20` y `contrato_proximo_a_vencer(30) = True` sobre un contrato de prueba (datos de prueba revertidos después).

### TASK-04 🔴 — `activos_v2.editar` asigna `activo.proveedor_id` (columna inexistente)
- **Archivo:** `app/activos_v2/routes.py:259`
- `activo.proveedor_id = form.proveedor_id.data ...` — `Activo` no tiene `proveedor_id`; mismo patrón de pérdida silenciosa que TASK-03. El GET lo "lee" desde `DetalleEntrega` del primer movimiento de Entrega, pero el POST lo tira a la nada.
- **Acción:** o agregar la columna `proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))` a `Activo`, o eliminar el campo del formulario y persistirlo en `DetalleEntrega`.

### TASK-05 🔴 — Registro de auditoría de eliminación se autodestruye
- **Archivos:** `app/audit_helper.py` (`registrar_eliminacion_movimiento`) + `app/models.py` (`MovimientoHistorico`)
- El flujo es: crear `MovimientoHistorico(tipo_operacion='DELETE')` → `db.session.delete(movimiento)`. Pero `MovimientoHistorico.movimiento_id` tiene `ondelete='CASCADE'` y la relación `Movimiento.historial` tiene `cascade='all, delete-orphan'` → **al borrar el movimiento se borra también su registro de eliminación**. La auditoría legal (NIIF Sección 27) de borrados no queda en ninguna parte.
- **Acción:** guardar los eventos DELETE en una tabla sin FK-cascade (p. ej. `movimiento_id` como entero simple sin ForeignKey, más un snapshot JSON del movimiento), o cambiar a borrado lógico (`estado='Anulado'`).

### TASK-06 🟠 — Doble serialización JSON en columnas `db.JSON`
- **Archivos:** `app/movimientos/routes.py:527` y `:568`, `app/models.py:988` (`crear_desde_form`)
- `tipo_elementos=json.dumps(getlist(...))` y `tipo_traslado_json=json.dumps(...)` escriben un **string JSON dentro de una columna JSON** → MySQL guarda `"[\"a\",\"b\"]"` (string) en vez de `["a","b"]` (array). La lectura compensa con `json.loads(...)`, así que "funciona", pero:
  - imposibilita consultas JSON nativas de MySQL (`JSON_CONTAINS`, `->>`),
  - si algún día alguien escribe la lista directa (lo correcto), los `json.loads` de lectura (líneas ~1152, ~1202-1203 del PDF de traslado) lanzarán `TypeError` → error 500 en PDFs.
- **Acción:** quitar los `json.dumps(...)` al escribir (pasar la lista directa) y hacer la lectura tolerante (`if isinstance(x, str): json.loads(x)`); migrar datos existentes con un script (`UPDATE ... SET col = JSON_EXTRACT(col, '$')` cuando `JSON_TYPE(col)='STRING'`).

### TASK-07 🟠 — Triggers SQLAlchemy con commits anidados y sesiones mezcladas
- **Archivo:** `app/models.py` (TRIGGER 2, `actualizar_ultimo_mantenimiento_activo`)
- Dentro de un evento `after_insert/after_update` (que corre durante el flush de la sesión principal) se crea `Session(bind=connection)`, se carga el activo en **esa** sesión y luego se llama `activo.set_atributo_valor(...)`, que internamente hace `db.session.commit()` — commit de la sesión global **en medio del flush de otra transacción**. Esto produce errores intermitentes tipo *"Session is already flushing"* / *"This transaction is closed"* y puede confirmar datos a medias.
- **Acción:** dentro de los event listeners usar solo `connection.execute(update(...))` (SQL Core, sin commit), nunca `db.session`. Aplica también a TRIGGER 1 y TRIGGER 13/14 (usan `session.commit()` sobre el connection del flush; funciona de casualidad porque participa de la transacción externa, pero el patrón correcto es Core).

### TASK-08 🟠 — `Movimiento.crear_desde_form` está incompleto (solo maneja 'Entrega')
- **Archivo:** `app/models.py:888-1029`
- El método de clase duplica la lógica de `add_movimiento` de las rutas pero solo implementa el detalle de `Entrega` (el comentario `# Add other detail types here...` en la línea 1008 lo confirma). Nadie lo llama actualmente (la ruta usa su propia lógica), o sea es **código duplicado y divergente**.
- **Acción:** eliminar `crear_desde_form` por completo, o migrar la lógica de la ruta al modelo y dejar UNA sola implementación. Mantener dos copias garantiza que se desincronicen (ya pasó: la ruta valida Entrada/Salida y Comodato; el método no).

### TASK-09 🟠 — Rutas de archivos adjuntos guardadas como rutas ABSOLUTAS de Windows
- **Archivo:** `app/activos/routes.py` (`_save_file`, líneas 136-145)
- `subfolder_name = current_app.config[folder_key]` — pero `LOAN_CONTRACT_FOLDER`, `INVOICE_FOLDER`, etc. son rutas **absolutas** (`C:\...\uploads\loan_contracts`, ver `config.py:77-83`). `os.path.join(upload_base_dir, ruta_absoluta)` descarta el primer argumento, y en la BD se guarda la ruta absoluta completa (`C:\Users\david\...`). Consecuencias: si mueves el proyecto o despliegas en Linux, todos los enlaces a facturas/órdenes/contratos se rompen; además `os.path.join(UPLOAD_FOLDER, ruta_absoluta)` en `edit_activo`/`delete_activo` funciona solo por el mismo accidente.
- **Acción:** guardar en BD la ruta **relativa** (`loan_contracts/archivo.pdf`): en `_save_file`, derivar el nombre de subcarpeta con `os.path.basename(current_app.config[folder_key])` o definir constantes relativas separadas. Script de migración para normalizar las rutas ya guardadas (strip del prefijo `UPLOAD_FOLDER`).

### TASK-10 🟠 — Recuperación de contraseña no envía correo (feature incompleta)
- **Archivo:** `app/auth/routes.py:87-99`
- `forgot_password` genera el token y hace `print()` del enlace en consola ("SIMULACIÓN DE ENVÍO DE CORREO"). Existe `app/email_service.py` (SMTP completo con `MAIL_*` de config) pero no está conectado aquí.
- **Acción:** reutilizar `email_service` para enviar el `reset_url`; eliminar los `print` (en producción exponen el token de reseteo en logs de consola).

### TASK-11 🟠 — Logging de depuración sensible en login
- **Archivo:** `app/auth/routes.py:29-45`
- En cada POST se loggea el email, si el usuario existe y si la contraseña fue correcta (`[LOGIN DEBUG]`). Eso facilita enumeración de usuarios a quien lea logs y llena el log de ruido.
- **Acción:** eliminar los bloques `[LOGIN DEBUG]`; dejar solo el log de login exitoso/fallido sin distinguir "usuario no existe" de "contraseña mala".

### TASK-12 🟡 — `init-db` duplicado y destructivo
- **Archivos:** `app/__init__.py:170` + `:174-182`, y `app/db.py`
- El comando `init-db` (con `db.drop_all()`) está definido dos veces (`app/db.py` y al final de `app/__init__.py`) y registrado una; un `flask init-db` accidental **destruye toda la base de datos** sin confirmación.
- **Acción:** dejar una sola definición (la de `app/db.py`), añadir `click.confirm('Esto BORRA toda la BD. ¿Continuar?', abort=True)` y eliminar el duplicado del `__init__.py`. Igual con el doble `@login_manager.user_loader` (definido en `extensions.py` y re-definido en `auth/routes.py` — el segundo pisa al primero; dejar solo uno).

### TASK-13 🟡 — `activos_v2.eliminar_activo` borra sin validar relaciones
- **Archivo:** `app/activos_v2/routes.py:453-472`
- A diferencia de `activos.delete_activo` (que valida movimientos/mantenimientos/auditoría/hoja de vida antes de borrar), la versión v2 hace `db.session.delete(activo)` directo. La FK `movimiento_activos.activo_id` es `ondelete='RESTRICT'`, así que MySQL lo frena con un `IntegrityError` feo, pero: (a) el mensaje al usuario es críptico, (b) activos sin movimientos pero con historial se borran perdiendo trazabilidad, (c) además el evento `before_delete` (TRIGGER 14) ya insertó el registro de auditoría con commit propio aunque el DELETE falle.
- **Acción:** replicar las validaciones de `activos.delete_activo` o unificar ambas rutas en un solo servicio.

### TASK-14 🟡 — `ATRIBUTOS_POR_CLASE` definido 3 veces con contenidos distintos
- **Archivos:** `app/config.py:86-110`, `app/activos/routes.py:27-105`, `app/activos_v2/atributos_dinamicos.py`
- La versión de `config.py` es más pobre (p. ej. clase 1 sin `fabricante`, sin `frecuencia_mantenimiento`) y la de `activos/routes.py` marca campos como `required` que en config no lo son. Según qué módulo valide, un mismo activo pasa o no la validación.
- **Acción:** una sola fuente de verdad (idealmente la tabla `atributo_definicion` del sistema EAV FASE 2.1, que ya existe y está más completa) y eliminar los diccionarios estáticos. Como mínimo, dejar solo el de `activos_v2/atributos_dinamicos.py` e importarlo donde haga falta.

### TASK-15 🟡 — Sistema EAV (FASE 2.1) y JSON legado coexisten sin plan de corte
- **Archivos:** `app/models.py` (`CategoriaActivo`, `AtributoDefinicion`, `AtributoValor` + `Activo.atributos_dinamicos_json`)
- Hay dos sistemas de atributos dinámicos en paralelo: el EAV tipado (con validación, auditoría, índices) y el campo JSON (`atributos_dinamicos_json`) que es el que usan las rutas de `activos/` y `activos_v2/`. TRIGGER 2 escribe en ambos "transitoriamente". Ningún wizard escribe al EAV.
- **Acción:** decidir: o se completa la migración al EAV (script `migrar_json_a_eav.py` ya existe en la raíz — ejecutarlo/validarlo y cambiar los formularios), o se elimina el EAV. Documentar la decisión.

### TASK-16 🟡 — `esta_proximo_a_vencer` como property con parámetro
- **Archivo:** `app/models.py:1491-1497`
- `@property def esta_proximo_a_vencer(self, dias_alerta=30)` — una property no recibe argumentos; funciona solo porque el default cubre la llamada, pero `detalle.esta_proximo_a_vencer(60)` (uso natural) lanzaría `TypeError: 'bool' object is not callable`.
- **Acción:** convertirla en método normal `def esta_proximo_a_vencer(self, dias_alerta=30)` y ajustar las plantillas que la usen como atributo.

### TASK-17 🟡 — Cálculo de "% aprobación" del dashboard de movimientos es engañoso
- **Archivo:** `app/movimientos/routes.py:170-179`
- `porcentaje_aprobacion = ((aprobados_mes - aprobados_mes_anterior) / max(aprobados_mes_anterior,1)) * 100` — es una **variación intermensual**, no un porcentaje de aprobación; con mes anterior = 0 el `or 1` distorsiona el resultado (p. ej. 3 aprobados vs 0 → "200%"). Además la "TENDENCIA ÚLTIMOS 6 MESES" usa `timedelta(days=i*30)`, que se desalinea con meses reales (enero 31 días).
- **Acción:** renombrar la métrica o calcular `aprobados/total*100`; para la serie mensual usar `dateutil.relativedelta(months=i)`.

### TASK-18 🟡 — Excepciones silenciadas con `except: pass` (bare except)
- **Archivos:** `app/main/routes.py` (líneas 86, 98, 150, 163, 173), `app/models.py` (2073, 2234, 2246), `app/reportes/routes.py` (529, 971, 1264)
- Los bare `except:` capturan hasta `KeyboardInterrupt`/`SystemExit` y ocultan errores reales (por eso TASK-03 pasó desapercibido: los `hasattr`/`except` tragaban el problema).
- **Acción:** reemplazar por `except (ValueError, TypeError):` o el tipo concreto; loggear en vez de ignorar.

### TASK-19 🔵 — `role_required('Admin')` bloquea Reportes a Supervisor/Auditor
- **Archivo:** `app/reportes/routes.py:31,81` vs `app/permissions.py`
- El sistema RBAC (`PERMISOS_POR_ROL`) da `ver_reportes` a Supervisor, Auditor y User, pero `/reportes/` y `/reportes/depreciacion` usan el decorador viejo `role_required('Admin')` que exige igualdad exacta de rol. Inconsistencia entre los dos sistemas de permisos.
- **Acción:** migrar todas las rutas a `@require_permission('ver_reportes')` y deprecar `role_required` (o mantenerlo solo para acciones estrictamente de Admin).

### TASK-20 🔵 — Redundancias menores / limpieza
- `app/movimientos/routes.py` (`generar_acta_pdf`): `context = {}` en PASO 6 se sobrescribe con `context = {...}` en PASO 7 — la asignación previa de `context['accesorios']` para Traslado era código muerto (se recalcula después). Limpiar para evitar confusión.
- Dos listeners duplicados sobre `Activo.estado` con `'set'` (TRIGGER 3 imprime a consola, TRIGGER 10 audita). Eliminar TRIGGER 3 (solo hace `print`).
- `print()` usados como logging en modelos/triggers (`[TRIGGER ERROR]`, `[FIRMA]`, `[AUDIT]`) → cambiar a `current_app.logger` / logger de módulo.
- `app/utils.py` está vacío (0 líneas) → eliminar o usar.
- Raíz del proyecto llena de scripts one-off (`check_*.py`, `reset_password*.py`, `temp_migrate*.py`, `nul`, `query`, ~20 archivos .md de sesiones): mover a una carpeta `scripts/` y `docs/`, borrar los obsoletos.
- `app/__pycache__` y `venv/` aparecen en git status → verificar `.gitignore` (`__pycache__/`, `venv/`, `instance/`, `uploads/`).

### TASK-21 🔵 — Concurrencia: `flask run` de desarrollo con MySQL
- **Archivo:** `run.py`
- `app.run(debug=True, host='0.0.0.0')` expone el debugger de Werkzeug (ejecución remota de código con el PIN) a toda la red local. Para uso multiusuario real: `waitress-serve --port=5000 run:app` (Windows) y `debug=False`.

---

## 4. Resumen ejecutivo

| Categoría | Corregidos | Pendientes |
|---|---|---|
| 🔴 Críticos | 3 (FIX-03, 04, 05) | 4 (TASK-01, 03, 04, 05) |
| 🟠 Altos | 5 (FIX-06..10) | 6 (TASK-06..11) |
| 🟡/🔵 Medios y bajos | 5 (FIX-11..13 + config) | 11 (TASK-02, 12..21) |

**Migración a MySQL:** completada a nivel de código — se eliminó `app/database.py` (sqlite3) y la rama SQLite de `config.py`; no queda ninguna sintaxis SQLite en el proyecto. Falta lo operativo: TASK-01 (credenciales) y TASK-02 (migración Alembic de esquema).

**Orden sugerido de ataque:** TASK-01 → TASK-02 → TASK-03 → TASK-04 → TASK-05 → TASK-06 → resto.
