/**
 * Editor de Hojas de Vida Biomédicas
 * Maneja la edición de hojas de vida existentes con wizard de 4 pasos
 */

let pasoActual = 1;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Editor de Hoja de Vida iniciado');

    // Configurar botón de guardar
    const btnGuardar = document.getElementById('btn-guardar-cambios');
    if (btnGuardar) {
        btnGuardar.addEventListener('click', guardarCambios);
    }
});

/**
 * Navegar al siguiente paso del wizard
 */
function siguientePaso(numeroPaso) {
    // Guardar datos del paso actual antes de continuar
    guardarDatosPasoActual();

    // Ocultar paso actual
    document.querySelectorAll('.wizard-step-content').forEach(step => {
        step.classList.remove('active');
    });

    // Mostrar nuevo paso
    const nuevoPaso = document.getElementById(`paso-${numeroPaso}`);
    if (nuevoPaso) {
        nuevoPaso.classList.add('active');
    }

    // Actualizar indicadores visuales
    actualizarIndicadoresPasos(numeroPaso);

    // Si es el paso 4, generar resumen
    if (numeroPaso === 4) {
        generarResumen();
    }

    pasoActual = numeroPaso;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Navegar al paso anterior
 */
function anteriorPaso(numeroPaso) {
    document.querySelectorAll('.wizard-step-content').forEach(step => {
        step.classList.remove('active');
    });

    const nuevoPaso = document.getElementById(`paso-${numeroPaso}`);
    if (nuevoPaso) {
        nuevoPaso.classList.add('active');
    }

    actualizarIndicadoresPasos(numeroPaso);
    pasoActual = numeroPaso;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Actualizar indicadores visuales de los pasos
 */
function actualizarIndicadoresPasos(pasoActivo) {
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        const numeroPaso = index + 1;

        if (numeroPaso < pasoActivo) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (numeroPaso === pasoActivo) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });
}

/**
 * Guardar datos del paso actual en sessionStorage
 */
function guardarDatosPasoActual() {
    if (pasoActual === 1) {
        guardarDatosPaso1();
    } else if (pasoActual === 2) {
        guardarDatosPaso2();
    }
}

/**
 * Recopilar datos del Paso 1
 */
function guardarDatosPaso1() {
    const datos = {
        distribuidor: document.getElementById('distribuidor').value,
        forma_adquisicion: document.getElementById('forma_adquisicion').value,
        telefono: document.getElementById('telefono').value,
        correo_electronico: document.getElementById('correo_electronico').value,
        fecha_ingreso: document.getElementById('fecha_ingreso').value,
        costo: document.getElementById('costo').value,
        n_factura: document.getElementById('n_factura').value,
        n_orden_compra: document.getElementById('n_orden_compra').value,
        fecha_fabricacion: document.getElementById('fecha_fabricacion').value,
        fecha_instalacion: document.getElementById('fecha_instalacion').value,
        vencimiento_garantia: document.getElementById('vencimiento_garantia').value,
        vida_util_anios: document.getElementById('vida_util_anios').value,
        permiso_comercializacion: document.getElementById('permiso_comercializacion').value
    };

    sessionStorage.setItem('edicion_paso1', JSON.stringify(datos));
}

/**
 * Recopilar datos del Paso 2
 */
function guardarDatosPaso2() {
    const datos = {
        voltaje: document.getElementById('voltaje').value,
        frecuencia: document.getElementById('frecuencia').value,
        corriente: document.getElementById('corriente').value,
        potencia: document.getElementById('potencia').value,
        dimensiones: document.getElementById('dimensiones').value,
        peso: document.getElementById('peso').value,
        equipo_fijo_movil: document.getElementById('equipo_fijo_movil').value,
        humedad_relativa: document.getElementById('humedad_relativa').value,
        temperatura_trabajo: document.getElementById('temperatura_trabajo').value,
        clasificacion_riesgo: document.getElementById('clasificacion_riesgo').value,
        clasificacion_biomedica: document.getElementById('clasificacion_biomedica').value,
        manual_usuario: document.getElementById('manual_usuario').checked,
        manual_servicio: document.getElementById('manual_servicio').checked,
        requiere_calibracion: document.getElementById('requiere_calibracion').checked,
        periodicidad_mantenimiento: document.getElementById('periodicidad_mantenimiento').value,
        periodicidad_metrologia: document.getElementById('periodicidad_metrologia').value
    };

    sessionStorage.setItem('edicion_paso2', JSON.stringify(datos));
}

/**
 * Generar resumen de datos antes de guardar
 */
function generarResumen() {
    const paso1 = JSON.parse(sessionStorage.getItem('edicion_paso1') || '{}');
    const paso2 = JSON.parse(sessionStorage.getItem('edicion_paso2') || '{}');

    const resumenHTML = `
        <div class="row g-3">
            <div class="col-12">
                <h6 class="text-primary mb-3">
                    <i class="bi bi-clipboard-data"></i> Datos Generales
                </h6>
            </div>
            <div class="col-md-6">
                <strong>Proveedor:</strong> ${paso1.distribuidor || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Forma de Adquisición:</strong> ${paso1.forma_adquisicion || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Fecha de Ingreso:</strong> ${paso1.fecha_ingreso || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Costo:</strong> ${paso1.costo ? '$' + parseFloat(paso1.costo).toLocaleString('es-CO') : 'N/A'}
            </div>

            <div class="col-12 mt-4">
                <h6 class="text-primary mb-3">
                    <i class="bi bi-gear"></i> Datos Técnicos
                </h6>
            </div>
            <div class="col-md-6">
                <strong>Voltaje:</strong> ${paso2.voltaje || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Frecuencia:</strong> ${paso2.frecuencia || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Clasificación de Riesgo:</strong> ${paso2.clasificacion_riesgo || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Periodicidad de Mantenimiento:</strong> ${paso2.periodicidad_mantenimiento || 'N/A'}
            </div>
            <div class="col-md-4">
                <strong>Manual de Usuario:</strong> ${paso2.manual_usuario ? '✓ Sí' : '✗ No'}
            </div>
            <div class="col-md-4">
                <strong>Manual de Servicio:</strong> ${paso2.manual_servicio ? '✓ Sí' : '✗ No'}
            </div>
            <div class="col-md-4">
                <strong>Requiere Calibración:</strong> ${paso2.requiere_calibracion ? '✓ Sí' : '✗ No'}
            </div>
        </div>
    `;

    document.getElementById('resumen-datos').innerHTML = resumenHTML;
}

/**
 * Guardar todos los cambios (enviar PUT al backend)
 */
async function guardarCambios() {
    const btnGuardar = document.getElementById('btn-guardar-cambios');

    try {
        // Deshabilitar botón y mostrar loading
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        // Recopilar todos los datos
        guardarDatosPasoActual();
        const paso1 = JSON.parse(sessionStorage.getItem('edicion_paso1') || '{}');
        const paso2 = JSON.parse(sessionStorage.getItem('edicion_paso2') || '{}');

        const activo_id = document.getElementById('activo_id').value;

        // Crear FormData para enviar datos y archivos
        const formData = new FormData();

        // Agregar todos los datos de texto
        const todosLosDatos = { ...paso1, ...paso2 };
        for (const [key, value] of Object.entries(todosLosDatos)) {
            if (value !== null && value !== undefined && value !== '') {
                formData.append(key, value);
            }
        }

        // Agregar archivos si fueron seleccionados
        const archivos = [
            'foto_activo',
            'pdf_factura',
            'pdf_invima',
            'pdf_importacion',
            'pdf_manual_usuario',
            'pdf_manual_servicio'
        ];

        archivos.forEach(nombreArchivo => {
            const input = document.getElementById(nombreArchivo);
            if (input && input.files && input.files.length > 0) {
                formData.append(nombreArchivo, input.files[0]);
            }
        });

        // Enviar solicitud PUT al servidor
        const response = await fetch(`/biomedicos/api/hojas-vida/${activo_id}`, {
            method: 'PUT',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // Limpiar sessionStorage
            sessionStorage.removeItem('edicion_paso1');
            sessionStorage.removeItem('edicion_paso2');

            // Mostrar mensaje de éxito
            mostrarMensaje('Hoja de Vida actualizada exitosamente', 'success');

            // Redirigir a la vista de detalle después de 1 segundo
            setTimeout(() => {
                window.location.href = `/biomedicos/hoja-vida/detalle/${activo_id}`;
            }, 1000);
        } else {
            throw new Error(result.message || 'Error al actualizar la Hoja de Vida');
        }

    } catch (error) {
        console.error('Error al guardar cambios:', error);
        mostrarMensaje(error.message || 'Error al guardar los cambios', 'error');

        // Restaurar botón
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = '<i class="bi bi-check-circle"></i> Guardar Cambios';
    }
}

/**
 * Mostrar mensaje de notificación
 */
function mostrarMensaje(mensaje, tipo = 'info') {
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = tipo === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';

    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi ${iconClass}"></i> ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Insertar al inicio del contenido del wizard
    const container = document.querySelector('.wizard-content-container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHTML);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}
