/**
 * Wizard de Creación de Hoja de Vida - Estilo iOS
 * Sistema de Gestión de Activos Fijos - Módulo Biomédico
 */

// Estado del wizard
let pasoActual = 1;
const totalPasos = 4;
let activoSeleccionado = null;

// Almacenamiento temporal de datos
const datosWizard = {
    paso1: {},
    paso2: {},
    paso3: {
        calibraciones: [],
        preventivo: [],
        correctivo: [],
        legal: []
    },
    paso4: {}
};

/**
 * Inicialización del wizard
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar Select2 con búsqueda AJAX
    inicializarSelect2Activos();

    // Restaurar datos desde sessionStorage si existen
    restaurarDatosWizard();
});

/**
 * Inicializar Select2 con búsqueda dinámica AJAX
 */
function inicializarSelect2Activos() {
    $('#activo_id').select2({
        theme: 'default',
        placeholder: '🔍 Buscar por placa o nombre del activo...',
        allowClear: true,
        language: {
            noResults: function() {
                return 'No se encontraron resultados';
            },
            searching: function() {
                return 'Buscando...';
            },
            inputTooShort: function() {
                return 'Escriba al menos 2 caracteres para buscar';
            }
        },
        minimumInputLength: 2,
        ajax: {
            url: '/biomedicos/api/hojas-vida',
            dataType: 'json',
            delay: 300,
            data: function(params) {
                return {
                    q: params.term, // término de búsqueda
                    estado: '0' // Solo activos sin hoja de vida
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(activo) {
                        return {
                            id: activo.activo_id || activo.id,
                            text: activo.placa_codigo_interno + ' - ' + activo.nombre_activo,
                            activo: activo // Guardar datos completos
                        };
                    })
                };
            },
            cache: true
        }
    });

    // Event listener para cuando se selecciona un activo
    $('#activo_id').on('select2:select', function(e) {
        const data = e.params.data;
        if (data && data.activo) {
            activoSeleccionado = data.activo;
            mostrarInfoActivo(activoSeleccionado);
        }
    });

    // Event listener para cuando se limpia la selección
    $('#activo_id').on('select2:clear', function() {
        ocultarInfoActivo();
        activoSeleccionado = null;
    });
}


/**
 * Mostrar información del activo seleccionado
 */
function mostrarInfoActivo(activo) {
    document.getElementById('info-activo-seleccionado').style.display = 'block';
    document.getElementById('info-placa').textContent = activo.placa_codigo_interno || '-';
    document.getElementById('info-marca').textContent = activo.marca || '-';
    document.getElementById('info-modelo').textContent = activo.modelo || '-';
    document.getElementById('info-serie').textContent = activo.numero_serie || '-';
}

/**
 * Ocultar información del activo
 */
function ocultarInfoActivo() {
    document.getElementById('info-activo-seleccionado').style.display = 'none';
    activoSeleccionado = null;
}

/**
 * Navegar al siguiente paso
 */
function siguientePaso() {
    // Validar paso actual
    if (!validarPaso(pasoActual)) {
        return;
    }

    // Guardar datos del paso actual
    guardarDatosPaso(pasoActual);

    if (pasoActual < totalPasos) {
        pasoActual++;
        actualizarUI();

        // Si es el paso 4, generar resumen
        if (pasoActual === 4) {
            generarResumen();
        }

        // Scroll al inicio
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Navegar al paso anterior
 */
function anteriorPaso() {
    if (pasoActual > 1) {
        pasoActual--;
        actualizarUI();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Ir a un paso específico (desde los botones de editar)
 */
function irAPaso(numeroPaso) {
    if (numeroPaso >= 1 && numeroPaso <= totalPasos) {
        pasoActual = numeroPaso;
        actualizarUI();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Actualizar UI del wizard
 */
function actualizarUI() {
    // Actualizar indicadores de pasos
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        const stepNumber = index + 1;
        step.classList.remove('active', 'completed');

        if (stepNumber < pasoActual) {
            step.classList.add('completed');
        } else if (stepNumber === pasoActual) {
            step.classList.add('active');
        }
    });

    // Actualizar contenido visible
    document.querySelectorAll('.wizard-step-content').forEach((content, index) => {
        content.classList.remove('active');
        if (index + 1 === pasoActual) {
            content.classList.add('active');
        }
    });

    // Actualizar botones de navegación
    const btnAnterior = document.getElementById('btn-anterior');
    const btnSiguiente = document.getElementById('btn-siguiente');
    const btnGuardar = document.getElementById('btn-guardar');

    if (pasoActual === 1) {
        btnAnterior.style.display = 'none';
    } else {
        btnAnterior.style.display = 'inline-block';
    }

    if (pasoActual === totalPasos) {
        btnSiguiente.style.display = 'none';
        btnGuardar.style.display = 'inline-block';
    } else {
        btnSiguiente.style.display = 'inline-block';
        btnGuardar.style.display = 'none';
    }
}

/**
 * Validar datos del paso actual
 */
function validarPaso(paso) {
    switch (paso) {
        case 1:
            return validarPaso1();
        case 2:
            return validarPaso2();
        case 3:
            return validarPaso3();
        case 4:
            return validarPaso4();
        default:
            return true;
    }
}

/**
 * Validar Paso 1
 */
function validarPaso1() {
    const activoId = document.getElementById('activo_id').value;
    const fechaAdquisicion = document.getElementById('fecha_adquisicion').value;
    const formaAdquisicion = document.getElementById('forma_adquisicion').value;

    if (!activoId) {
        showError('Debe seleccionar un activo');
        return false;
    }

    if (!fechaAdquisicion) {
        showError('Debe ingresar la fecha de adquisición');
        return false;
    }

    if (!formaAdquisicion) {
        showError('Debe seleccionar la forma de adquisición');
        return false;
    }

    return true;
}

/**
 * Validar Paso 2
 */
function validarPaso2() {
    // Paso 2 es opcional, pero se puede agregar validación si es necesario
    return true;
}

/**
 * Validar Paso 3
 */
function validarPaso3() {
    // Paso 3 es opcional (documentos)
    return true;
}

/**
 * Validar Paso 4
 */
function validarPaso4() {
    const confirmar = document.getElementById('confirmar_datos').checked;

    if (!confirmar) {
        showError('Debe confirmar que los datos son correctos');
        return false;
    }

    return true;
}

/**
 * Guardar datos del paso actual en el objeto datosWizard
 */
function guardarDatosPaso(paso) {
    switch (paso) {
        case 1:
            guardarDatosPaso1();
            break;
        case 2:
            guardarDatosPaso2();
            break;
        case 3:
            // Los archivos se guardan en upload_documentos.js
            break;
        case 4:
            // Paso de resumen, no hay datos que guardar
            break;
    }

    // Guardar en sessionStorage
    sessionStorage.setItem('datosWizard', JSON.stringify(datosWizard));
}

/**
 * Guardar datos del paso 1
 * Mapeo a campos del modelo HojaVidaBiomedico
 */
function guardarDatosPaso1() {
    datosWizard.paso1 = {
        // ID del activo
        activo_id: document.getElementById('activo_id').value,

        // Mapeo de campos: formulario → modelo backend
        fecha_ingreso: document.getElementById('fecha_adquisicion').value,  // fecha_adquisicion → fecha_ingreso
        forma_adquisicion: document.getElementById('forma_adquisicion').value,
        distribuidor: document.getElementById('proveedor').value,  // proveedor → distribuidor
        telefono: document.getElementById('telefono_proveedor').value,  // telefono_proveedor → telefono
        correo_electronico: document.getElementById('email_proveedor').value,  // email_proveedor → correo_electronico
        costo: document.getElementById('costo_adquisicion').value,  // costo_adquisicion → costo
        observaciones_generales: document.getElementById('observaciones_generales').value  // Campo adicional (no en modelo)
    };
}

/**
 * Guardar datos del paso 2
 * Mapeo a campos del modelo HojaVidaBiomedico
 */
function guardarDatosPaso2() {
    datosWizard.paso2 = {
        // Campos que coinciden directamente
        clasificacion_biomedica: document.getElementById('clasificacion_biomedica').value,
        clasificacion_riesgo: document.getElementById('clasificacion_riesgo').value,
        voltaje: document.getElementById('voltaje').value,
        corriente: document.getElementById('corriente').value,
        potencia: document.getElementById('potencia').value,

        // Mapeo de campos: formulario → modelo backend
        vida_util_anios: document.getElementById('vida_util').value,  // vida_util → vida_util_anios
        requiere_calibracion: document.getElementById('requiere_calibracion').value === '1',  // Convertir a boolean
        periodicidad_metrologia: document.getElementById('periodicidad_calibracion').value,  // periodicidad_calibracion → periodicidad_metrologia

        // Campos adicionales del formulario (no en modelo, pero útiles para validación)
        tecnologia_predominante: document.getElementById('tecnologia_predominante').value,  // No en modelo
        frecuencia_uso: document.getElementById('frecuencia_uso').value,  // No en modelo
        especificaciones_tecnicas: document.getElementById('especificaciones_tecnicas').value  // No en modelo
    };
}

/**
 * Restaurar datos del wizard desde sessionStorage
 */
function restaurarDatosWizard() {
    const datosGuardados = sessionStorage.getItem('datosWizard');
    if (datosGuardados) {
        const datos = JSON.parse(datosGuardados);

        // Restaurar paso 1
        if (datos.paso1) {
            Object.keys(datos.paso1).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = datos.paso1[key];
                }
            });
        }

        // Restaurar paso 2
        if (datos.paso2) {
            Object.keys(datos.paso2).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = datos.paso2[key];
                }
            });
        }
    }
}

/**
 * Generar resumen en el paso 4
 */
function generarResumen() {
    // Resumen Datos Generales
    let htmlGenerales = '';
    if (activoSeleccionado) {
        htmlGenerales += `<div class="resumen-item">
            <span class="resumen-item-label">Activo:</span>
            <span class="resumen-item-value">${activoSeleccionado.nombre_activo}</span>
        </div>`;
        htmlGenerales += `<div class="resumen-item">
            <span class="resumen-item-label">Placa:</span>
            <span class="resumen-item-value">${activoSeleccionado.placa_codigo_interno}</span>
        </div>`;
    }

    if (datosWizard.paso1) {
        Object.keys(datosWizard.paso1).forEach(key => {
            const value = datosWizard.paso1[key];
            if (value && key !== 'activo_id') {
                const label = formatearLabel(key);
                htmlGenerales += `<div class="resumen-item">
                    <span class="resumen-item-label">${label}:</span>
                    <span class="resumen-item-value">${value}</span>
                </div>`;
            }
        });
    }
    document.getElementById('resumen-generales').innerHTML = htmlGenerales;

    // Resumen Datos Técnicos
    let htmlTecnicos = '';
    if (datosWizard.paso2) {
        Object.keys(datosWizard.paso2).forEach(key => {
            const value = datosWizard.paso2[key];
            if (value) {
                const label = formatearLabel(key);
                htmlTecnicos += `<div class="resumen-item">
                    <span class="resumen-item-label">${label}:</span>
                    <span class="resumen-item-value">${value}</span>
                </div>`;
            }
        });
    }

    if (htmlTecnicos === '') {
        htmlTecnicos = '<p class="text-muted mb-0">No se ingresaron datos técnicos</p>';
    }
    document.getElementById('resumen-tecnicos').innerHTML = htmlTecnicos;

    // Resumen Documentos
    let htmlDocumentos = '';
    const totalArchivos =
        datosWizard.paso3.calibraciones.length +
        datosWizard.paso3.preventivo.length +
        datosWizard.paso3.correctivo.length +
        datosWizard.paso3.legal.length;

    if (totalArchivos > 0) {
        if (datosWizard.paso3.calibraciones.length > 0) {
            htmlDocumentos += `<div class="resumen-item">
                <span class="resumen-item-label">Calibraciones:</span>
                <span class="resumen-item-value">${datosWizard.paso3.calibraciones.length} archivo(s)</span>
            </div>`;
        }
        if (datosWizard.paso3.preventivo.length > 0) {
            htmlDocumentos += `<div class="resumen-item">
                <span class="resumen-item-label">Mantenimiento Preventivo:</span>
                <span class="resumen-item-value">${datosWizard.paso3.preventivo.length} archivo(s)</span>
            </div>`;
        }
        if (datosWizard.paso3.correctivo.length > 0) {
            htmlDocumentos += `<div class="resumen-item">
                <span class="resumen-item-label">Mantenimiento Correctivo:</span>
                <span class="resumen-item-value">${datosWizard.paso3.correctivo.length} archivo(s)</span>
            </div>`;
        }
        if (datosWizard.paso3.legal.length > 0) {
            htmlDocumentos += `<div class="resumen-item">
                <span class="resumen-item-label">Documentación Legal:</span>
                <span class="resumen-item-value">${datosWizard.paso3.legal.length} archivo(s)</span>
            </div>`;
        }
    } else {
        htmlDocumentos = '<p class="text-muted mb-0">No se cargaron documentos</p>';
    }

    document.getElementById('resumen-documentos').innerHTML = htmlDocumentos;
}

/**
 * Formatear etiquetas de campos
 */
function formatearLabel(key) {
    const labels = {
        // Paso 1 - Datos Generales
        'activo_id': 'Activo',
        'fecha_ingreso': 'Fecha de Adquisición',
        'forma_adquisicion': 'Forma de Adquisición',
        'distribuidor': 'Proveedor',
        'telefono': 'Teléfono Proveedor',
        'correo_electronico': 'Email Proveedor',
        'costo': 'Costo de Adquisición',
        'observaciones_generales': 'Observaciones',

        // Paso 2 - Datos Técnicos
        'clasificacion_biomedica': 'Clasificación Biomédica',
        'clasificacion_riesgo': 'Clasificación de Riesgo',
        'tecnologia_predominante': 'Tecnología Predominante',
        'voltaje': 'Voltaje',
        'corriente': 'Corriente',
        'potencia': 'Potencia',
        'frecuencia_uso': 'Frecuencia de Uso',
        'vida_util_anios': 'Vida Útil',
        'requiere_calibracion': 'Requiere Calibración',
        'periodicidad_metrologia': 'Periodicidad Calibración',
        'especificaciones_tecnicas': 'Especificaciones Técnicas'
    };

    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Guardar hoja de vida completa
 * Envía datos al endpoint POST /biomedicos/api/hojas-vida
 */
async function guardarHojaVida() {
    // Validar paso 4
    if (!validarPaso4()) {
        return;
    }

    // Mostrar loading
    const btnGuardar = document.getElementById('btn-guardar');
    const textoOriginal = btnGuardar.innerHTML;
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';

    try {
        // Preparar FormData para enviar
        const formData = new FormData();

        // PASO 1: Agregar datos generales (con mapeo correcto)
        if (datosWizard.paso1) {
            Object.keys(datosWizard.paso1).forEach(key => {
                const value = datosWizard.paso1[key];
                if (value !== null && value !== undefined && value !== '') {
                    formData.append(key, value);
                }
            });
        }

        // PASO 2: Agregar datos técnicos (con mapeo correcto)
        if (datosWizard.paso2) {
            Object.keys(datosWizard.paso2).forEach(key => {
                const value = datosWizard.paso2[key];
                if (value !== null && value !== undefined && value !== '') {
                    // Convertir booleanos a string para FormData
                    if (typeof value === 'boolean') {
                        formData.append(key, value ? 'true' : 'false');
                    } else {
                        formData.append(key, value);
                    }
                }
            });
        }

        // PASO 3: Agregar información de archivos temporales
        // Los archivos ya están en el servidor temporal
        // Solo enviamos las referencias
        if (datosWizard.paso3) {
            Object.keys(datosWizard.paso3).forEach(categoria => {
                const archivos = datosWizard.paso3[categoria];
                if (archivos && archivos.length > 0) {
                    // Enviar como JSON string para que el backend procese
                    formData.append(`archivos_${categoria}`, JSON.stringify(archivos));
                }
            });
        }

        console.log('Enviando datos al servidor...');
        // Debug: mostrar datos que se envían
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
        }

        // Enviar al backend
        const response = await fetch('/biomedicos/api/hojas-vida', {
            method: 'POST',
            body: formData
        });

        const responseData = await response.json();

        if (response.ok && responseData.success) {
            showSuccess('✅ Hoja de vida creada exitosamente');

            // Limpiar sessionStorage
            sessionStorage.removeItem('datosWizard');

            // Redirigir a la lista después de 1.5 segundos
            setTimeout(() => {
                window.location.href = '/biomedicos/hojas-vida';
            }, 1500);
        } else {
            // Error del servidor
            const mensaje = responseData.message || 'Error al guardar la hoja de vida';
            showError('❌ ' + mensaje);
            console.error('Error del servidor:', responseData);
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    } catch (error) {
        console.error('Error al guardar:', error);
        showError('❌ Error de conexión al guardar la hoja de vida');
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = textoOriginal;
    }
}
