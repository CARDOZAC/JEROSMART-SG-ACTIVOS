# PLAN DE ACCIÓN DETALLADO - MÓDULO BIOMÉDICO
## Sistema de Gestión de Equipos Biomédicos JeroSmart

---

## 📋 ÍNDICE
1. [Análisis de Estado Actual](#análisis-de-estado-actual)
2. [Arquitectura del Módulo](#arquitectura-del-módulo)
3. [Plan de Desarrollo por Submódulos](#plan-de-desarrollo-por-submódulos)
4. [Cronograma de Tareas](#cronograma-de-tareas)
5. [Estructura de Base de Datos](#estructura-de-base-de-datos)
6. [Wireframes y Flujos de Usuario](#wireframes-y-flujos-de-usuario)

---

## 1. ANÁLISIS DE ESTADO ACTUAL

### 1.1 Componentes Existentes ✅

**Backend (Python/Flask):**
- ✅ `app/biomedicos/routes.py` - Rutas API implementadas
- ✅ `app/models.py` - Modelos de BD completos:
  - `HojaVidaBiomedico`
  - `Mantenimiento`
  - `MantenimientoTipo`
  - `MantenimientoFoto`
  - `DocumentoAdjunto`
  - `Firma`
- ✅ `app/biomedicos/formatos.json` - Tipos de reportes de mantenimiento definidos

**Frontend (Templates/JavaScript):**
- ✅ Templates base para gestión de mantenimientos
- ✅ Sistema de firmas digitales implementado
- ✅ Generación de PDFs con WeasyPrint

### 1.2 Componentes Faltantes ❌

**1. Submódulo HOJAS DE VIDA:**
   - ❌ Wizard completo para crear hojas de vida
   - ❌ Vista de tabla con filtros y búsqueda
   - ❌ Vista de detalle/resumen de hoja de vida
   - ❌ Sistema de carga de archivos adjuntos (4 categorías)
   - ❌ Enlace directo con activos biomédicos

**2. Submódulo MANTENIMIENTOS:**
   - ❌ Sistema de preguardado/borradores
   - ❌ Wizard con selección dinámica de formatos
   - ❌ Tabla de accesorios con cálculo de totales
   - ❌ Canvas de firmas duales (ingeniero + receptor)
   - ❌ Generación de PDF personalizado por tipo de reporte

**3. Submódulo REPORTES:**
   - ❌ Reporte individual (Hoja de vida + mantenimientos + documentación)
   - ❌ Reporte grupal de mantenimientos realizados
   - ❌ Reporte grupal de hojas de vida registradas
   - ❌ Reporte de mantenimientos pendientes
   - ❌ Filtros por fecha, activo, ubicación, estado

---

## 2. ARQUITECTURA DEL MÓDULO

### 2.1 Estructura de Directorios

```
app/
├── biomedicos/
│   ├── __init__.py
│   ├── routes.py                          # ✅ Existente - Ampliar
│   ├── context_builders.py                # ✅ Existente
│   ├── formatos.json                      # ✅ Existente
│   │
│   ├── forms.py                           # 🆕 CREAR - Validación de formularios
│   ├── pdf_generators.py                  # 🆕 CREAR - Generación de PDFs
│   ├── file_handlers.py                   # 🆕 CREAR - Gestión de archivos
│   │
│   ├── templates/
│   │   ├── biomedicos/
│   │   │   ├── hojas_vida/
│   │   │   │   ├── ver_hojas_vida.html           # 🆕 CREAR
│   │   │   │   ├── wizard_crear_hoja_vida.html   # 🆕 CREAR
│   │   │   │   ├── detalle_hoja_vida.html        # 🆕 CREAR
│   │   │   │   └── componentes/
│   │   │   │       ├── paso1_datos_generales.html
│   │   │   │       ├── paso2_datos_tecnicos.html
│   │   │   │       ├── paso3_documentos.html
│   │   │   │       └── paso4_resumen.html
│   │   │   │
│   │   │   ├── mantenimientos/
│   │   │   │   ├── ver_mantenimientos.html       # ✅ Existente - Mejorar
│   │   │   │   ├── wizard_mantenimiento.html     # 🆕 CREAR
│   │   │   │   └── componentes/
│   │   │   │       ├── paso1_seleccionar_activo.html
│   │   │   │       ├── paso2_tipo_reporte.html
│   │   │   │       ├── paso3_datos_tecnico.html
│   │   │   │       ├── paso4_accesorios.html
│   │   │   │       ├── paso5_reporte_tecnico.html
│   │   │   │       └── paso6_firmas.html
│   │   │   │
│   │   │   └── reportes/
│   │   │       ├── reportes_dashboard.html        # 🆕 CREAR
│   │   │       └── componentes/
│   │   │           ├── filtros_reportes.html
│   │   │           └── preview_reporte.html
│   │   │
│   │   └── pdf_templates/
│   │       ├── hoja_vida_consolidada.html         # ✅ Existente
│   │       ├── mantenimiento_preventivo.html      # 🆕 CREAR
│   │       ├── mantenimiento_correctivo.html      # 🆕 CREAR
│   │       ├── reporte_grupal_mantenimientos.html # 🆕 CREAR
│   │       └── reporte_hojas_vida.html            # 🆕 CREAR
│   │
│   └── static/
│       ├── js/
│       │   ├── hojas_vida/
│       │   │   ├── wizard_hoja_vida.js            # 🆕 CREAR
│       │   │   ├── tabla_hojas_vida.js            # 🆕 CREAR
│       │   │   └── upload_documentos.js           # 🆕 CREAR
│       │   │
│       │   ├── mantenimientos/
│       │   │   ├── wizard_mantenimiento.js        # 🆕 CREAR
│       │   │   ├── tabla_mantenimientos.js        # ✅ Mejorar existente
│       │   │   ├── canvas_firmas.js               # 🆕 CREAR
│       │   │   └── tabla_accesorios.js            # 🆕 CREAR
│       │   │
│       │   └── reportes/
│       │       ├── generador_reportes.js          # 🆕 CREAR
│       │       └── filtros_dinamicos.js           # 🆕 CREAR
│       │
│       └── css/
│           └── biomedicos_styles.css              # 🆕 CREAR
│
└── migrations/
    └── biomedicos/
        └── 01_estructura_hojas_vida_mantenimientos.sql  # ✅ Ya existe en models.py
```

### 2.2 Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                    MÓDULO BIOMÉDICO                             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │ HOJAS VIDA  │  │MANTENIMIENTOS│  │  REPORTES    │
    └─────────────┘  └──────────────┘  └──────────────┘
          │                 │                  │
          │                 │                  │
          ▼                 ▼                  ▼
    ┌─────────────────────────────────────────────────┐
    │          Base de Datos (SQLAlchemy)             │
    ├─────────────────────────────────────────────────┤
    │ • hojas_vida_biomedicos                         │
    │ • mantenimientos                                │
    │ • mantenimiento_tipos                           │
    │ • documentos_adjuntos_biomedicos                │
    │ • firmas                                        │
    │ • activos (FK)                                  │
    └─────────────────────────────────────────────────┘
```

---

## 3. PLAN DE DESARROLLO POR SUBMÓDULOS

---

## 📘 SUBMÓDULO 1: HOJAS DE VIDA

### 3.1.1 Funcionalidades Principales

#### A. Vista de Tabla de Hojas de Vida

**Características:**
- Tabla paginada con todas las hojas de vida registradas
- Columnas:
  - Placa del activo
  - Nombre del equipo
  - Marca/Modelo
  - Serie
  - Ubicación
  - Fecha de creación
  - Estado (Completo/Incompleto)
  - Acciones (Ver, Editar, PDF, Eliminar)

**Filtros dinámicos:**
- Por placa/código interno
- Por nombre del activo
- Por ubicación
- Por estado de hoja de vida
- Por rango de fechas de creación

**Botón Principal:**
- "➕ Agregar Nueva Hoja de Vida" → Abre wizard

#### B. Wizard de Creación de Hoja de Vida (4 Pasos)

**PASO 1: Selección y Datos Generales**
- Buscador de activos biomédicos (autocompletado)
- Validación: El activo NO debe tener hoja de vida existente
- Campos:
  - Permiso de comercialización INVIMA
  - N° Factura
  - N° Orden de compra
  - Fecha de fabricación
  - Fecha de instalación
  - Distribuidor
  - Forma de adquisición (Compra, Donación, Comodato)
  - Teléfono contacto
  - Correo electrónico
  - Fecha de ingreso a la institución
  - Vencimiento de garantía
  - Costo de adquisición
  - Vida útil (años)

**PASO 2: Datos Técnicos**
- Especificaciones eléctricas:
  - Voltaje (V)
  - Frecuencia (Hz)
  - Corriente (A)
  - Potencia (W)
- Características físicas:
  - Dimensiones (Alto x Ancho x Largo)
  - Peso (kg)
  - Tipo: Fijo / Móvil
- Condiciones de operación:
  - Humedad relativa (%)
  - Temperatura de trabajo (°C)
- Documentación técnica:
  - ☑ Manual de usuario disponible
  - ☑ Manual de servicio disponible
- Clasificación:
  - Clasificación de riesgo (I, IIA, IIB, III)
  - Clasificación biomédica (Diagnóstico, Terapéutico, Apoyo, etc.)
- Mantenimiento:
  - Periodicidad de mantenimiento (Mensual, Trimestral, Semestral, Anual)
  - ☑ Requiere calibración
  - Periodicidad de metrología

**PASO 3: Documentos Adjuntos**

4 categorías de archivos (PDF principalmente):

1. **📋 Calibraciones**
   - Área de carga de archivos (drag & drop)
   - Lista de archivos cargados con opción de eliminar
   - Todos los PDFs se fusionan en un solo documento al guardar

2. **🔧 Mantenimientos Preventivos Anteriores**
   - Misma funcionalidad que calibraciones
   - Reportes históricos de mantenimientos antes del registro

3. **⚠️ Mantenimientos Correctivos Anteriores**
   - Misma funcionalidad
   - Historial de reparaciones realizadas

4. **📄 Documentación Legal y Auditable**
   - Registro INVIMA
   - Carta de importación
   - Manual de desinfección
   - Cronograma de mantenimiento
   - Certificados
   - Todo se unifica en un solo PDF

**Adicionalmente:**
- **📷 Foto del Equipo** (opcional)
  - Formato: JPG, PNG
  - Tamaño máximo: 5 MB
  - Se guarda en `ruta_foto_activo` del modelo `Activo`

**Funcionalidad Técnica:**
- Los archivos se suben al servidor temporalmente
- Al guardar, se procesan con PyPDF2 o similar para unificar PDFs
- Se guardan en `app/biomedicos/static/hojas_vida/{activo_id}/`
- Se registran en `documentos_adjuntos_biomedicos` con:
  - `tipo_documento` (calibracion, mantenimiento_preventivo, etc.)
  - `ruta_archivo`
  - `checksum_sha256` (integridad)

**PASO 4: Resumen y Confirmación**
- Vista previa de todos los datos ingresados
- Resumen organizado por secciones:
  - 📋 Información General
  - 🔧 Datos Técnicos
  - 📄 Documentos Adjuntos (con iconos y nombres)
- Botones:
  - "◀ Regresar" (volver a paso anterior)
  - "💾 Guardar Hoja de Vida"
  - "❌ Cancelar"

#### C. Vista de Detalle de Hoja de Vida

**Características:**
- Se accede al hacer clic en una fila de la tabla
- Misma estructura visual que el Paso 4 del wizard
- Pestañas organizadas:
  - 📋 Datos Generales
  - 🔧 Especificaciones Técnicas
  - 📄 Documentos (con visor de PDF embebido)
  - 📊 Historial de Mantenimientos (tabla resumida)
- Botones de acción:
  - "✏️ Editar" (abre wizard en modo edición)
  - "📄 Generar PDF Consolidado"
  - "🗑️ Eliminar Hoja de Vida"

### 3.1.2 Endpoints API Necesarios

```python
# HOJAS DE VIDA - API Endpoints

# ✅ YA EXISTE
GET  /biomedicos/api/hojas-vida
     - Lista todas las hojas de vida con filtros
     - Query params: ?q=placa&ubicacion=x&estado=completo

# ✅ YA EXISTE
POST /biomedicos/api/hojas-vida
     - Crea nueva hoja de vida
     - Body: FormData con todos los campos + archivos

# ✅ YA EXISTE
GET  /biomedicos/api/hojas-vida/<activo_id>
     - Obtiene detalle completo de hoja de vida

# ✅ YA EXISTE
PUT  /biomedicos/api/hojas-vida/<activo_id>
     - Actualiza hoja de vida existente

# ✅ YA EXISTE
DELETE /biomedicos/api/hojas-vida/<activo_id>
       - Elimina hoja de vida

# ✅ YA EXISTE
GET  /biomedicos/api/hojas-vida/pdf/<activo_id>
     - Genera PDF consolidado

# 🆕 CREAR
POST /biomedicos/api/hojas-vida/upload-temp
     - Sube archivo temporal durante wizard
     - Retorna: {file_id, file_name, file_url}

# 🆕 CREAR
GET  /biomedicos/api/activos-sin-hoja-vida
     - Lista activos biomédicos sin hoja de vida
     - Para el buscador del wizard paso 1
```

### 3.1.3 Tareas de Desarrollo - Hojas de Vida

#### FASE 1: Backend (Python/Flask)

**Tarea 1.1: Actualizar routes.py para Hojas de Vida**
- [ ] Crear endpoint `POST /api/hojas-vida/upload-temp` para archivos temporales
- [ ] Implementar función `merge_pdfs()` para unificar documentos
- [ ] Crear endpoint `GET /api/activos-sin-hoja-vida` con filtro de clase biomédica
- [ ] Agregar validación de que activo no tenga hoja de vida existente
- [ ] Implementar cálculo de checksum SHA256 para archivos

**Tarea 1.2: Crear file_handlers.py**
```python
# Funciones a implementar:
- save_temp_file(file, user_session_id)
- merge_pdf_documents(file_list, output_name)
- calculate_sha256(file_path)
- cleanup_temp_files(session_id)
- compress_image(image_path, max_size_mb=5)
```

**Tarea 1.3: Crear forms.py para Validación**
```python
from wtforms import Form, StringField, DateField, FloatField, BooleanField
from wtforms.validators import DataRequired, Optional, Email

class HojaVidaForm(Form):
    # Definir validadores para todos los campos
    permiso_comercializacion = StringField('Permiso INVIMA', [Optional()])
    n_factura = StringField('N° Factura', [Optional()])
    # ... etc
```

#### FASE 2: Frontend (Templates HTML)

**Tarea 2.1: Crear ver_hojas_vida.html**
- [ ] Estructura base con Jinja2 extends de `base.html`
- [ ] Tabla responsive con DataTables
- [ ] Formulario de filtros avanzados
- [ ] Botón "Agregar Hoja de Vida" destacado
- [ ] Modales para confirmación de eliminación
- [ ] Integración con sistema de notificaciones

**Tarea 2.2: Crear wizard_crear_hoja_vida.html**
- [ ] Estructura de wizard con 4 pasos
- [ ] Barra de progreso visual
- [ ] Navegación entre pasos (Siguiente/Anterior)
- [ ] Validación por paso antes de avanzar
- [ ] Almacenamiento temporal en `sessionStorage`

**Tarea 2.3: Crear componentes de cada paso**
- [ ] `paso1_datos_generales.html`
  - Autocompletado de activos
  - Campos de fecha con datepicker
  - Selectores personalizados
- [ ] `paso2_datos_tecnicos.html`
  - Campos numéricos con unidades
  - Checkboxes para manuales
  - Selectores de clasificación
- [ ] `paso3_documentos.html`
  - Drag & drop para archivos
  - Preview de archivos cargados
  - Progreso de carga
  - Botones de eliminar archivo
- [ ] `paso4_resumen.html`
  - Vista organizada por secciones
  - Iconos para tipos de documentos
  - Botón de confirmación

**Tarea 2.4: Crear detalle_hoja_vida.html**
- [ ] Layout con pestañas (tabs)
- [ ] Visor de PDF embebido
- [ ] Tabla de historial de mantenimientos
- [ ] Botones de acción (Editar, PDF, Eliminar)

#### FASE 3: JavaScript

**Tarea 3.1: wizard_hoja_vida.js**
```javascript
// Funcionalidades principales:
class WizardHojaVida {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = {};
        this.tempFiles = [];
    }

    nextStep()
    previousStep()
    goToStep(stepNumber)
    validateStep(stepNumber)
    saveToSession()
    loadFromSession()
    submitForm()
}
```

**Tarea 3.2: upload_documentos.js**
```javascript
// Gestión de carga de archivos
class DocumentUploader {
    constructor(categoryName, maxFiles) {
        this.category = categoryName;
        this.files = [];
        this.maxFiles = maxFiles;
    }

    handleDragOver(e)
    handleDrop(e)
    uploadFile(file)
    removeFile(fileId)
    mergePDFs()
}
```

**Tarea 3.3: tabla_hojas_vida.js**
```javascript
// Tabla interactiva
$(document).ready(function() {
    $('#tablaHojasVida').DataTable({
        ajax: '/biomedicos/api/hojas-vida',
        columns: [
            { data: 'placa_codigo_interno' },
            { data: 'nombre_activo' },
            { data: 'marca' },
            { data: 'modelo' },
            { data: 'ubicacion' },
            { data: 'fecha_creacion' },
            { data: 'estado' },
            {
                data: null,
                render: function(data, type, row) {
                    return `
                        <button onclick="verDetalle(${row.activo_id})">Ver</button>
                        <button onclick="editarHoja(${row.activo_id})">Editar</button>
                        <button onclick="generarPDF(${row.activo_id})">PDF</button>
                    `;
                }
            }
        ],
        language: { url: '/static/js/dataTables.spanish.json' }
    });
});
```

#### FASE 4: CSS y Estilos

**Tarea 4.1: biomedicos_styles.css**
- [ ] Estilos para wizard (progreso, pasos)
- [ ] Estilos para drag & drop
- [ ] Animaciones de transición entre pasos
- [ ] Responsive design para móviles
- [ ] Iconografía personalizada

---

## 📗 SUBMÓDULO 2: MANTENIMIENTOS

### 3.2.1 Funcionalidades Principales

#### A. Vista de Tabla de Mantenimientos

**Características:**
- Tabla con todos los mantenimientos (completos y borradores)
- Columnas:
  - ID Mantenimiento
  - Placa del activo
  - Nombre del equipo
  - Tipo de reporte
  - Fecha programada
  - Estado (Pendiente, En Proceso, Completado, Borrador)
  - Ingeniero responsable
  - Acciones

**Filtros:**
- Por estado (incluir "Borradores")
- Por tipo de mantenimiento
- Por activo
- Por rango de fechas
- Por ingeniero responsable

**Estados de Mantenimiento:**
- 🟡 **Borrador**: Guardado incompleto, se puede continuar
- 🔵 **Pendiente**: Programado pero no iniciado
- 🟠 **En Proceso**: Mantenimiento en ejecución
- 🟢 **Completado**: Finalizado con firmas
- 🔴 **Cancelado**: No se realizó

**Funcionalidad Especial: Preguardado**
- Botón "💾 Guardar Borrador" en cada paso del wizard
- Se guarda en BD con `estado='Borrador'`
- Desde la tabla, botón "▶️ Continuar" para retomar
- Campos guardados se cargan automáticamente

#### B. Wizard de Creación de Mantenimiento (6 Pasos)

**PASO 1: Seleccionar Activo**
- Buscador de activos biomédicos
- Muestra información del activo seleccionado:
  - Placa
  - Nombre
  - Ubicación actual
  - Último mantenimiento
  - Hoja de vida (link si existe)
- Botón: "Siguiente ➡️"

**PASO 2: Tipo de Reporte**
- Lista desplegable con tipos desde `formatos.json`:
  - Mantenimiento Preventivo Calentador de Paciente
  - Mantenimiento Preventivo Cama Hospitalaria
  - Mantenimiento Correctivo
  - Calibración
  - ... (todos los definidos en formatos.json)
- Muestra descripción del tipo seleccionado
- Carga dinámica de campos según el formato
- Botón: "Siguiente ➡️" o "💾 Guardar Borrador"

**PASO 3: Datos del Técnico**
- Formulario:
  - Nombre completo del técnico
  - Cédula
  - Cargo (ej: Ingeniero Biomédico)
  - Empresa (si es externo)
  - Fecha del mantenimiento
  - Hora de inicio
  - Hora de finalización
- Botón: "Siguiente ➡️" o "💾 Guardar Borrador"

**PASO 4: Tabla de Accesorios Utilizados**
- Tabla dinámica con columnas:
  - Descripción del accesorio
  - Cantidad
  - Botones: "➕ Agregar fila" / "🗑️ Eliminar fila"
- **Footer con total:** TOTAL: [suma de cantidades]
- Los accesorios se guardan como JSON en `atributos_reporte_json`
- Botón: "Siguiente ➡️" o "💾 Guardar Borrador"

**PASO 5: Reporte Técnico**
- Área de texto grande para:
  - Descripción de actividades realizadas
  - Hallazgos
  - Pruebas realizadas
  - Recomendaciones
- Campos dinámicos según tipo de reporte (cargados desde formatos.json)
- Editor de texto enriquecido (opcional)
- Botón: "Siguiente ➡️" o "💾 Guardar Borrador"

**PASO 6: Firmas Digitales**

Dos bloques de firma:

**Bloque 1: Ingeniero que realiza el mantenimiento**
- Canvas para firma digital
- Campo: Nombre completo (precargado del Paso 3)
- Campo: Cargo (precargado del Paso 3)
- Botón: "🔄 Limpiar firma"

**Bloque 2: Persona que recibe a conformidad**
- Canvas para firma digital
- Campo: Nombre completo
- Campo: Cargo
- Botón: "🔄 Limpiar firma"

**Validación:**
- Ambas firmas son obligatorias para completar
- Si falta alguna, mostrar error
- Firmas se guardan en tabla `firmas` con:
  - `tipo_documento='mantenimiento'`
  - `documento_id=mantenimiento.id`
  - `rol_firma='ingeniero'` o `'receptor'`
  - `firma_base64` (imagen PNG en base64)

**Botones finales:**
- "💾 Guardar como Borrador" (sin validar firmas)
- "✅ Completar Mantenimiento" (valida todo y guarda con estado='Completado')

#### C. Vista de Detalle de Mantenimiento

- Vista similar al último paso del wizard
- Muestra todos los datos ingresados
- Muestra las firmas guardadas
- Botones:
  - "✏️ Editar" (solo si estado != 'Completado')
  - "📄 Generar PDF"
  - "🗑️ Eliminar"

#### D. Generación de PDF de Mantenimiento

**Estructura del PDF:**
- **Encabezado:**
  - Logo de la institución
  - Título: "REPORTE DE MANTENIMIENTO - [Tipo]"
  - Código de mantenimiento: MTT-YYYY-NNNN
  - Fecha: DD/MM/YYYY

- **Sección 1: Datos del Equipo**
  - Placa
  - Nombre del activo
  - Marca/Modelo/Serie
  - Ubicación
  - Responsable actual

- **Sección 2: Datos del Mantenimiento**
  - Tipo de reporte
  - Fecha y hora
  - Ingeniero responsable
  - Empresa (si aplica)

- **Sección 3: Accesorios Utilizados**
  - Tabla con descripción y cantidad
  - Total de accesorios

- **Sección 4: Reporte Técnico**
  - Actividades realizadas
  - Observaciones
  - Campos dinámicos según formato

- **Sección 5: Firmas**
  - Firma del ingeniero (con nombre y cargo)
  - Firma del receptor (con nombre y cargo)

- **Pie de página:**
  - Generado por: [Usuario actual]
  - Fecha de generación: [Ahora]
  - Sistema JeroSmart Activos Fijos

### 3.2.2 Endpoints API Necesarios

```python
# MANTENIMIENTOS - API Endpoints

# ✅ YA EXISTE
GET  /biomedicos/api/mantenimientos
     - Lista mantenimientos con filtros
     - Query: ?estado=Borrador&activo_id=5&fecha_inicio=2024-01-01

# ✅ YA EXISTE
POST /biomedicos/api/mantenimientos
     - Crea nuevo mantenimiento

# ✅ YA EXISTE
GET  /biomedicos/api/mantenimientos/<id>
     - Obtiene detalle completo

# ✅ YA EXISTE
PUT  /biomedicos/api/mantenimientos/<id>
     - Actualiza mantenimiento existente

# ✅ YA EXISTE
DELETE /biomedicos/api/mantenimientos/<id>
       - Elimina mantenimiento

# ✅ YA EXISTE
GET  /biomedicos/api/mantenimiento-tipos
     - Lista tipos de mantenimiento

# ✅ YA EXISTE
GET  /biomedicos/api/reporte-formatos
     - Retorna formatos.json

# 🆕 CREAR
GET  /biomedicos/api/mantenimientos/pdf/<id>
     - Genera PDF del mantenimiento

# 🆕 CREAR
POST /biomedicos/api/mantenimientos/<id>/guardar-borrador
     - Guarda estado actual sin validar

# 🆕 CREAR
POST /biomedicos/api/mantenimientos/<id>/firmas
     - Guarda firmas digitales
     - Body: {firma_ingeniero: base64, firma_receptor: base64, ...}
```

### 3.2.3 Tareas de Desarrollo - Mantenimientos

#### FASE 1: Backend (Python/Flask)

**Tarea 1.1: Actualizar routes.py para Mantenimientos**
- [ ] Crear endpoint `POST /api/mantenimientos/<id>/guardar-borrador`
- [ ] Crear endpoint `POST /api/mantenimientos/<id>/firmas`
- [ ] Crear endpoint `GET /api/mantenimientos/pdf/<id>`
- [ ] Modificar validación para permitir guardar con campos incompletos
- [ ] Implementar lógica de estados (Borrador → En Proceso → Completado)

**Tarea 1.2: Crear pdf_generators.py**
```python
from weasyprint import HTML
from flask import render_template
from app.models import Mantenimiento

def generar_pdf_mantenimiento(mantenimiento_id):
    """
    Genera PDF personalizado según tipo de mantenimiento.
    """
    mantenimiento = Mantenimiento.query.get(mantenimiento_id)

    # Seleccionar template según tipo
    template = f'pdf_templates/mantenimiento_{mantenimiento.tipo.nombre.lower()}.html'

    # Construir contexto
    context = {
        'mantenimiento': mantenimiento,
        'activo': mantenimiento.activo,
        'ingeniero': mantenimiento.usuario,
        'firmas': mantenimiento.firmas,
        'accesorios': json.loads(mantenimiento.atributos_reporte_json).get('accesorios', []),
        # ... más datos
    }

    html = render_template(template, **context)
    pdf = HTML(string=html).write_pdf()

    return pdf
```

**Tarea 1.3: Mejorar Modelo Mantenimiento**
- [ ] Validar que `atributos_reporte_json` tenga estructura correcta
- [ ] Agregar método `puede_editarse()` según estado
- [ ] Agregar método `calcular_total_accesorios()`
- [ ] Agregar método `esta_completo()` para validación

#### FASE 2: Frontend (Templates HTML)

**Tarea 2.1: Mejorar ver_mantenimientos.html**
- [ ] Agregar filtro por estado "Borrador"
- [ ] Agregar columna "Progreso" (% de completitud)
- [ ] Botón "▶️ Continuar" para borradores
- [ ] Badge visual para cada estado
- [ ] Modales de confirmación

**Tarea 2.2: Crear wizard_mantenimiento.html**
- [ ] Estructura de 6 pasos
- [ ] Barra de progreso con iconos
- [ ] Botón flotante "💾 Guardar Borrador" en todos los pasos
- [ ] Validación condicional según estado

**Tarea 2.3: Crear componentes de pasos**
- [ ] `paso1_seleccionar_activo.html`
- [ ] `paso2_tipo_reporte.html` (carga dinámica desde formatos.json)
- [ ] `paso3_datos_tecnico.html`
- [ ] `paso4_accesorios.html` (tabla dinámica con totales)
- [ ] `paso5_reporte_tecnico.html` (campos dinámicos)
- [ ] `paso6_firmas.html` (2 canvas)

**Tarea 2.4: Crear templates PDF**
- [ ] `pdf_templates/mantenimiento_base.html` (layout común)
- [ ] `pdf_templates/mantenimiento_preventivo.html`
- [ ] `pdf_templates/mantenimiento_correctivo.html`
- [ ] `pdf_templates/mantenimiento_calibracion.html`

#### FASE 3: JavaScript

**Tarea 3.1: wizard_mantenimiento.js**
```javascript
class WizardMantenimiento {
    constructor(mantenimientoId = null) {
        this.id = mantenimientoId;
        this.currentStep = 1;
        this.totalSteps = 6;
        this.data = {};
        this.isBorrador = false;
    }

    loadBorrador(id)        // Cargar borrador existente
    guardarBorrador()       // Guardar estado actual
    nextStep()
    previousStep()
    validateStep(step)
    submitFinal()           // Solo si todas las firmas están
}
```

**Tarea 3.2: canvas_firmas.js**
```javascript
class CanvasFirma {
    constructor(canvasId, rolFirma) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.rol = rolFirma;
        this.isDrawing = false;
        this.initEvents();
    }

    initEvents() {
        // Mouse events
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', () => this.stopDrawing());

        // Touch events para móviles
        this.canvas.addEventListener('touchstart', (e) => this.startDrawing(e));
        this.canvas.addEventListener('touchmove', (e) => this.draw(e));
        this.canvas.addEventListener('touchend', () => this.stopDrawing());
    }

    startDrawing(e)
    draw(e)
    stopDrawing()
    clear()
    getDataURL()            // Retorna base64 PNG
    isEmpty()
}
```

**Tarea 3.3: tabla_accesorios.js**
```javascript
class TablaAccesorios {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.accesorios = [];
        this.render();
    }

    agregarFila() {
        this.accesorios.push({ descripcion: '', cantidad: 0 });
        this.render();
    }

    eliminarFila(index) {
        this.accesorios.splice(index, 1);
        this.render();
    }

    calcularTotal() {
        return this.accesorios.reduce((sum, acc) => sum + acc.cantidad, 0);
    }

    render() {
        // Renderiza tabla HTML con inputs editables
        let html = '<table class="tabla-accesorios">';
        html += '<thead><tr><th>Descripción</th><th>Cantidad</th><th>Acciones</th></tr></thead>';
        html += '<tbody>';

        this.accesorios.forEach((acc, i) => {
            html += `<tr>
                <td><input type="text" value="${acc.descripcion}" onchange="tablaAccesorios.update(${i}, 'descripcion', this.value)"></td>
                <td><input type="number" value="${acc.cantidad}" onchange="tablaAccesorios.update(${i}, 'cantidad', this.value)"></td>
                <td><button onclick="tablaAccesorios.eliminarFila(${i})">🗑️</button></td>
            </tr>`;
        });

        html += '</tbody>';
        html += `<tfoot><tr><td>TOTAL</td><td colspan="2">${this.calcularTotal()}</td></tr></tfoot>`;
        html += '</table>';
        html += '<button onclick="tablaAccesorios.agregarFila()">➕ Agregar accesorio</button>';

        this.container.innerHTML = html;
    }

    update(index, field, value) {
        this.accesorios[index][field] = value;
        this.render();
    }

    getData() {
        return this.accesorios;
    }
}

// Instancia global
let tablaAccesorios = null;

document.addEventListener('DOMContentLoaded', () => {
    tablaAccesorios = new TablaAccesorios('container-tabla-accesorios');
});
```

#### FASE 4: CSS y Estilos

**Tarea 4.1: Estilos específicos de mantenimientos**
- [ ] Canvas de firmas con borde y fondo
- [ ] Tabla de accesorios responsive
- [ ] Badges de estado con colores
- [ ] Botón flotante "Guardar Borrador"
- [ ] Animaciones de carga

---

## 📙 SUBMÓDULO 3: REPORTES

### 3.3.1 Tipos de Reportes

#### REPORTE 1: Individual Consolidado
**Nombre:** Reporte Completo de Equipo Biomédico

**Contenido:**
1. Hoja de Vida completa del activo
2. Todos los mantenimientos realizados (cronológicamente)
3. Toda la documentación adjunta
4. Gráfico de historial de mantenimientos

**Filtros:**
- Seleccionar activo específico
- Rango de fechas de mantenimientos

**Formato de salida:** PDF de múltiples páginas

#### REPORTE 2: Grupal de Mantenimientos Realizados
**Nombre:** Reporte de Mantenimientos por Período

**Contenido:**
Tabla con columnas:
- Fecha de mantenimiento
- Placa del activo
- Nombre del equipo
- Ubicación
- Tipo de mantenimiento
- Estado
- Ingeniero responsable
- Observaciones

**Filtros:**
- Rango de fechas
- Tipo de mantenimiento
- Estado
- Ubicación
- Ingeniero

**Formato de salida:** PDF o Excel

#### REPORTE 3: Grupal de Hojas de Vida Registradas
**Nombre:** Inventario de Hojas de Vida

**Contenido:**
Tabla con columnas:
- Placa
- Nombre del equipo
- Marca/Modelo
- Serie
- Ubicación
- Fecha de creación HdV
- Estado de documentación (% completo)
- Último mantenimiento

**Filtros:**
- Ubicación
- Estado de documentación
- Fecha de creación

**Formato de salida:** PDF o Excel

#### REPORTE 4: Mantenimientos Pendientes
**Nombre:** Reporte de Mantenimientos Pendientes

**Contenido:**
Tabla con columnas:
- Placa
- Nombre del equipo
- Ubicación
- Tipo de mantenimiento
- Fecha programada
- Días de atraso (si aplica)
- Estado (Pendiente / Borrador)
- Observaciones

**Filtros:**
- Solo atrasados
- Por ubicación
- Por tipo de mantenimiento

**Formato de salida:** PDF

#### REPORTE 5: Estadísticas de Gestión (ADICIONAL SUGERIDO)
**Nombre:** Dashboard de Métricas Biomédicas

**Contenido:**
- Total de equipos con hoja de vida vs sin hoja de vida (gráfico)
- Mantenimientos realizados por mes (gráfico de líneas)
- Distribución de mantenimientos por tipo (gráfico de torta)
- Top 10 equipos con más mantenimientos
- Equipos con mantenimiento vencido
- Cumplimiento de cronograma (% de mantenimientos a tiempo)

**Filtros:**
- Año
- Trimestre
- Ubicación

**Formato de salida:** Dashboard interactivo (HTML) + PDF estático

### 3.3.2 Endpoints API Necesarios

```python
# REPORTES - API Endpoints

# 🆕 CREAR
GET  /biomedicos/api/reportes/individual/<activo_id>
     - Genera reporte consolidado de un activo
     - Query params: ?formato=pdf&fecha_inicio=...&fecha_fin=...

# 🆕 CREAR
GET  /biomedicos/api/reportes/mantenimientos-realizados
     - Reporte grupal de mantenimientos
     - Query: ?formato=pdf&fecha_inicio=...&ubicacion=...&tipo=...

# 🆕 CREAR
GET  /biomedicos/api/reportes/hojas-vida-registradas
     - Inventario de hojas de vida
     - Query: ?formato=excel&ubicacion=...

# 🆕 CREAR
GET  /biomedicos/api/reportes/mantenimientos-pendientes
     - Reporte de mantenimientos pendientes
     - Query: ?solo_atrasados=true&ubicacion=...

# 🆕 CREAR
GET  /biomedicos/api/reportes/estadisticas
     - Métricas y estadísticas para dashboard
     - Query: ?periodo=2024-Q1

# 🆕 CREAR
POST /biomedicos/api/reportes/personalizado
     - Genera reporte personalizado según parámetros
     - Body: { tipo, filtros, columnas, formato }
```

### 3.3.3 Tareas de Desarrollo - Reportes

#### FASE 1: Backend (Python/Flask)

**Tarea 1.1: Crear módulo de generación de reportes**
```python
# app/biomedicos/report_generators.py

from app.models import HojaVidaBiomedico, Mantenimiento, Activo
from flask import render_template
from weasyprint import HTML
import pandas as pd
from datetime import datetime

class ReportGenerator:
    def __init__(self, tipo_reporte, filtros=None):
        self.tipo = tipo_reporte
        self.filtros = filtros or {}

    def generar_individual(self, activo_id):
        """Reporte consolidado de un activo."""
        pass

    def generar_mantenimientos_realizados(self):
        """Reporte grupal de mantenimientos."""
        pass

    def generar_hojas_vida_registradas(self):
        """Inventario de hojas de vida."""
        pass

    def generar_pendientes(self):
        """Mantenimientos pendientes."""
        pass

    def generar_estadisticas(self):
        """Dashboard de métricas."""
        pass

    def _aplicar_filtros(self, query):
        """Aplica filtros comunes a las queries."""
        pass

    def _exportar_excel(self, dataframe, nombre_archivo):
        """Exporta DataFrame a Excel."""
        pass

    def _exportar_pdf(self, html_content, nombre_archivo):
        """Exporta HTML a PDF."""
        pass
```

**Tarea 1.2: Implementar endpoints en routes.py**
- [ ] Implementar cada endpoint de reportes
- [ ] Agregar validación de filtros
- [ ] Optimizar queries con joins
- [ ] Agregar caché para reportes pesados

**Tarea 1.3: Crear queries optimizadas**
```python
# app/biomedicos/queries.py

def get_mantenimientos_con_filtros(filtros):
    """
    Query optimizada para reportes de mantenimientos.
    Incluye eager loading de relaciones.
    """
    query = Mantenimiento.query\
        .options(
            db.joinedload(Mantenimiento.activo),
            db.joinedload(Mantenimiento.tipo),
            db.joinedload(Mantenimiento.usuario)
        )

    if filtros.get('fecha_inicio'):
        query = query.filter(Mantenimiento.fecha_mantenimiento >= filtros['fecha_inicio'])

    # ... más filtros

    return query.all()
```

#### FASE 2: Frontend (Templates HTML)

**Tarea 2.1: Crear reportes_dashboard.html**
- [ ] Layout con cards para cada tipo de reporte
- [ ] Formularios de filtros por tipo de reporte
- [ ] Preview de reporte antes de generar
- [ ] Botones de descarga (PDF/Excel)
- [ ] Historial de reportes generados

**Tarea 2.2: Crear templates PDF de reportes**
- [ ] `pdf_templates/reporte_individual_consolidado.html`
- [ ] `pdf_templates/reporte_mantenimientos_realizados.html`
- [ ] `pdf_templates/reporte_hojas_vida.html`
- [ ] `pdf_templates/reporte_pendientes.html`
- [ ] `pdf_templates/reporte_estadisticas.html`

**Tarea 2.3: Crear componentes de filtros**
- [ ] `componentes/filtros_reportes.html`
  - Selectores de fecha
  - Multiselect de ubicaciones
  - Multiselect de tipos de mantenimiento
  - Checkbox de opciones
- [ ] `componentes/preview_reporte.html`
  - Vista previa en modal
  - Botón "Generar definitivo"

#### FASE 3: JavaScript

**Tarea 3.1: generador_reportes.js**
```javascript
class GeneradorReportes {
    constructor() {
        this.tipoSeleccionado = null;
        this.filtros = {};
    }

    seleccionarTipo(tipo) {
        this.tipoSeleccionado = tipo;
        this.mostrarFormularioFiltros(tipo);
    }

    mostrarFormularioFiltros(tipo) {
        // Carga formulario específico según tipo
        $('#filtros-container').load(`/biomedicos/reportes/filtros/${tipo}`);
    }

    generarPreview() {
        // Genera vista previa del reporte
        const filtros = this.recopilarFiltros();

        $.ajax({
            url: `/biomedicos/api/reportes/${this.tipoSeleccionado}/preview`,
            method: 'POST',
            data: JSON.stringify(filtros),
            contentType: 'application/json',
            success: (html) => {
                $('#preview-modal .modal-body').html(html);
                $('#preview-modal').modal('show');
            }
        });
    }

    generarFinal(formato = 'pdf') {
        const filtros = this.recopilarFiltros();

        // Construir URL con query params
        const params = new URLSearchParams({
            formato: formato,
            ...filtros
        });

        // Descargar archivo
        window.open(`/biomedicos/api/reportes/${this.tipoSeleccionado}?${params}`, '_blank');
    }

    recopilarFiltros() {
        // Recopila todos los filtros del formulario
        const filtros = {};

        $('#form-filtros input, #form-filtros select').each(function() {
            const name = $(this).attr('name');
            const value = $(this).val();
            if (value) filtros[name] = value;
        });

        return filtros;
    }
}

let generadorReportes = new GeneradorReportes();
```

**Tarea 3.2: filtros_dinamicos.js**
```javascript
// Carga dinámica de opciones según filtros previos
class FiltrosDinamicos {
    constructor() {
        this.filtrosActivos = {};
    }

    cargarUbicaciones(callback) {
        $.get('/api/ubicaciones', (data) => {
            this.renderSelect('ubicacion', data, callback);
        });
    }

    cargarTiposMantenimiento(callback) {
        $.get('/biomedicos/api/mantenimiento-tipos', (data) => {
            this.renderSelect('tipo_mantenimiento', data, callback);
        });
    }

    renderSelect(fieldName, options, callback) {
        // Renderiza select con opciones
        const select = $(`#filtro-${fieldName}`);
        select.empty();

        options.forEach(opt => {
            select.append(`<option value="${opt.id}">${opt.nombre}</option>`);
        });

        if (callback) callback();
    }

    aplicarFiltrosEncadenados() {
        // Filtros que dependen de otros
        // Ej: Al seleccionar ubicación, filtrar activos de esa ubicación
    }
}
```

#### FASE 4: Gráficos y Visualizaciones

**Tarea 4.1: Integrar Chart.js para estadísticas**
- [ ] Instalar Chart.js via CDN
- [ ] Crear gráficos de líneas para mantenimientos por mes
- [ ] Crear gráficos de torta para distribución de tipos
- [ ] Crear gráficos de barras para comparativas

**Ejemplo:**
```javascript
// dashboard_charts.js
function crearGraficoMantenimientosMes(data) {
    const ctx = document.getElementById('grafico-mantenimientos-mes').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.meses,
            datasets: [{
                label: 'Mantenimientos Realizados',
                data: data.valores,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
```

---

## 4. CRONOGRAMA DE TAREAS

### 4.1 Estimación de Tiempos

| Submódulo | Fase | Tareas | Tiempo Estimado |
|-----------|------|--------|----------------|
| **HOJAS DE VIDA** | Backend | Endpoints, validación, file handling | 12 horas |
|  | Frontend | Templates, wizard, tablas | 16 horas |
|  | JavaScript | Wizard, upload, interacciones | 14 horas |
|  | CSS | Estilos, responsive, animaciones | 6 horas |
|  | Testing | Pruebas integradas | 4 horas |
|  | **Subtotal** | | **52 horas** |
| **MANTENIMIENTOS** | Backend | Endpoints, borradores, PDFs | 14 horas |
|  | Frontend | Templates wizard 6 pasos, PDFs | 18 horas |
|  | JavaScript | Wizard, firmas, accesorios | 16 horas |
|  | CSS | Canvas, tablas, estados | 6 horas |
|  | Testing | Pruebas integradas | 4 horas |
|  | **Subtotal** | | **58 horas** |
| **REPORTES** | Backend | Generators, queries, exports | 16 horas |
|  | Frontend | Dashboard, formularios filtros | 12 horas |
|  | JavaScript | Generador, filtros, gráficos | 14 horas |
|  | CSS | Dashboard, gráficos | 4 horas |
|  | Testing | Pruebas de reportes | 4 horas |
|  | **Subtotal** | | **50 horas** |
| **INTEGRACIÓN** | Pruebas end-to-end | Flujos completos | 8 horas |
|  | Documentación | Manuales usuario | 6 horas |
|  | Ajustes finales | Bugs, optimización | 6 horas |
|  | **Subtotal** | | **20 horas** |
| **TOTAL GENERAL** | | | **180 horas** |

### 4.2 Cronograma Sugerido (6 Semanas)

**Asumiendo 30 horas/semana de desarrollo:**

#### SEMANA 1: Hojas de Vida - Backend + Frontend Base
- **Días 1-2:** Backend (endpoints, validación, file handling)
- **Días 3-4:** Templates HTML (wizard 4 pasos, tabla)
- **Día 5:** Testing inicial

#### SEMANA 2: Hojas de Vida - Frontend Completo
- **Días 1-2:** JavaScript (wizard, navegación)
- **Días 3-4:** Sistema de carga de archivos
- **Día 5:** CSS y responsive

#### SEMANA 3: Mantenimientos - Backend + Wizard
- **Días 1-2:** Backend (borradores, firmas)
- **Días 3-4:** Templates wizard 6 pasos
- **Día 5:** Testing inicial

#### SEMANA 4: Mantenimientos - Frontend Completo
- **Días 1-2:** JavaScript (wizard, canvas firmas)
- **Días 3-4:** Tabla de accesorios, generación PDFs
- **Día 5:** CSS y ajustes

#### SEMANA 5: Reportes
- **Días 1-2:** Backend (generators, queries)
- **Días 3-4:** Frontend (dashboard, filtros)
- **Día 5:** JavaScript (generador, gráficos)

#### SEMANA 6: Integración y Testing
- **Días 1-2:** Pruebas end-to-end
- **Días 3-4:** Ajustes y correcciones
- **Día 5:** Documentación y entrega

---

## 5. ESTRUCTURA DE BASE DE DATOS

### 5.1 Tablas Existentes (Ya en models.py)

#### hojas_vida_biomedicos
```sql
CREATE TABLE hojas_vida_biomedicos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    activo_id INT UNIQUE NOT NULL,

    -- Datos Generales
    permiso_comercializacion VARCHAR(100),
    n_factura VARCHAR(100),
    n_orden_compra VARCHAR(100),
    fecha_fabricacion DATE,
    fecha_instalacion DATE,

    -- Adquisición
    distribuidor VARCHAR(150),
    forma_adquisicion VARCHAR(100),
    telefono VARCHAR(50),
    correo_electronico VARCHAR(100),
    fecha_ingreso DATE,
    vencimiento_garantia DATE,
    costo FLOAT,
    vida_util_anios INT,

    -- Técnicos
    voltaje VARCHAR(50),
    frecuencia VARCHAR(50),
    dimensiones VARCHAR(100),
    corriente VARCHAR(50),
    potencia VARCHAR(50),
    peso VARCHAR(50),
    equipo_fijo_movil VARCHAR(20),
    humedad_relativa VARCHAR(50),
    temperatura_trabajo VARCHAR(50),
    manual_usuario BOOLEAN DEFAULT FALSE,
    manual_servicio BOOLEAN DEFAULT FALSE,
    clasificacion_riesgo VARCHAR(50),
    clasificacion_biomedica VARCHAR(100),
    periodicidad_mantenimiento VARCHAR(100),
    requiere_calibracion BOOLEAN DEFAULT FALSE,
    periodicidad_metrologia VARCHAR(100),

    FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE
);
```

#### documentos_adjuntos_biomedicos
```sql
CREATE TABLE documentos_adjuntos_biomedicos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    hoja_vida_id INT,
    activo_id INT,
    movimiento_id INT,
    tipo_documento VARCHAR(100) NOT NULL,  -- 'calibracion', 'mantenimiento_preventivo', etc.
    ruta_archivo VARCHAR(500) NOT NULL,
    nombre_archivo_original VARCHAR(200),
    checksum_sha256 VARCHAR(64),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_carga_id INT,
    tamano_bytes INT,
    mime_type VARCHAR(100),

    FOREIGN KEY (hoja_vida_id) REFERENCES hojas_vida_biomedicos(id) ON DELETE CASCADE,
    FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_carga_id) REFERENCES usuarios(id) ON DELETE SET NULL,

    CHECK (
        (hoja_vida_id IS NOT NULL) OR
        (activo_id IS NOT NULL) OR
        (movimiento_id IS NOT NULL)
    )
);
```

#### mantenimientos
```sql
CREATE TABLE mantenimientos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    activo_id INT NOT NULL,
    tipo_id INT NOT NULL,
    fecha_mantenimiento DATE NOT NULL,
    duracion_minutos INT,
    observaciones TEXT,
    usuario_id INT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',  -- 'Borrador', 'Pendiente', 'Completado', 'Cancelado'
    atributos_reporte_json JSON,  -- Campos dinámicos + accesorios

    FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE,
    FOREIGN KEY (tipo_id) REFERENCES mantenimiento_tipos(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),

    INDEX idx_estado (estado),
    INDEX idx_fecha (fecha_mantenimiento)
);
```

#### firmas
```sql
CREATE TABLE firmas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    documento_id INT NOT NULL,
    tipo_documento VARCHAR(20) NOT NULL,  -- 'movimiento', 'mantenimiento'
    rol_firma VARCHAR(50) NOT NULL,  -- 'ingeniero', 'receptor', etc.
    firma_base64 LONGTEXT NOT NULL,  -- Imagen PNG en base64
    nombre_firmante VARCHAR(200),
    firma_svg TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    timestamp_firma DATETIME DEFAULT CURRENT_TIMESTAMP,
    hash_documento VARCHAR(64),
    consentimiento_aceptado BOOLEAN DEFAULT FALSE,

    UNIQUE KEY uk_documento_tipo_rol (documento_id, tipo_documento, rol_firma)
);
```

### 5.2 Índices Sugeridos para Optimización

```sql
-- Índices para búsquedas frecuentes en hojas de vida
CREATE INDEX idx_hoja_vida_activo ON hojas_vida_biomedicos(activo_id);
CREATE INDEX idx_hoja_vida_fecha_ingreso ON hojas_vida_biomedicos(fecha_ingreso);

-- Índices para documentos
CREATE INDEX idx_doc_hoja_vida ON documentos_adjuntos_biomedicos(hoja_vida_id);
CREATE INDEX idx_doc_tipo ON documentos_adjuntos_biomedicos(tipo_documento);

-- Índices para mantenimientos
CREATE INDEX idx_mant_activo_fecha ON mantenimientos(activo_id, fecha_mantenimiento);
CREATE INDEX idx_mant_estado_fecha ON mantenimientos(estado, fecha_mantenimiento);
CREATE INDEX idx_mant_tipo ON mantenimientos(tipo_id);

-- Índices para firmas
CREATE INDEX idx_firma_documento ON firmas(documento_id, tipo_documento);
```

### 5.3 Datos Semilla Necesarios

```sql
-- Insertar tipos de mantenimiento básicos
INSERT INTO mantenimiento_tipos (nombre) VALUES
    ('Mantenimiento Preventivo'),
    ('Mantenimiento Correctivo'),
    ('Calibración'),
    ('Verificación Metrológica'),
    ('Mantenimiento Predictivo'),
    ('Inspección de Seguridad');

-- Nota: Los formatos específicos se cargan desde formatos.json
```

---

## 6. WIREFRAMES Y FLUJOS DE USUARIO

### 6.1 Wireframe: Vista de Tabla de Hojas de Vida

```
┌────────────────────────────────────────────────────────────────┐
│  GESTIÓN BIOMÉDICA > Hojas de Vida                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [🔍 Buscar...]  [Ubicación ▼]  [Estado ▼]  [➕ Nueva HdV]   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Placa  │ Equipo      │ Marca  │ Ubicación │ Acciones    │ │
│  ├────────┼─────────────┼────────┼───────────┼─────────────┤ │
│  │ BM-001 │ Monitor FC  │ Philips│ UCI       │ [Ver][PDF]  │ │
│  │ BM-002 │ Ventilador  │ Drager │ UCI-2     │ [Ver][PDF]  │ │
│  │ BM-003 │ Electrocardió│ GE    │ Urgencias │ [Ver][PDF]  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Mostrando 1-10 de 45 registros  [< 1 2 3 4 5 >]             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Wireframe: Wizard Hoja de Vida - Paso 1

```
┌────────────────────────────────────────────────────────────────┐
│  Crear Hoja de Vida - Paso 1 de 4: Datos Generales            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [●═══○───○───○]  Progreso: 25%                              │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Seleccionar Activo Biomédico:                            │ │
│  │ [🔍 Buscar por placa o nombre...]                        │ │
│  │                                                          │ │
│  │ ✅ Seleccionado: BM-101 - Monitor de Signos Vitales     │ │
│  │    Marca: Philips   Modelo: IntelliVue MP50             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Permiso Comercialización INVIMA: [___________________]       │
│  N° Factura:          [___________________]                   │
│  N° Orden de Compra:  [___________________]                   │
│  Fecha de Fabricación: [📅 dd/mm/yyyy]                        │
│  Fecha de Instalación: [📅 dd/mm/yyyy]                        │
│                                                                │
│  Distribuidor:        [___________________]                   │
│  Forma de Adquisición: [Seleccionar ▼]                        │
│  Teléfono:            [___________________]                   │
│  Correo Electrónico:  [___________________]                   │
│                                                                │
│  Fecha de Ingreso:         [📅 dd/mm/yyyy]                    │
│  Vencimiento de Garantía:  [📅 dd/mm/yyyy]                    │
│  Costo de Adquisición:     [$_____________]                   │
│  Vida Útil (años):         [____]                             │
│                                                                │
│                      [❌ Cancelar]  [Siguiente ➡️]            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 6.3 Wireframe: Wizard Hoja de Vida - Paso 3 (Documentos)

```
┌────────────────────────────────────────────────────────────────┐
│  Crear Hoja de Vida - Paso 3 de 4: Documentos Adjuntos        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [●═══●═══●───○]  Progreso: 75%                              │
│                                                                │
│  📋 1. Calibraciones (PDFs se unificarán)                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Arrastra archivos aquí o [📎 Seleccionar archivos]      │ │
│  │                                                          │ │
│  │ ✅ calibracion_2023_01.pdf  [🗑️]                        │ │
│  │ ✅ calibracion_2023_06.pdf  [🗑️]                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  🔧 2. Mantenimientos Preventivos Anteriores                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [📎 Seleccionar archivos]                                │ │
│  │                                                          │ │
│  │ ✅ mant_prev_2022.pdf  [🗑️]                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ⚠️ 3. Mantenimientos Correctivos Anteriores                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [📎 Seleccionar archivos]  (Sin archivos)               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  📄 4. Documentación Legal y Auditable                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [📎 Seleccionar archivos]                                │ │
│  │                                                          │ │
│  │ ✅ registro_invima.pdf  [🗑️]                            │ │
│  │ ✅ manual_usuario.pdf  [🗑️]                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  📷 Foto del Equipo (opcional)                                │
│  [📷 Capturar/Subir imagen]  ✅ foto_monitor.jpg  [🗑️]      │
│                                                                │
│                   [◀ Anterior]  [Siguiente ➡️]                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 6.4 Wireframe: Wizard Mantenimiento - Paso 6 (Firmas)

```
┌────────────────────────────────────────────────────────────────┐
│  Crear Mantenimiento - Paso 6 de 6: Firmas Digitales          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [●═══●═══●═══●═══●═══●]  Progreso: 100%                     │
│                                                                │
│  👨‍🔧 Firma del Ingeniero que realiza el mantenimiento         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                                                          │ │
│  │                  [Canvas de Firma]                       │ │
│  │                                                          │ │
│  │              (Área para dibujar firma)                   │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│  [🔄 Limpiar firma]                                           │
│                                                                │
│  Nombre completo: [Juan Pérez Gómez]                          │
│  Cargo:          [Ingeniero Biomédico]                        │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  ✅ Persona que recibe a conformidad                          │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                                                          │ │
│  │                  [Canvas de Firma]                       │ │
│  │                                                          │ │
│  │              (Área para dibujar firma)                   │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│  [🔄 Limpiar firma]                                           │
│                                                                │
│  Nombre completo: [_____________________________]             │
│  Cargo:          [_____________________________]             │
│                                                                │
│  ⚠️ Ambas firmas son obligatorias para completar              │
│                                                                │
│       [◀ Anterior]  [💾 Guardar Borrador]  [✅ Completar]     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 6.5 Flujo de Usuario: Crear Hoja de Vida

```
┌─────────────────┐
│   Usuario       │
│   Accede a      │
│ "Hojas de Vida" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Clic en        │
│ "➕ Nueva HdV"  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ PASO 1: Busca y selecciona activo       │
│ - Sistema valida que no tenga HdV       │
│ - Rellena datos generales               │
└────────┬────────────────────────────────┘
         │ [Siguiente ➡️]
         ▼
┌─────────────────────────────────────────┐
│ PASO 2: Ingresa datos técnicos          │
│ - Especificaciones eléctricas           │
│ - Características físicas               │
│ - Clasificaciones                       │
└────────┬────────────────────────────────┘
         │ [Siguiente ➡️]
         ▼
┌─────────────────────────────────────────┐
│ PASO 3: Sube documentos (4 categorías)  │
│ - Arrastra PDFs                         │
│ - Sistema sube a carpeta temporal       │
│ - Muestra lista de archivos             │
└────────┬────────────────────────────────┘
         │ [Siguiente ➡️]
         ▼
┌─────────────────────────────────────────┐
│ PASO 4: Revisa resumen completo         │
│ - Ve todos los datos                    │
│ - Ve lista de documentos                │
└────────┬────────────────────────────────┘
         │ [💾 Guardar]
         ▼
┌─────────────────────────────────────────┐
│ BACKEND:                                │
│ 1. Crea registro HojaVidaBiomedico      │
│ 2. Unifica PDFs por categoría           │
│ 3. Calcula checksums                    │
│ 4. Guarda archivos finales              │
│ 5. Crea registros DocumentoAdjunto      │
│ 6. Actualiza ruta_foto_activo           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ ✅ Éxito: Redirige a tabla de HdV      │
│    con mensaje "Hoja de Vida creada"   │
└─────────────────────────────────────────┘
```

### 6.6 Flujo de Usuario: Completar Mantenimiento con Firmas

```
┌──────────────────┐
│ Usuario accede a │
│ "Mantenimientos" │
└────────┬─────────┘
         │
         ▼
┌───────────────────┐
│ Clic en           │
│ "Nuevo Mantto"    │
└────────┬──────────┘
         │
         ▼
[Pasos 1-5: Datos, accesorios, reporte]
         │
         │ [Siguiente ➡️]
         ▼
┌─────────────────────────────────────────┐
│ PASO 6: FIRMAS DIGITALES               │
│                                         │
│ Canvas 1 (Ingeniero):                   │
│ - Usuario dibuja firma con mouse/touch  │
│ - Ingresa nombre y cargo                │
│                                         │
│ Canvas 2 (Receptor):                    │
│ - Receptor dibuja firma                 │
│ - Ingresa nombre y cargo                │
└────────┬────────────────────────────────┘
         │
         ├─── [💾 Guardar Borrador] ───┐
         │                              │
         │ [✅ Completar]               │
         │                              │
         ▼                              ▼
┌─────────────────────┐    ┌────────────────────┐
│ Validación:         │    │ Guarda con:        │
│ - Firmas vacías?    │    │ estado='Borrador'  │
│                     │    │ (sin validar)      │
│ SI: Error, retornar │    └────────────────────┘
│ NO: Continuar       │              │
└────────┬────────────┘              │
         │                           │
         ▼                           │
┌──────────────────────────────────┐ │
│ BACKEND:                         │ │
│ 1. Actualiza mantenimiento       │ │
│    estado='Completado'           │ │
│ 2. Convierte canvas a PNG base64 │ │
│ 3. Crea 2 registros en 'firmas':│ │
│    - firma_ingeniero             │ │
│    - firma_receptor              │ │
│ 4. Guarda metadatos (IP, etc.)   │ │
└────────┬─────────────────────────┘ │
         │                           │
         ▼                           │
┌──────────────────────────────────┐ │
│ ✅ Éxito: Muestra detalle del    │ │
│    mantenimiento con firmas      │ │
│    + Botón "📄 Generar PDF"      │ │
└──────────────────────────────────┘ │
                                     │
         ┌───────────────────────────┘
         │ Usuario retoma después
         ▼
┌────────────────────────────────┐
│ Desde tabla, clic en "▶️ Continuar" │
│ Carga datos del borrador      │
│ Usuario completa pasos faltantes│
└────────────────────────────────┘
```

---

## 7. CONSIDERACIONES ADICIONALES

### 7.1 Seguridad

**Validaciones Backend:**
- [ ] Validar que usuario tenga permisos para crear/editar hojas de vida
- [ ] Validar tipos de archivo permitidos (solo PDF, JPG, PNG)
- [ ] Validar tamaño máximo de archivos (10 MB por PDF, 5 MB por imagen)
- [ ] Sanitizar nombres de archivo para prevenir path traversal
- [ ] Validar checksums de archivos subidos
- [ ] Prevenir CSRF en formularios de wizard
- [ ] Validar que activo pertenezca a clase biomédica

**Integridad de Datos:**
- [ ] Transacciones atómicas para creación de HdV (si falla, rollback completo)
- [ ] Validar que activo exista antes de crear HdV
- [ ] Prevenir duplicados (un activo = una HdV)
- [ ] Backup automático de archivos críticos

### 7.2 Rendimiento

**Optimizaciones:**
- [ ] Eager loading en queries (joinedload de activos, tipos, usuarios)
- [ ] Paginación en tablas (máximo 50 registros por página)
- [ ] Caching de formatos.json en memoria
- [ ] Compresión de imágenes al subir
- [ ] Lazy loading de PDFs en vistas
- [ ] Índices en campos de búsqueda frecuente

**Procesamiento Asíncrono:**
- [ ] Generación de PDFs largos en background (Celery)
- [ ] Unificación de PDFs en worker separado
- [ ] Cálculo de checksums en background

### 7.3 Usabilidad

**UX/UI:**
- [ ] Tooltips explicativos en campos complejos
- [ ] Validación en tiempo real (feedback inmediato)
- [ ] Autoguardado cada 30 segundos en wizards
- [ ] Breadcrumbs para navegación
- [ ] Mensajes de error claros y específicos
- [ ] Loading spinners durante operaciones largas
- [ ] Confirmaciones antes de eliminar

**Accesibilidad:**
- [ ] Etiquetas ARIA para lectores de pantalla
- [ ] Navegación por teclado completa
- [ ] Contraste de colores adecuado
- [ ] Tamaños de fuente ajustables

### 7.4 Compatibilidad

**Navegadores:**
- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Edge 90+
- [ ] Safari 14+

**Dispositivos:**
- [ ] Desktop (1920x1080)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667) - funcionalidad básica

### 7.5 Testing

**Pruebas Unitarias (Pytest):**
```python
# tests/test_hojas_vida.py
def test_crear_hoja_vida_sin_activo():
    """No debe permitir crear HdV sin activo."""
    pass

def test_crear_hoja_vida_duplicada():
    """No debe permitir duplicar HdV para mismo activo."""
    pass

def test_merge_pdfs():
    """Debe unificar múltiples PDFs en uno solo."""
    pass

def test_checksum_archivo():
    """Debe calcular SHA256 correctamente."""
    pass
```

**Pruebas de Integración:**
```python
# tests/test_wizard_hojas_vida.py
def test_wizard_completo():
    """Simula flujo completo de wizard."""
    pass

def test_wizard_con_archivos():
    """Simula carga de archivos en paso 3."""
    pass
```

**Pruebas E2E (Selenium/Playwright):**
- [ ] Flujo completo: Login → Crear HdV → Verificar en tabla
- [ ] Flujo completo: Crear mantenimiento con firmas → Generar PDF
- [ ] Flujo: Generar reporte grupal con filtros

### 7.6 Documentación

**Manuales a Crear:**
1. **Manual de Usuario:**
   - Cómo crear hojas de vida
   - Cómo registrar mantenimientos
   - Cómo generar reportes
   - FAQ

2. **Manual Técnico:**
   - Arquitectura del módulo
   - Estructura de BD
   - APIs disponibles
   - Cómo extender formatos.json

3. **Manual de Instalación:**
   - Requisitos del sistema
   - Dependencias Python
   - Configuración de carpetas
   - Migraciones de BD

---

## 8. PRÓXIMOS PASOS INMEDIATOS

### Para empezar el desarrollo:

1. **AHORA MISMO:**
   - [ ] Revisar y aprobar este plan
   - [ ] Priorizar submódulos (¿empezamos por Hojas de Vida?)
   - [ ] Confirmar tecnologías (WeasyPrint, PyPDF2, etc.)

2. **ESTA SEMANA:**
   - [ ] Crear estructura de carpetas
   - [ ] Instalar dependencias necesarias
   - [ ] Crear ramas de desarrollo
   - [ ] Iniciar con Backend de Hojas de Vida

3. **PRÓXIMAS 2 SEMANAS:**
   - [ ] Completar Hojas de Vida (52 horas)
   - [ ] Testing inicial
   - [ ] Demo funcional para validación

---

## 9. PREGUNTAS PENDIENTES

Antes de empezar, necesito confirmar:

1. **¿Formatos de Reporte?**
   - ¿Los formatos en formatos.json son finales o hay que agregar más?
   - ¿Cada tipo de mantenimiento tiene su template PDF único?

2. **¿Sistema de Permisos?**
   - ¿Todos los usuarios pueden crear HdV y mantenimientos?
   - ¿Hay roles específicos (Ingeniero, Jefe, Admin)?

3. **¿Integraciones Externas?**
   - ¿Se integra con algún sistema de gestión hospitalaria?
   - ¿Se exportan datos a otros sistemas?

4. **¿Notificaciones?**
   - ¿Enviar emails cuando se crea un mantenimiento?
   - ¿Alertas de mantenimientos vencidos?

5. **¿Prioridad de Reportes?**
   - ¿Qué reportes son más urgentes? ¿Empezamos por alguno en específico?

---

## 10. RECURSOS NECESARIOS

### Software:
- ✅ Python 3.12
- ✅ Flask
- ✅ SQLAlchemy
- ✅ WeasyPrint (para PDFs)
- 🆕 PyPDF2 (para unificar PDFs)
- 🆕 Pillow (para comprimir imágenes)
- 🆕 Chart.js (para gráficos en reportes)

### Librerías JavaScript:
- ✅ jQuery
- ✅ DataTables
- 🆕 Signature Pad (canvas de firmas)
- 🆕 Dropzone.js (drag & drop archivos)
- 🆕 Chart.js (gráficos)

---

**FIN DEL PLAN DE ACCIÓN DETALLADO**

---

## Resumen Ejecutivo

Este plan detalla la implementación completa del módulo biomédico con:
- **3 submódulos principales:** Hojas de Vida, Mantenimientos, Reportes
- **Tiempo estimado:** 180 horas (6 semanas a 30h/semana)
- **Tecnologías:** Python/Flask, SQLAlchemy, JavaScript, WeasyPrint, Chart.js
- **Entregables:** Sistema completo funcional, documentado y testeado

El desarrollo es modular e incremental, permitiendo entregas parciales funcionales.

**Próximo paso sugerido:** Empezar con el submódulo de HOJAS DE VIDA (Backend + Frontend básico) en las próximas 2 semanas.
