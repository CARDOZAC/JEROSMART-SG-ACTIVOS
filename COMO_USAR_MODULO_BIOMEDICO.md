# 📘 Cómo Usar el Módulo Biomédico - Hojas de Vida

## 🎯 Rutas Principales

### 1. **Página Principal del Módulo Biomédico**
```
URL: http://10.10.204.154:5000/biomedicos/
```
Esta es la página de inicio que muestra 3 tarjetas:
- **Hojas de Vida** → Te lleva a la tabla de hojas de vida
- **Mantenimientos** → Gestión de mantenimientos
- **Reportes** → Generación de reportes

**Cómo llegar:**
- Haz clic en el menú principal → **Más** → **Biomédicos**

---

### 2. **Tabla de Hojas de Vida** ✅ NUEVO
```
URL: http://10.10.204.154:5000/biomedicos/hojas-vida
```
Esta es la vista principal de gestión de hojas de vida que incluye:
- ✅ Tabla con lista de equipos biomédicos
- ✅ Filtros (búsqueda, ubicación, estado)
- ✅ Badges de estado (Completo/Pendiente)
- ✅ Botón "Nueva Hoja de Vida" (abre el wizard)
- ✅ Paginación

**Cómo llegar:**
1. Menú → **Más** → **Biomédicos**
2. Clic en la tarjeta **"Hojas de Vida"**

---

### 3. **Wizard de Creación de Hoja de Vida** ✅ NUEVO
```
URL: http://10.10.204.154:5000/biomedicos/hoja-vida/wizard
```
Este es el wizard de 4 pasos para crear una hoja de vida digital:

**Paso 1: Datos Generales**
- Selector de activo biomédico (solo muestra activos sin hoja de vida)
- Información del activo (placa, marca, modelo, serie)
- Fecha y forma de adquisición
- Datos del proveedor
- Costo de adquisición

**Paso 2: Datos Técnicos**
- Clasificación biomédica (Clase I, IIA, IIB, III)
- Clasificación de riesgo
- Tecnología predominante
- Datos eléctricos (voltaje, corriente, potencia)
- Frecuencia de uso y vida útil
- Calibración

**Paso 3: Documentos** (Drag & Drop con Dropzone.js)
- Calibraciones
- Mantenimiento Preventivo
- Mantenimiento Correctivo
- Documentación Legal
- **Solo archivos PDF permitidos**

**Paso 4: Resumen**
- Vista previa de todos los datos
- Botones para editar cada sección
- Confirmación final

**Cómo llegar:**
1. Ir a **Hojas de Vida** (ruta #2)
2. Clic en botón **"Nueva Hoja de Vida"** (esquina superior derecha)

---

## 🔌 Endpoints API (Para desarrolladores)

### GET - Listar Hojas de Vida (con filtros)
```
GET http://10.10.204.154:5000/biomedicos/api/hojas-vida
```

**Parámetros opcionales:**
- `q` - Búsqueda por nombre o placa
- `ubicacion` - Filtrar por ubicación
- `estado` - Filtrar por estado (0=sin hoja de vida, 1=con hoja de vida)
- `pagina` - Número de página
- `por_pagina` - Items por página

**Ejemplo:**
```bash
# Ver todos los activos sin hoja de vida
curl "http://10.10.204.154:5000/biomedicos/api/hojas-vida?estado=0"

# Buscar por placa o nombre
curl "http://10.10.204.154:5000/biomedicos/api/hojas-vida?q=monitor"

# Filtrar por ubicación
curl "http://10.10.204.154:5000/biomedicos/api/hojas-vida?ubicacion=UCI"
```

---

### POST - Crear Hoja de Vida
```
POST http://10.10.204.154:5000/biomedicos/api/hojas-vida
```

**Body (multipart/form-data):**
- `activo_id` (requerido)
- `fecha_adquisicion` (requerido)
- `forma_adquisicion` (requerido)
- `proveedor`
- `telefono_proveedor`
- `email_proveedor`
- `costo_adquisicion`
- `clasificacion_biomedica`
- `clasificacion_riesgo`
- ... (todos los campos del wizard)

---

### POST - Subir Archivo Temporal
```
POST http://10.10.204.154:5000/biomedicos/api/hojas-vida/upload-temp
```

**Body (multipart/form-data):**
- `file` (archivo PDF)
- `categoria` (calibraciones|preventivo|correctivo|legal)

**Respuesta exitosa:**
```json
{
  "success": true,
  "filename": "20250126_143022_certificado.pdf",
  "filepath": "c:/uploads/temp/20250126_143022_certificado.pdf",
  "checksum": "a3b2c1d4e5f6...",
  "message": "Archivo cargado exitosamente"
}
```

---

## 🧪 Testing Rápido

### 1. Verificar que el módulo está funcionando:
```bash
curl http://10.10.204.154:5000/biomedicos/
```
Deberías ver HTML con "Módulo de Gestión Biomédica"

### 2. Verificar la tabla de hojas de vida:
```bash
curl http://10.10.204.154:5000/biomedicos/hojas-vida
```
Deberías ver HTML con filtros y lista iOS

### 3. Verificar el API de activos:
```bash
curl http://10.10.204.154:5000/biomedicos/api/hojas-vida?estado=0
```
Deberías ver JSON con lista de activos sin hoja de vida

### 4. Verificar el wizard:
```bash
curl http://10.10.204.154:5000/biomedicos/hoja-vida/wizard
```
Deberías ver HTML con "Paso 1: Datos Generales"

---

## 📁 Archivos Creados

### Templates HTML:
1. `app/templates/biomedicos/base_biomedico.html` - Template base
2. `app/templates/biomedicos/hojas_vida/ver_hojas_vida.html` - Tabla principal
3. `app/templates/biomedicos/hojas_vida/wizard_hoja_vida.html` - Wizard completo

### JavaScript:
1. `app/static/js/biomedicos/hojas_vida/tabla_hojas_vida.js` - Gestión de tabla
2. `app/static/js/biomedicos/hojas_vida/wizard_hoja_vida.js` - Lógica del wizard
3. `app/static/js/biomedicos/hojas_vida/upload_documentos.js` - Dropzone.js

### CSS:
1. `app/static/css/biomedicos/hojas-vida.css` - Estilos iOS

### Backend:
1. `app/biomedicos/routes.py` - Agregados endpoints:
   - `GET /biomedicos/hojas-vida`
   - `GET /biomedicos/hoja-vida/wizard`
   - `POST /biomedicos/api/hojas-vida/upload-temp`

---

## ⚠️ Importante

### ❌ NO uses estas URLs directamente:
- `/biomedicos/api/hojas-vida` → Esto es un endpoint API que devuelve JSON, no HTML
- `/biomedicos/api/hojas-vida/upload-temp` → Endpoint para subir archivos, no para navegación

### ✅ SÍ usa estas URLs para navegar:
- `/biomedicos/` → Página principal del módulo
- `/biomedicos/hojas-vida` → Tabla de hojas de vida
- `/biomedicos/hoja-vida/wizard` → Wizard de creación

---

## 🎨 Características del Diseño iOS

- **Glassmorphism effects** en cards y modales
- **SF Pro Display font** (via Poppins)
- **Smooth transitions** (0.3s cubic-bezier)
- **Sistema de colores iOS:**
  - Azul: `--ios-blue` (#007AFF)
  - Verde: `--ios-green` (#34C759)
  - Naranja: `--ios-orange` (#FF9500)
  - Rojo: `--ios-red` (#FF3B30)
  - Púrpura: `--ios-purple` (#AF52DE)
- **Border radius consistente:** 8px, 12px, 16px
- **Separators:** 0.5px solid
- **Espaciado:** 8px, 12px, 16px, 24px

---

## 🐛 Troubleshooting

### Problema: "No se cargan los activos en el selector"
**Solución:** Verifica que existan activos biomédicos sin hoja de vida:
```bash
curl "http://10.10.204.154:5000/biomedicos/api/hojas-vida?estado=0"
```

### Problema: "No se suben los archivos PDF"
**Solución:** Verifica que la carpeta `uploads/temp` exista y tenga permisos de escritura

### Problema: "No veo el botón Nueva Hoja de Vida"
**Solución:** Asegúrate de estar en la ruta correcta:
- ❌ `/biomedicos/api/hojas-vida` (API endpoint - JSON)
- ✅ `/biomedicos/hojas-vida` (Vista HTML)

---

## 📞 Soporte

Si tienes problemas, verifica:
1. ✅ Servidor Flask corriendo en puerto 5000
2. ✅ Blueprint `biomedicos_bp` registrado en `app/__init__.py`
3. ✅ Archivos JavaScript y CSS cargando sin errores (F12 en navegador)
4. ✅ Base de datos con activos biomédicos (clase_id = 1)
