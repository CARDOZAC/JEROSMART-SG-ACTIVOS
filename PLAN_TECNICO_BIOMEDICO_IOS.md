# ESPECIFICACIONES TÉCNICAS - MÓDULO BIOMÉDICO
## Stack Tecnológico y Guía de Implementación iOS

---

## 🎨 STACK TECNOLÓGICO DEFINIDO

### Frontend
- ✅ **HTML5 + Jinja2** (Templates del lado del servidor)
- ✅ **CSS Puro** con tu sistema de diseño iOS existente
- ✅ **JavaScript Vanilla** (sin frameworks pesados)
- ✅ **Bootstrap 5.3.3** (solo para grid y utilidades)
- ✅ **Bootstrap Icons** para iconografía

### Backend
- ✅ **Python 3.12**
- ✅ **Flask** (framework web)
- ✅ **SQLAlchemy** (ORM)
- ✅ **WeasyPrint** (generación de PDFs)

### Librerías JavaScript Ligeras
- ✅ **jQuery 3.x** (manipulación DOM, AJAX)
- ✅ **Signature Pad** (canvas de firmas - ya implementado)
- 🆕 **Dropzone.js** (drag & drop de archivos)
- 🆕 **Chart.js** (gráficos para reportes)

### Base de Datos
- ✅ **MySQL 8.0** (ya configurado)
- ✅ **Modelos ya creados en `app/models.py`**

---

## 📐 SISTEMA DE DISEÑO iOS (Ya Implementado)

### Archivos CSS Existentes a Reutilizar

```
app/static/css/
├── ios-design-system.css      ✅ Sistema completo iOS
├── ios-style.css              ✅ Estilos adicionales
├── ios-theme.css              ✅ Temas claro/oscuro
├── ios-signature.css          ✅ Canvas de firmas
├── ios-wizard.css             ✅ Wizards paso a paso
├── wizard.css                 ✅ Estilos de wizard
├── wizard-clean.css           ✅ Wizard minimalista
└── signature_wizard.css       ✅ Wizard con firmas
```

### Paleta de Colores iOS (De tu sistema existente)

```css
/* Colores principales */
--ios-blue: #007AFF;           /* Botones primarios */
--ios-green: #34C759;          /* Éxito */
--ios-orange: #FF9500;         /* Advertencias */
--ios-red: #FF3B30;            /* Errores */

/* Fondos */
--ios-bg-primary: #F2F2F7;     /* Fondo principal */
--ios-bg-secondary: #FFFFFF;   /* Tarjetas */

/* Texto */
--ios-label-primary: #000000;
--ios-label-secondary: #3C3C43;

/* Border Radius */
--ios-radius-xs: 6px;
--ios-radius-sm: 10px;
--ios-radius-md: 14px;
--ios-radius-lg: 18px;
```

---

## 🏗️ ARQUITECTURA DE COMPONENTES

### Patrón de Diseño: MVC Tradicional

```
┌─────────────────────────────────────────────────┐
│                   USUARIO                       │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│            TEMPLATES (Views)                    │
│  • Jinja2 con herencia                         │
│  • Componentes reutilizables                   │
│  • CSS iOS nativo                              │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│         JAVASCRIPT (Interactividad)             │
│  • Vanilla JS + jQuery                         │
│  • Clases ES6 para organización                │
│  • AJAX para comunicación con backend          │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│           ROUTES (Controllers)                  │
│  • app/biomedicos/routes.py                    │
│  • Endpoints REST para APIs                    │
│  • Renderizado de templates                   │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│            MODELS (Database)                    │
│  • SQLAlchemy ORM                              │
│  • app/models.py                               │
└─────────────────────────────────────────────────┘
```

---

## 📱 COMPONENTES REUTILIZABLES iOS

### 1. Botones iOS

Ya implementado en tu sistema, usar clases existentes:

```html
<!-- Botón primario iOS -->
<button class="ios-btn ios-btn-primary">
    <i class="bi bi-plus-circle"></i> Agregar
</button>

<!-- Botón secundario iOS -->
<button class="ios-btn ios-btn-secondary">
    Cancelar
</button>

<!-- Botón destructivo -->
<button class="ios-btn ios-btn-danger">
    <i class="bi bi-trash"></i> Eliminar
</button>
```

### 2. Cards iOS (Tarjetas)

```html
<div class="ios-card">
    <div class="ios-card-header">
        <h3 class="ios-card-title">Título de la Tarjeta</h3>
    </div>
    <div class="ios-card-body">
        Contenido de la tarjeta
    </div>
</div>
```

Estilos sugeridos para agregar:

```css
/* Agregar a ios-design-system.css si no existe */
.ios-card {
    background: var(--ios-bg-secondary);
    border-radius: var(--ios-radius-md);
    box-shadow: var(--ios-shadow-sm);
    overflow: hidden;
    margin-bottom: var(--ios-space-md);
}

.ios-card-header {
    padding: var(--ios-space-md);
    border-bottom: 0.5px solid var(--ios-separator);
}

.ios-card-title {
    font-size: var(--ios-font-size-headline);
    font-weight: 600;
    margin: 0;
    color: var(--ios-label-primary);
}

.ios-card-body {
    padding: var(--ios-space-md);
}
```

### 3. Lista iOS Grouped (Para tablas de datos)

```html
<div class="ios-list-grouped">
    <div class="ios-list-header">Equipos Biomédicos</div>

    <div class="ios-list-item" onclick="verDetalle(1)">
        <div class="ios-list-content">
            <div class="ios-list-title">Monitor de Signos Vitales</div>
            <div class="ios-list-subtitle">BM-001 • UCI</div>
        </div>
        <i class="bi bi-chevron-right ios-list-chevron"></i>
    </div>

    <div class="ios-list-item" onclick="verDetalle(2)">
        <div class="ios-list-content">
            <div class="ios-list-title">Ventilador Mecánico</div>
            <div class="ios-list-subtitle">BM-002 • UCI-2</div>
        </div>
        <i class="bi bi-chevron-right ios-list-chevron"></i>
    </div>
</div>
```

Estilos:

```css
.ios-list-grouped {
    background: transparent;
    margin: var(--ios-space-md) 0;
}

.ios-list-header {
    font-size: var(--ios-font-size-footnote);
    text-transform: uppercase;
    color: var(--ios-label-secondary);
    padding: var(--ios-space-sm) var(--ios-space-md);
    font-weight: 400;
    letter-spacing: 0.5px;
}

.ios-list-item {
    background: var(--ios-bg-secondary);
    padding: var(--ios-space-md);
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 0.5px solid var(--ios-separator);
    cursor: pointer;
    transition: background-color 0.2s;
}

.ios-list-item:first-of-type {
    border-top-left-radius: var(--ios-radius-sm);
    border-top-right-radius: var(--ios-radius-sm);
}

.ios-list-item:last-of-type {
    border-bottom: none;
    border-bottom-left-radius: var(--ios-radius-sm);
    border-bottom-right-radius: var(--ios-radius-sm);
}

.ios-list-item:hover {
    background: var(--ios-bg-tertiary);
}

.ios-list-item:active {
    background: var(--ios-gray-6);
}

.ios-list-content {
    flex: 1;
}

.ios-list-title {
    font-size: var(--ios-font-size-body);
    font-weight: 400;
    color: var(--ios-label-primary);
    margin-bottom: 2px;
}

.ios-list-subtitle {
    font-size: var(--ios-font-size-footnote);
    color: var(--ios-label-secondary);
}

.ios-list-chevron {
    color: var(--ios-gray-3);
    font-size: 14px;
}
```

### 4. Wizard iOS (Ya implementado)

Basado en tu `wizard-clean.css` y `ios-wizard.css`:

```html
<div class="wizard-container">
    <!-- Barra de progreso -->
    <div class="wizard-progress">
        <div class="wizard-step active">
            <div class="wizard-step-circle">1</div>
            <div class="wizard-step-label">Datos Generales</div>
        </div>
        <div class="wizard-step">
            <div class="wizard-step-circle">2</div>
            <div class="wizard-step-label">Datos Técnicos</div>
        </div>
        <div class="wizard-step">
            <div class="wizard-step-circle">3</div>
            <div class="wizard-step-label">Documentos</div>
        </div>
        <div class="wizard-step">
            <div class="wizard-step-circle">4</div>
            <div class="wizard-step-label">Resumen</div>
        </div>
    </div>

    <!-- Contenido del paso actual -->
    <div class="wizard-content">
        <div class="wizard-panel active" id="paso1">
            <!-- Contenido paso 1 -->
        </div>
        <div class="wizard-panel" id="paso2">
            <!-- Contenido paso 2 -->
        </div>
    </div>

    <!-- Botones de navegación -->
    <div class="wizard-footer">
        <button class="ios-btn ios-btn-secondary" id="btn-prev">
            <i class="bi bi-chevron-left"></i> Anterior
        </button>
        <button class="ios-btn ios-btn-primary" id="btn-next">
            Siguiente <i class="bi bi-chevron-right"></i>
        </button>
    </div>
</div>
```

### 5. Drag & Drop iOS para Archivos

Integración con Dropzone.js (librería ligera):

```html
<!-- En el <head> -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/min/dropzone.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/min/dropzone.min.js"></script>

<!-- Área de carga -->
<div class="ios-dropzone" id="dropzone-calibraciones">
    <div class="ios-dropzone-content">
        <i class="bi bi-cloud-upload" style="font-size: 48px; color: var(--ios-blue);"></i>
        <h4>Arrastra archivos PDF aquí</h4>
        <p class="text-muted">o haz clic para seleccionar</p>
    </div>
</div>
```

JavaScript:

```javascript
// Configuración estilo iOS
Dropzone.options.dropzoneCalibraciones = {
    url: "/biomedicos/api/hojas-vida/upload-temp",
    paramName: "file",
    maxFilesize: 10, // MB
    acceptedFiles: "application/pdf",
    addRemoveLinks: true,
    dictDefaultMessage: "",
    dictRemoveFile: "Eliminar",
    dictCancelUpload: "Cancelar",
    init: function() {
        this.on("success", function(file, response) {
            console.log("Archivo subido:", response);
            // Guardar file_id en array temporal
        });
    }
};
```

Estilos personalizados:

```css
.ios-dropzone {
    background: var(--ios-bg-secondary);
    border: 2px dashed var(--ios-separator);
    border-radius: var(--ios-radius-md);
    padding: var(--ios-space-xl);
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
}

.ios-dropzone:hover {
    border-color: var(--ios-blue);
    background: var(--ios-bg-tertiary);
}

.ios-dropzone.dz-drag-hover {
    border-color: var(--ios-blue);
    background: rgba(0, 122, 255, 0.05);
}

.ios-dropzone .dz-preview {
    margin: var(--ios-space-sm);
    padding: var(--ios-space-sm);
    background: var(--ios-bg-tertiary);
    border-radius: var(--ios-radius-xs);
}
```

---

## 🔧 ESTRUCTURA DE ARCHIVOS DETALLADA

### Backend (Python)

```
app/biomedicos/
│
├── __init__.py                    # Blueprint registration
│
├── routes.py                      # ✅ YA EXISTE - Endpoints API
│   ├── GET /api/hojas-vida
│   ├── POST /api/hojas-vida
│   ├── GET /api/mantenimientos
│   └── ... (otros endpoints)
│
├── context_builders.py            # ✅ YA EXISTE - Builders para PDFs
│
├── formatos.json                  # ✅ YA EXISTE - Tipos de reportes
│
├── forms.py                       # 🆕 CREAR
│   └── WTForms para validación
│
├── file_handlers.py               # 🆕 CREAR
│   ├── save_temp_file()
│   ├── merge_pdf_documents()
│   ├── calculate_sha256()
│   └── compress_image()
│
├── pdf_generators.py              # 🆕 CREAR
│   ├── generar_pdf_hoja_vida()
│   ├── generar_pdf_mantenimiento()
│   └── generar_pdf_reporte_grupal()
│
└── queries.py                     # 🆕 CREAR
    └── Queries optimizadas con filtros
```

### Frontend - Templates (Jinja2)

```
app/templates/biomedicos/
│
├── hojas_vida/
│   ├── ver_hojas_vida.html               # 🆕 Tabla principal
│   ├── wizard_hoja_vida.html             # 🆕 Wizard 4 pasos
│   ├── detalle_hoja_vida.html            # 🆕 Vista detallada
│   │
│   └── componentes/
│       ├── paso1_datos_generales.html    # 🆕 Paso 1 wizard
│       ├── paso2_datos_tecnicos.html     # 🆕 Paso 2 wizard
│       ├── paso3_documentos.html         # 🆕 Paso 3 wizard
│       └── paso4_resumen.html            # 🆕 Paso 4 wizard
│
├── mantenimientos/
│   ├── ver_mantenimientos.html           # ✅ Mejorar existente
│   ├── wizard_mantenimiento.html         # 🆕 Wizard 6 pasos
│   │
│   └── componentes/
│       ├── paso1_seleccionar_activo.html
│       ├── paso2_tipo_reporte.html
│       ├── paso3_datos_tecnico.html
│       ├── paso4_accesorios.html
│       ├── paso5_reporte_tecnico.html
│       └── paso6_firmas.html             # Reutilizar firmar.html
│
├── reportes/
│   ├── dashboard_reportes.html           # 🆕 Selector de reportes
│   │
│   └── componentes/
│       ├── filtros_reportes.html
│       └── preview_reporte.html
│
└── pdf_templates/                         # Templates para PDFs
    ├── hoja_vida_consolidada.html        # ✅ YA EXISTE
    ├── mantenimiento_preventivo.html     # 🆕 CREAR
    ├── mantenimiento_correctivo.html     # 🆕 CREAR
    └── reporte_grupal.html               # 🆕 CREAR
```

### Frontend - JavaScript

```
app/static/js/biomedicos/
│
├── hojas_vida/
│   ├── wizard_hoja_vida.js               # 🆕 Lógica del wizard
│   ├── tabla_hojas_vida.js               # 🆕 Tabla interactiva
│   └── upload_documentos.js              # 🆕 Drag & drop
│
├── mantenimientos/
│   ├── wizard_mantenimiento.js           # 🆕 Wizard 6 pasos
│   ├── tabla_accesorios.js               # 🆕 Tabla dinámica
│   └── canvas_firmas.js                  # ✅ Reutilizar existente
│
└── reportes/
    ├── generador_reportes.js             # 🆕 Dashboard reportes
    └── filtros_dinamicos.js              # 🆕 Filtros encadenados
```

### Frontend - CSS

```
app/static/css/
│
├── ios-design-system.css                 # ✅ Base del sistema
├── ios-wizard.css                        # ✅ Estilos wizard
├── ios-signature.css                     # ✅ Canvas firmas
│
└── biomedicos/                           # 🆕 Estilos específicos
    ├── hojas-vida.css
    ├── mantenimientos.css
    └── reportes.css
```

---

## 💻 EJEMPLOS DE CÓDIGO

### 1. Template Base para Módulo Biomédico

```html
<!-- app/templates/biomedicos/base_biomedico.html -->
{% extends "base.html" %}

{% block head_extra %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/ios-wizard.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/biomedicos/hojas-vida.css') }}">
{% endblock %}

{% block content %}
<div class="container-fluid" style="max-width: 1400px; padding: var(--ios-space-lg);">

    <!-- Breadcrumb iOS -->
    <nav aria-label="breadcrumb" style="margin-bottom: var(--ios-space-md);">
        <ol class="breadcrumb" style="background: transparent; padding: 0;">
            <li class="breadcrumb-item">
                <a href="{{ url_for('main.index') }}" style="color: var(--ios-blue);">
                    <i class="bi bi-house-door"></i> Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                Gestión Biomédica
            </li>
        </ol>
    </nav>

    <!-- Título de la página -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h1 class="h2" style="font-weight: 600; color: var(--ios-label-primary); margin-bottom: 4px;">
                {% block page_title %}Gestión Biomédica{% endblock %}
            </h1>
            <p class="text-muted" style="font-size: var(--ios-font-size-subhead); margin: 0;">
                {% block page_subtitle %}Sistema de gestión de equipos biomédicos{% endblock %}
            </p>
        </div>
        {% block page_actions %}{% endblock %}
    </div>

    <!-- Contenido específico -->
    {% block biomedico_content %}{% endblock %}

</div>
{% endblock %}

{% block scripts %}
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
{% block biomedico_scripts %}{% endblock %}
{% endblock %}
```

### 2. Tabla iOS de Hojas de Vida

```html
<!-- app/templates/biomedicos/hojas_vida/ver_hojas_vida.html -->
{% extends "biomedicos/base_biomedico.html" %}

{% block page_title %}Hojas de Vida{% endblock %}
{% block page_subtitle %}Gestión de hojas de vida de equipos biomédicos{% endblock %}

{% block page_actions %}
<a href="{{ url_for('biomedicos.wizard_hoja_vida') }}" class="ios-btn ios-btn-primary">
    <i class="bi bi-plus-circle"></i> Nueva Hoja de Vida
</a>
{% endblock %}

{% block biomedico_content %}

<!-- Filtros iOS -->
<div class="ios-card mb-4">
    <div class="ios-card-body">
        <form id="form-filtros" class="row g-3">
            <div class="col-md-4">
                <input type="text"
                       class="form-control ios-input"
                       id="filtro-placa"
                       placeholder="🔍 Buscar por placa o nombre">
            </div>
            <div class="col-md-3">
                <select class="form-select ios-select" id="filtro-ubicacion">
                    <option value="">Todas las ubicaciones</option>
                    <option value="UCI">UCI</option>
                    <option value="Urgencias">Urgencias</option>
                    <!-- ... -->
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select ios-select" id="filtro-estado">
                    <option value="">Todos los estados</option>
                    <option value="completo">Completo</option>
                    <option value="incompleto">Incompleto</option>
                </select>
            </div>
            <div class="col-md-2">
                <button type="button" class="ios-btn ios-btn-secondary w-100" onclick="limpiarFiltros()">
                    Limpiar
                </button>
            </div>
        </form>
    </div>
</div>

<!-- Lista iOS Grouped -->
<div class="ios-list-grouped" id="lista-hojas-vida">
    <!-- Cargado dinámicamente con JavaScript -->
    <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Cargando...</span>
        </div>
    </div>
</div>

<!-- Paginación -->
<nav aria-label="Paginación" class="mt-4">
    <ul class="pagination justify-content-center" id="paginacion">
        <!-- Generado dinámicamente -->
    </ul>
</nav>

{% endblock %}

{% block biomedico_scripts %}
<script src="{{ url_for('static', filename='js/biomedicos/hojas_vida/tabla_hojas_vida.js') }}"></script>
<script>
    // Inicializar tabla
    document.addEventListener('DOMContentLoaded', function() {
        cargarHojasVida();
    });
</script>
{% endblock %}
```

### 3. JavaScript para Tabla de Hojas de Vida

```javascript
// app/static/js/biomedicos/hojas_vida/tabla_hojas_vida.js

let paginaActual = 1;
let totalPaginas = 1;
const itemsPorPagina = 20;

/**
 * Carga las hojas de vida desde el backend
 */
function cargarHojasVida() {
    const filtros = obtenerFiltros();

    // Mostrar loading
    mostrarLoading();

    // AJAX con jQuery
    $.ajax({
        url: '/biomedicos/api/hojas-vida',
        method: 'GET',
        data: {
            pagina: paginaActual,
            por_pagina: itemsPorPagina,
            ...filtros
        },
        success: function(response) {
            renderizarHojasVida(response.hojas_vida);
            renderizarPaginacion(response.total, response.pagina_actual);
        },
        error: function(xhr) {
            mostrarError('Error al cargar hojas de vida');
        }
    });
}

/**
 * Renderiza la lista de hojas de vida estilo iOS
 */
function renderizarHojasVida(hojasVida) {
    const container = document.getElementById('lista-hojas-vida');

    if (hojasVida.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-inbox" style="font-size: 64px; color: var(--ios-gray-3);"></i>
                <h4 class="mt-3 text-muted">No hay hojas de vida registradas</h4>
            </div>
        `;
        return;
    }

    let html = '<div class="ios-list-header">Equipos Biomédicos</div>';

    hojasVida.forEach(hdv => {
        const badge = hdv.tiene_hoja_vida
            ? '<span class="badge bg-success">Completo</span>'
            : '<span class="badge bg-warning">Pendiente</span>';

        html += `
            <div class="ios-list-item" onclick="verDetalleHdV(${hdv.activo_id})">
                <div class="ios-list-content">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="ios-list-title">${hdv.nombre_activo}</div>
                            <div class="ios-list-subtitle">
                                ${hdv.placa_codigo_interno} • ${hdv.ubicacion || 'Sin ubicación'}
                            </div>
                        </div>
                        ${badge}
                    </div>
                </div>
                <i class="bi bi-chevron-right ios-list-chevron"></i>
            </div>
        `;
    });

    container.innerHTML = html;
}

/**
 * Ver detalle de hoja de vida
 */
function verDetalleHdV(activoId) {
    window.location.href = `/biomedicos/hojas-vida/${activoId}`;
}

/**
 * Obtener filtros del formulario
 */
function obtenerFiltros() {
    return {
        placa: document.getElementById('filtro-placa').value,
        ubicacion: document.getElementById('filtro-ubicacion').value,
        estado: document.getElementById('filtro-estado').value
    };
}

/**
 * Mostrar loading
 */
function mostrarLoading() {
    const container = document.getElementById('lista-hojas-vida');
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
}

/**
 * Mostrar error con notificación iOS
 */
function mostrarError(mensaje) {
    // Usar tu sistema de notificaciones existente
    alert(mensaje); // Placeholder
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Filtros en tiempo real
    document.getElementById('filtro-placa').addEventListener('input', debounce(cargarHojasVida, 500));
    document.getElementById('filtro-ubicacion').addEventListener('change', cargarHojasVida);
    document.getElementById('filtro-estado').addEventListener('change', cargarHojasVida);
});

// Utilidad de debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

### 4. Clase JavaScript para Wizard de Hoja de Vida

```javascript
// app/static/js/biomedicos/hojas_vida/wizard_hoja_vida.js

class WizardHojaVida {
    constructor() {
        this.pasoActual = 1;
        this.totalPasos = 4;
        this.datos = {};
        this.archivosTemp = {
            calibraciones: [],
            mantenimientos_preventivos: [],
            mantenimientos_correctivos: [],
            documentacion_legal: []
        };

        this.init();
    }

    init() {
        this.cargarEventos();
        this.cargarDatosGuardados();
        this.actualizarUI();
    }

    cargarEventos() {
        document.getElementById('btn-siguiente').addEventListener('click', () => this.siguientePaso());
        document.getElementById('btn-anterior').addEventListener('click', () => this.pasoAnterior());
        document.getElementById('btn-guardar').addEventListener('click', () => this.guardarHojaVida());
    }

    siguientePaso() {
        // Validar paso actual
        if (!this.validarPaso(this.pasoActual)) {
            return;
        }

        // Guardar datos del paso
        this.guardarDatosPaso(this.pasoActual);

        // Avanzar
        if (this.pasoActual < this.totalPasos) {
            this.pasoActual++;
            this.actualizarUI();
            this.guardarEnSession();
        }
    }

    pasoAnterior() {
        if (this.pasoActual > 1) {
            this.pasoActual--;
            this.actualizarUI();
        }
    }

    validarPaso(paso) {
        switch(paso) {
            case 1:
                return this.validarPaso1();
            case 2:
                return this.validarPaso2();
            case 3:
                return true; // Documentos son opcionales
            case 4:
                return true; // Resumen no requiere validación
            default:
                return true;
        }
    }

    validarPaso1() {
        const activoId = document.getElementById('activo-seleccionado').value;

        if (!activoId) {
            this.mostrarError('Debes seleccionar un activo biomédico');
            return false;
        }

        // Validar campos obligatorios
        const camposRequeridos = [
            'fecha-ingreso',
            'costo-adquisicion'
        ];

        for (let campo of camposRequeridos) {
            const valor = document.getElementById(campo).value;
            if (!valor) {
                this.mostrarError(`El campo es obligatorio: ${campo}`);
                return false;
            }
        }

        return true;
    }

    validarPaso2() {
        // Validaciones de datos técnicos
        return true;
    }

    guardarDatosPaso(paso) {
        const formulario = document.getElementById(`form-paso${paso}`);
        const formData = new FormData(formulario);

        formData.forEach((value, key) => {
            this.datos[key] = value;
        });
    }

    actualizarUI() {
        // Ocultar todos los pasos
        for (let i = 1; i <= this.totalPasos; i++) {
            document.getElementById(`paso${i}`).classList.remove('active');
            document.querySelector(`.wizard-step[data-step="${i}"]`).classList.remove('active');
        }

        // Mostrar paso actual
        document.getElementById(`paso${this.pasoActual}`).classList.add('active');
        document.querySelector(`.wizard-step[data-step="${this.pasoActual}"]`).classList.add('active');

        // Actualizar botones
        document.getElementById('btn-anterior').disabled = (this.pasoActual === 1);

        if (this.pasoActual === this.totalPasos) {
            document.getElementById('btn-siguiente').style.display = 'none';
            document.getElementById('btn-guardar').style.display = 'inline-block';
        } else {
            document.getElementById('btn-siguiente').style.display = 'inline-block';
            document.getElementById('btn-guardar').style.display = 'none';
        }

        // Scroll al inicio
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    guardarEnSession() {
        sessionStorage.setItem('wizard_hoja_vida', JSON.stringify({
            paso: this.pasoActual,
            datos: this.datos,
            archivos: this.archivosTemp
        }));
    }

    cargarDatosGuardados() {
        const guardado = sessionStorage.getItem('wizard_hoja_vida');
        if (guardado) {
            const datos = JSON.parse(guardado);
            this.pasoActual = datos.paso || 1;
            this.datos = datos.datos || {};
            this.archivosTemp = datos.archivos || {};

            // Rellenar formularios con datos guardados
            this.rellenarFormularios();
        }
    }

    rellenarFormularios() {
        for (let [key, value] of Object.entries(this.datos)) {
            const campo = document.getElementById(key);
            if (campo) {
                campo.value = value;
            }
        }
    }

    async guardarHojaVida() {
        // Mostrar loading
        this.mostrarLoading('Guardando hoja de vida...');

        // Preparar datos
        const formData = new FormData();

        // Agregar todos los datos del wizard
        for (let [key, value] of Object.entries(this.datos)) {
            formData.append(key, value);
        }

        // Agregar archivos temporales
        for (let [categoria, archivos] of Object.entries(this.archivosTemp)) {
            formData.append(`archivos_${categoria}`, JSON.stringify(archivos));
        }

        try {
            const response = await fetch('/biomedicos/api/hojas-vida', {
                method: 'POST',
                body: formData
            });

            const resultado = await response.json();

            if (resultado.success) {
                this.mostrarExito('Hoja de vida creada exitosamente');

                // Limpiar sessionStorage
                sessionStorage.removeItem('wizard_hoja_vida');

                // Redirigir
                setTimeout(() => {
                    window.location.href = '/biomedicos/hojas-vida';
                }, 1500);
            } else {
                this.mostrarError(resultado.message);
            }
        } catch (error) {
            this.mostrarError('Error al guardar la hoja de vida');
        } finally {
            this.ocultarLoading();
        }
    }

    mostrarError(mensaje) {
        // Usar sistema de notificaciones iOS
        alert(mensaje); // Placeholder
    }

    mostrarExito(mensaje) {
        alert(mensaje); // Placeholder
    }

    mostrarLoading(mensaje) {
        // Implementar overlay con spinner
    }

    ocultarLoading() {
        // Ocultar overlay
    }
}

// Inicializar wizard
let wizard;
document.addEventListener('DOMContentLoaded', function() {
    wizard = new WizardHojaVida();
});
```

---

## 📊 SISTEMA DE NOTIFICACIONES iOS

Crear un sistema de notificaciones toast estilo iOS:

```javascript
// app/static/js/ios-toast.js

class iOSToast {
    static show(mensaje, tipo = 'info', duracion = 3000) {
        const toast = document.createElement('div');
        toast.className = `ios-toast ios-toast-${tipo}`;
        toast.innerHTML = `
            <div class="ios-toast-content">
                <i class="bi ${this.getIcon(tipo)} me-2"></i>
                <span>${mensaje}</span>
            </div>
        `;

        document.body.appendChild(toast);

        // Animar entrada
        setTimeout(() => toast.classList.add('show'), 100);

        // Animar salida
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duracion);
    }

    static getIcon(tipo) {
        const icons = {
            'success': 'bi-check-circle-fill',
            'error': 'bi-x-circle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'info': 'bi-info-circle-fill'
        };
        return icons[tipo] || icons['info'];
    }
}

// Alias globales
window.showSuccess = (msg) => iOSToast.show(msg, 'success');
window.showError = (msg) => iOSToast.show(msg, 'error');
window.showWarning = (msg) => iOSToast.show(msg, 'warning');
window.showInfo = (msg) => iOSToast.show(msg, 'info');
```

CSS:

```css
/* app/static/css/ios-toast.css */

.ios-toast {
    position: fixed;
    top: 80px;
    left: 50%;
    transform: translateX(-50%) translateY(-20px);
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: var(--ios-radius-md);
    padding: 12px 20px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: none;
}

.ios-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.ios-toast-content {
    display: flex;
    align-items: center;
    font-size: var(--ios-font-size-subhead);
    color: var(--ios-label-primary);
    font-weight: 500;
}

.ios-toast-success { border-left: 4px solid var(--ios-green); }
.ios-toast-error { border-left: 4px solid var(--ios-red); }
.ios-toast-warning { border-left: 4px solid var(--ios-orange); }
.ios-toast-info { border-left: 4px solid var(--ios-blue); }

.ios-toast-success i { color: var(--ios-green); }
.ios-toast-error i { color: var(--ios-red); }
.ios-toast-warning i { color: var(--ios-orange); }
.ios-toast-info i { color: var(--ios-blue); }
```

---

## 🎯 RESUMEN DE TECNOLOGÍAS

| Componente | Tecnología | Estado |
|------------|-----------|--------|
| **Backend Framework** | Flask | ✅ Implementado |
| **ORM** | SQLAlchemy | ✅ Implementado |
| **Templates** | Jinja2 | ✅ Implementado |
| **CSS Framework** | Bootstrap 5 (solo grid) | ✅ Implementado |
| **Diseño** | Sistema iOS Personalizado | ✅ Implementado |
| **JavaScript** | Vanilla JS + jQuery | ✅ Implementado |
| **Drag & Drop** | Dropzone.js | 🆕 Por integrar |
| **Gráficos** | Chart.js | 🆕 Por integrar |
| **Firmas** | Signature Pad | ✅ Implementado |
| **PDFs** | WeasyPrint | ✅ Implementado |
| **Base de Datos** | MySQL 8.0 | ✅ Implementado |

---

## ✅ CHECKLIST DE INICIO

Antes de empezar a desarrollar:

- [ ] Confirmar que NO se usará React
- [ ] Confirmar uso de JavaScript Vanilla + jQuery
- [ ] Confirmar diseño iOS minimalista
- [ ] Instalar Dropzone.js via CDN
- [ ] Instalar Chart.js via CDN
- [ ] Crear carpeta `app/static/js/biomedicos/`
- [ ] Crear carpeta `app/static/css/biomedicos/`
- [ ] Crear carpeta `app/templates/biomedicos/`

---

## 🚀 PRÓXIMO PASO

**Empezar con el submódulo de Hojas de Vida:**

1. Crear estructura de carpetas
2. Crear `ver_hojas_vida.html` con lista iOS
3. Crear `tabla_hojas_vida.js` con AJAX
4. Probar carga de datos desde backend existente

¿Empezamos con esto?
