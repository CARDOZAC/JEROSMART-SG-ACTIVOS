# GUÍA DE PRUEBA - Wizard de Hojas de Vida Biomédicas
**Fecha**: 2025-11-27
**Módulo**: Gestión Biomédica - Hojas de Vida

---

## 🎯 OBJETIVO

Probar el flujo completo del wizard de creación de hojas de vida para equipos biomédicos.

---

## ✅ MEJORAS IMPLEMENTADAS

### 1. Mapeo Correcto de Campos
Se corrigió el mapeo entre los campos del formulario y el modelo `HojaVidaBiomedico`:

| Campo Formulario | Campo Modelo Backend | Tipo |
|------------------|---------------------|------|
| `fecha_adquisicion` | `fecha_ingreso` | Date |
| `proveedor` | `distribuidor` | String |
| `telefono_proveedor` | `telefono` | String |
| `email_proveedor` | `correo_electronico` | String |
| `costo_adquisicion` | `costo` | Float |
| `vida_util` | `vida_util_anios` | Integer |
| `periodicidad_calibracion` | `periodicidad_metrologia` | String |
| `requiere_calibracion` | `requiere_calibracion` | Boolean |

### 2. Función `guardarHojaVida()` Mejorada
- ✅ Validación de datos antes de enviar
- ✅ Conversión correcta de booleanos
- ✅ Manejo de valores nulos/vacíos
- ✅ Envío de referencias a archivos temporales
- ✅ Logs de debug para desarrollo
- ✅ Mensajes de error/éxito mejorados

### 3. Sistema de Notificaciones
- ✅ ios-toast.js integrado
- ✅ Funciones globales: `showSuccess()`, `showError()`, `showWarning()`, `showInfo()`
- ✅ Diseño iOS nativo

---

## 🚀 PASOS PARA PROBAR EL WIZARD

### PASO 0: Verificar Configuración Inicial

1. **Iniciar servidor Flask**
   ```bash
   cd "c:\Users\david\JEROSMART ACTIVOS"
   venv\Scripts\activate
   python run.py
   ```

2. **Verificar que el servidor está corriendo**
   - Abrir navegador: `http://localhost:5000`
   - Login al sistema

### PASO 1: Acceder al Wizard

1. Navegar a: **Gestión Biomédica → Hojas de Vida**
   - URL: `http://localhost:5000/biomedicos/hojas-vida`

2. Click en botón **"Nueva Hoja de Vida"**
   - Debe redirigir a: `http://localhost:5000/biomedicos/hoja-vida/wizard`

3. **Verificar elementos visuales:**
   - ✅ Barra de progreso con 4 pasos visible
   - ✅ Paso 1 marcado como activo (azul)
   - ✅ Botón "Siguiente" visible
   - ✅ Botón "Anterior" oculto

### PASO 2: Completar Paso 1 - Datos Generales

#### 2.1 Seleccionar Activo Biomédico

1. **Click en el campo "Seleccionar Equipo Biomédico"**
   - Debe mostrar dropdown de Select2

2. **Escribir al menos 2 caracteres** (ej: "BIO" o nombre de placa)
   - Debe aparecer mensaje "Buscando..."
   - Debe cargar resultados vía AJAX desde `/biomedicos/api/hojas-vida?q=BIO&estado=0`

3. **Seleccionar un activo de la lista**
   - Debe mostrar sección "Información del Activo"
   - Debe rellenar: Placa, Marca, Modelo, Serie

**⚠️ IMPORTANTE:** Solo aparecen activos biomédicos SIN hoja de vida (estado=0)

#### 2.2 Completar Datos Generales

| Campo | Valor de Prueba | Requerido |
|-------|-----------------|-----------|
| Fecha de Adquisición | `2024-01-15` | ✅ Sí |
| Forma de Adquisición | `Compra` | ✅ Sí |
| Proveedor | `Medtronic Colombia` | ❌ No |
| Teléfono Proveedor | `3001234567` | ❌ No |
| Email Proveedor | `contacto@medtronic.com` | ❌ No |
| Costo de Adquisición | `15000000` | ❌ No |
| Observaciones Generales | `Equipo nuevo adquirido para UCI` | ❌ No |

#### 2.3 Validaciones Paso 1

**Probar validaciones:**
1. Click "Siguiente" sin seleccionar activo → Debe mostrar error
2. Seleccionar activo pero sin fecha → Debe mostrar error
3. Sin forma de adquisición → Debe mostrar error
4. Con todos los campos requeridos → Debe avanzar a Paso 2

**Comportamiento esperado:**
- ✅ Paso 1 marcado como "completado" (verde con ✓)
- ✅ Paso 2 marcado como "activo" (azul)
- ✅ Botón "Anterior" ahora visible
- ✅ Datos guardados en `sessionStorage`

### PASO 3: Completar Paso 2 - Datos Técnicos

#### 3.1 Completar Datos Técnicos

| Campo | Valor de Prueba | Requerido |
|-------|-----------------|-----------|
| Clasificación Biomédica | `Clase IIA - Riesgo Moderado` | ❌ No |
| Clasificación de Riesgo | `Soporte de Vida` | ❌ No |
| Tecnología Predominante | `Electrónica` | ❌ No |
| Voltaje | `110/220` | ❌ No |
| Corriente | `5` | ❌ No |
| Potencia | `500` | ❌ No |
| Frecuencia de Uso | `Continuo (24/7)` | ❌ No |
| Vida Útil Estimada | `10` | ❌ No |
| Requiere Calibración | `Sí` | ❌ No |
| Periodicidad Calibración | `Anual` | ❌ No |
| Especificaciones Técnicas | `Monitor multiparamétrico de signos vitales con pantalla táctil de 15 pulgadas` | ❌ No |

#### 3.2 Validaciones Paso 2

**Probar navegación:**
1. Click "Anterior" → Debe volver a Paso 1 con datos preservados
2. Click "Siguiente" → Debe avanzar a Paso 3

**Comportamiento esperado:**
- ✅ Paso 2 marcado como "completado" (verde con ✓)
- ✅ Paso 3 marcado como "activo" (azul)
- ✅ Datos guardados en `sessionStorage`

### PASO 4: Completar Paso 3 - Documentos

#### 4.1 Probar Dropzone.js

**Para cada categoría de documentos:**

##### 4.1.1 Calibraciones
1. **Drag & Drop:**
   - Arrastrar archivo PDF sobre zona "Calibraciones"
   - Debe cambiar color de borde a azul
   - Debe subir automáticamente a `/biomedicos/api/hojas-vida/upload-temp`
   - Debe mostrar toast de éxito: "Archivo cargado: [nombre]"

2. **Click para seleccionar:**
   - Click en zona de dropzone
   - Seleccionar archivo PDF
   - Debe subir automáticamente

3. **Validaciones:**
   - Intentar subir archivo que NO sea PDF → Debe rechazar
   - Intentar subir archivo > 10MB → Debe rechazar
   - Subir múltiples archivos → Todos deben aparecer en lista

4. **Eliminar archivo:**
   - Click en botón "Eliminar" de un archivo
   - Debe remover de la lista
   - Debe mostrar toast: "Archivo eliminado: [nombre]"

##### 4.1.2 Mantenimiento Preventivo
- Repetir pruebas de 4.1.1

##### 4.1.3 Mantenimiento Correctivo
- Repetir pruebas de 4.1.1

##### 4.1.4 Documentación Legal
- Repetir pruebas de 4.1.1

#### 4.2 Verificar Almacenamiento Temporal

**Abrir consola del navegador (F12):**
```javascript
// Ver datos guardados
JSON.parse(sessionStorage.getItem('datosWizard'))
```

**Debe mostrar:**
```json
{
  "paso1": { ... },
  "paso2": { ... },
  "paso3": {
    "calibraciones": [
      {
        "nombre_original": "calibracion_2024.pdf",
        "nombre_temporal": "20251127_123456_calibracion_2024.pdf",
        "ruta_temporal": "/uploads/temp/...",
        "tamano": 152432,
        "checksum": "abc123..."
      }
    ],
    "preventivo": [],
    "correctivo": [],
    "legal": []
  }
}
```

#### 4.3 Avanzar a Paso 4

Click "Siguiente" → Debe avanzar a resumen

### PASO 5: Completar Paso 4 - Resumen y Confirmación

#### 5.1 Verificar Resumen

**Sección "Datos Generales":**
- ✅ Debe mostrar activo seleccionado
- ✅ Debe mostrar placa
- ✅ Debe mostrar todos los campos completados en Paso 1
- ✅ Botón "Editar" → Click debe volver a Paso 1

**Sección "Datos Técnicos":**
- ✅ Debe mostrar todos los campos completados en Paso 2
- ✅ Si no hay datos → Debe decir "No se ingresaron datos técnicos"
- ✅ Botón "Editar" → Click debe volver a Paso 2

**Sección "Documentos Adjuntos":**
- ✅ Debe mostrar resumen: "Calibraciones: 2 archivo(s)"
- ✅ Si no hay documentos → Debe decir "No se cargaron documentos"
- ✅ Botón "Editar" → Click debe volver a Paso 3

#### 5.2 Confirmar Datos

1. **Intentar guardar sin marcar checkbox**
   - Click "Crear Hoja de Vida"
   - Debe mostrar error: "Debe confirmar que los datos son correctos"

2. **Marcar checkbox de confirmación**
   - ✅ "Confirmo que toda la información es correcta"

3. **Click "Crear Hoja de Vida"**

**Comportamiento esperado:**
- ✅ Botón cambia a "Guardando..." con spinner
- ✅ Botón deshabilitado durante envío
- ✅ Console muestra logs de datos enviados
- ✅ Request POST a `/biomedicos/api/hojas-vida`

#### 5.3 Verificar Respuesta del Servidor

**Escenario 1: Éxito**
- ✅ Toast verde: "✅ Hoja de vida creada exitosamente"
- ✅ Espera 1.5 segundos
- ✅ Redirige a `/biomedicos/hojas-vida`
- ✅ `sessionStorage` limpio

**Escenario 2: Error**
- ❌ Toast rojo: "❌ [mensaje de error]"
- ✅ Botón vuelve a estado normal
- ✅ Usuario puede corregir y reintentar

---

## 🔍 VERIFICACIÓN EN BACKEND

### 1. Verificar en Base de Datos

```sql
-- Ver última hoja de vida creada
SELECT * FROM hojas_vida_biomedicos
ORDER BY id DESC LIMIT 1;

-- Ver documentos adjuntos
SELECT * FROM documentos_adjuntos_biomedicos
WHERE hoja_vida_id = (SELECT MAX(id) FROM hojas_vida_biomedicos);
```

### 2. Verificar Archivos Físicos

```bash
# Listar archivos temporales
dir "c:\Users\david\JEROSMART ACTIVOS\uploads\temp"

# Listar archivos de hojas de vida
dir "c:\Users\david\JEROSMART ACTIVOS\uploads\hojas_de_vida"
```

### 3. Probar Generación de PDF

1. Desde la lista de hojas de vida, click en un equipo
2. Debe haber botón "Generar PDF" o "Ver Hoja de Vida"
3. Click → Debe generar PDF consolidado

---

## 🐛 PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: Select2 no carga opciones
**Síntoma:** Al escribir en el campo, no aparecen resultados

**Solución:**
1. Verificar que jQuery está cargado ANTES de Select2
2. Verificar en consola si hay error 404 en `/biomedicos/api/hojas-vida`
3. Verificar que hay activos biomédicos sin hoja de vida en la BD

**Query para verificar:**
```sql
SELECT a.id, a.nombre_activo, a.placa_codigo_interno
FROM activos a
LEFT JOIN hojas_vida_biomedicos h ON a.id = h.activo_id
WHERE a.clase_id = 1 AND h.id IS NULL;
```

### Problema 2: Dropzone no funciona
**Síntoma:** No se puede arrastrar archivos

**Solución:**
1. Verificar que Dropzone.js está cargado
2. Verificar en consola: `typeof Dropzone` → Debe ser "function"
3. Verificar endpoint: `/biomedicos/api/hojas-vida/upload-temp` existe

### Problema 3: Error al guardar
**Síntoma:** "Error 500" al crear hoja de vida

**Solución:**
1. Ver logs del servidor Flask
2. Verificar que carpeta `uploads/temp` existe
3. Verificar permisos de escritura
4. Verificar que `activo_id` existe y no tiene ya una hoja de vida

### Problema 4: Datos no se preservan al navegar
**Síntoma:** Al volver a paso anterior, campos vacíos

**Solución:**
1. Abrir F12 → Application → Session Storage
2. Verificar que existe clave `datosWizard`
3. Si no existe, revisar función `guardarDatosPaso()`

---

## ✅ CHECKLIST DE PRUEBAS

### Funcionalidad Básica
- [ ] Wizard se abre correctamente
- [ ] Barra de progreso funciona
- [ ] Select2 carga activos dinámicamente
- [ ] Navegación entre pasos funciona
- [ ] Datos se preservan al navegar
- [ ] Validaciones de campos requeridos funcionan
- [ ] Dropzone permite subir PDFs
- [ ] Resumen muestra todos los datos
- [ ] Confirmación final guarda correctamente
- [ ] Redirección después de guardar funciona

### Integración Backend
- [ ] Endpoint POST `/api/hojas-vida` recibe datos
- [ ] Hoja de vida se crea en BD
- [ ] Documentos se asocian correctamente
- [ ] Archivos se mueven de `/temp` a `/hojas_de_vida`
- [ ] PDF consolidado se genera correctamente

### Experiencia de Usuario (UX)
- [ ] Diseño iOS se ve correctamente
- [ ] Animaciones funcionan suavemente
- [ ] Mensajes de error son claros
- [ ] Toast notifications se ven bien
- [ ] Loading states son visibles
- [ ] Mobile responsive funciona

---

## 📊 CASOS DE PRUEBA ESPECÍFICOS

### Caso 1: Flujo Completo Exitoso
1. Seleccionar activo
2. Llenar todos los campos obligatorios
3. Agregar 2 archivos de calibración
4. Agregar 1 archivo legal
5. Confirmar y guardar
6. **Resultado esperado:** Hoja de vida creada, archivos asociados, redirección exitosa

### Caso 2: Validación de Campos Requeridos
1. No seleccionar activo
2. Click "Siguiente"
3. **Resultado esperado:** Error: "Debe seleccionar un activo"

### Caso 3: Navegación con Preservación
1. Completar Paso 1
2. Completar Paso 2
3. Volver a Paso 1
4. **Resultado esperado:** Datos del Paso 1 aún visibles

### Caso 4: Cancelación de Wizard
1. Completar Paso 1
2. Click "Cancelar" en header
3. **Resultado esperado:** Redirección a lista, datos en sessionStorage permanecen

### Caso 5: Archivo Inválido
1. Intentar subir archivo .docx en Dropzone
2. **Resultado esperado:** Error: "Solo se permiten archivos PDF"

---

## 🎯 MÉTRICAS DE ÉXITO

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Tiempo de creación | < 3 min | Cronometrar desde apertura hasta guardado |
| Tasa de error | < 5% | Intentos fallidos / Intentos totales |
| Satisfacción UX | > 4/5 | Encuesta post-uso |
| Preservación de datos | 100% | Datos guardados al navegar / Total |

---

## 📝 NOTAS FINALES

- **Dropzone.js** y **Select2** se cargan desde CDN
- Los archivos temporales se guardan en `/uploads/temp`
- La hoja de vida se asocia al activo mediante `activo_id` (unique)
- El wizard usa `sessionStorage` para persistencia temporal
- Los datos se limpian al finalizar exitosamente

---

**Última actualización:** 2025-11-27
**Próximo paso:** Probar wizard en entorno de desarrollo
