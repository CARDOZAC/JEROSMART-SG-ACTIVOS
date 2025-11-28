/**
 * Wizard de Mantenimiento Biomédico
 * Maneja el flujo completo de creación de mantenimientos con 6 pasos
 */

let pasoActual = 1;
let tipoMantenimientoSeleccionado = null;
let accesorios = [];
let signaturePadTecnico = null;
let signaturePadResponsable = null;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Wizard de Mantenimiento iniciado');

    // Inicializar Select2 para búsqueda de activos
    $('#activo_id').select2({
        placeholder: '-- Buscar por placa o nombre del equipo --',
        ajax: {
            url: '/biomedicos/api/activos-biomedicos',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term
                };
            },
            processResults: function (data) {
                return {
                    results: data.map(activo => ({
                        id: activo.id,
                        text: `${activo.placa_codigo_interno} - ${activo.nombre_activo}`,
                        data: activo
                    }))
                };
            },
            cache: true
        },
        minimumInputLength: 2,
        language: {
            inputTooShort: function() {
                return 'Escriba al menos 2 caracteres para buscar';
            },
            searching: function() {
                return 'Buscando...';
            },
            noResults: function() {
                return 'No se encontraron resultados';
            }
        }
    });

    // Evento cuando se selecciona un activo
    $('#activo_id').on('select2:select', function(e) {
        const activo = e.params.data.data;
        mostrarInfoActivo(activo);
        document.getElementById('btn-paso1-siguiente').disabled = false;
    });

    // Configurar botón de guardar
    document.getElementById('btn-guardar-mantenimiento').addEventListener('click', guardarMantenimiento);

    // Establecer fecha actual por defecto
    document.getElementById('fecha_mantenimiento').valueAsDate = new Date();

    // Cargar datos en modo edición
    if (window.MODO_EDICION && window.MANTENIMIENTO_DATA) {
        cargarDatosEdicion();
    }
});

/**
 * Mostrar información del activo seleccionado
 */
function mostrarInfoActivo(activo) {
    document.getElementById('info-placa').textContent = activo.placa_codigo_interno || 'N/A';
    document.getElementById('info-marca').textContent = activo.marca || 'N/A';
    document.getElementById('info-modelo').textContent = activo.modelo || 'N/A';
    document.getElementById('info-serie').textContent = activo.serie || 'N/A';
    document.getElementById('info-ubicacion').textContent = activo.ubicacion || 'N/A';

    document.getElementById('info-activo-seleccionado').style.display = 'block';
}

/**
 * Navegar al siguiente paso
 */
function siguientePaso(numeroPaso) {
    // Validar paso actual antes de avanzar
    if (!validarPasoActual()) {
        return;
    }

    // Guardar datos del paso actual
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

    // Lógica específica por paso
    if (numeroPaso === 5) {
        cargarFormularioDinamico();
    } else if (numeroPaso === 6) {
        inicializarCanvasFirmas();
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
 * Seleccionar tipo de mantenimiento
 */
function seleccionarTipo(tipo) {
    tipoMantenimientoSeleccionado = tipo;

    // Remover selección anterior
    document.querySelectorAll('.tipo-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Marcar la seleccionada
    document.getElementById(`card-${tipo}`).classList.add('selected');
    document.getElementById('tipo_mantenimiento').value = tipo;
    document.getElementById('btn-paso2-siguiente').disabled = false;

    // Guardar en sessionStorage
    sessionStorage.setItem('tipo_mantenimiento', tipo);
}

/**
 * Agregar accesorio a la tabla
 */
function agregarAccesorio() {
    const nombre = document.getElementById('accesorio_nombre').value.trim();
    const cantidad = document.getElementById('accesorio_cantidad').value || 1;
    const referencia = document.getElementById('accesorio_referencia').value.trim();

    if (!nombre) {
        mostrarMensaje('Debe ingresar el nombre del accesorio', 'warning');
        return;
    }

    const accesorio = {
        id: Date.now(),
        nombre: nombre,
        cantidad: parseInt(cantidad),
        referencia: referencia
    };

    accesorios.push(accesorio);
    renderizarTablaAccesorios();

    // Limpiar formulario
    document.getElementById('accesorio_nombre').value = '';
    document.getElementById('accesorio_cantidad').value = '1';
    document.getElementById('accesorio_referencia').value = '';

    // Guardar en sessionStorage
    sessionStorage.setItem('accesorios', JSON.stringify(accesorios));
}

/**
 * Eliminar accesorio de la tabla
 */
function eliminarAccesorio(id) {
    accesorios = accesorios.filter(acc => acc.id !== id);
    renderizarTablaAccesorios();
    sessionStorage.setItem('accesorios', JSON.stringify(accesorios));
}

/**
 * Renderizar tabla de accesorios
 */
function renderizarTablaAccesorios() {
    const tbody = document.getElementById('tbody-accesorios');

    if (accesorios.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    <i class="bi bi-inbox"></i> No se han agregado accesorios
                </td>
            </tr>
        `;
        return;
    }

    const html = accesorios.map(acc => `
        <tr>
            <td>${acc.nombre}</td>
            <td>${acc.cantidad}</td>
            <td>${acc.referencia || '-'}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="eliminarAccesorio(${acc.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = html;
}

/**
 * Cargar formulario dinámico según tipo de mantenimiento
 */
function cargarFormularioDinamico() {
    const tipo = tipoMantenimientoSeleccionado;
    const container = document.getElementById('formulario-dinamico');

    let formularioHTML = '';

    if (tipo === 'preventivo') {
        formularioHTML = `
            <h6 class="mb-3 text-primary">
                <i class="bi bi-calendar-check"></i> Mantenimiento Preventivo
            </h6>
            <div class="row g-3">
                <div class="col-md-12">
                    <label class="form-label">Actividades Realizadas</label>
                    <textarea class="form-control" id="actividades_realizadas" rows="4" placeholder="Descripción de las actividades realizadas..."></textarea>
                </div>
                <div class="col-md-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="limpieza_general">
                        <label class="form-check-label" for="limpieza_general">
                            Limpieza general del equipo
                        </label>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="revision_electrica">
                        <label class="form-check-label" for="revision_electrica">
                            Revisión eléctrica
                        </label>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="lubricacion">
                        <label class="form-check-label" for="lubricacion">
                            Lubricación de partes móviles
                        </label>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="pruebas_funcionamiento">
                        <label class="form-check-label" for="pruebas_funcionamiento">
                            Pruebas de funcionamiento
                        </label>
                    </div>
                </div>
            </div>
        `;
    } else if (tipo === 'correctivo') {
        formularioHTML = `
            <h6 class="mb-3 text-danger">
                <i class="bi bi-exclamation-triangle"></i> Mantenimiento Correctivo
            </h6>
            <div class="row g-3">
                <div class="col-md-12">
                    <label class="form-label">Descripción de la Falla</label>
                    <textarea class="form-control" id="descripcion_falla" rows="3" placeholder="Describa la falla presentada..."></textarea>
                </div>
                <div class="col-md-12">
                    <label class="form-label">Causa de la Falla</label>
                    <textarea class="form-control" id="causa_falla" rows="2" placeholder="Causa identificada..."></textarea>
                </div>
                <div class="col-md-12">
                    <label class="form-label">Solución Aplicada</label>
                    <textarea class="form-control" id="solucion_aplicada" rows="3" placeholder="Descripción de la reparación realizada..."></textarea>
                </div>
                <div class="col-md-12">
                    <label class="form-label">Recomendaciones</label>
                    <textarea class="form-control" id="recomendaciones" rows="2" placeholder="Recomendaciones para prevenir la falla..."></textarea>
                </div>
            </div>
        `;
    } else if (tipo === 'calibracion') {
        formularioHTML = `
            <h6 class="mb-3 text-primary">
                <i class="bi bi-speedometer2"></i> Calibración
            </h6>
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Parámetro Calibrado</label>
                    <input type="text" class="form-control" id="parametro_calibrado" placeholder="Ej: Presión, Temperatura">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Patrón de Referencia</label>
                    <input type="text" class="form-control" id="patron_referencia" placeholder="Patrón utilizado">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Valor Medido Antes</label>
                    <input type="text" class="form-control" id="valor_antes" placeholder="Valor inicial">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Valor Medido Después</label>
                    <input type="text" class="form-control" id="valor_despues" placeholder="Valor después de calibración">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Incertidumbre</label>
                    <input type="text" class="form-control" id="incertidumbre" placeholder="±">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Equipo Cumple</label>
                    <select class="form-select" id="equipo_cumple">
                        <option value="">Seleccione...</option>
                        <option value="Si">Sí</option>
                        <option value="No">No</option>
                    </select>
                </div>
            </div>
        `;
    }

    container.innerHTML = formularioHTML;

    // Cargar datos de edición si existen
    if (window.MODO_EDICION && window.REPORTE_TECNICO_EDICION) {
        setTimeout(() => {
            cargarDatosReporteTecnico(window.REPORTE_TECNICO_EDICION);
        }, 100); // Timeout para asegurar que el DOM se haya renderizado
    }
}

/**
 * Inicializar canvas de firmas
 */
function inicializarCanvasFirmas() {
    if (signaturePadTecnico === null) {
        const canvasTecnico = document.getElementById('canvas-tecnico');
        signaturePadTecnico = new SignaturePad(canvasTecnico, {
            backgroundColor: 'rgb(255, 255, 255)',
            penColor: 'rgb(0, 0, 0)'
        });

        const canvasResponsable = document.getElementById('canvas-responsable');
        signaturePadResponsable = new SignaturePad(canvasResponsable, {
            backgroundColor: 'rgb(255, 255, 255)',
            penColor: 'rgb(0, 0, 0)'
        });
    }
}

/**
 * Limpiar firma
 */
function limpiarFirma(tipo) {
    if (tipo === 'tecnico' && signaturePadTecnico) {
        signaturePadTecnico.clear();
    } else if (tipo === 'responsable' && signaturePadResponsable) {
        signaturePadResponsable.clear();
    }
}

/**
 * Validar paso actual antes de avanzar
 */
function validarPasoActual() {
    switch (pasoActual) {
        case 1:
            const activoId = document.getElementById('activo_id').value;
            if (!activoId) {
                mostrarMensaje('Debe seleccionar un equipo biomédico', 'error');
                return false;
            }
            return true;

        case 2:
            if (!tipoMantenimientoSeleccionado) {
                mostrarMensaje('Debe seleccionar el tipo de mantenimiento', 'error');
                return false;
            }
            return true;

        case 3:
            const fechaMantenimiento = document.getElementById('fecha_mantenimiento').value;
            const tecnicoResponsable = document.getElementById('tecnico_responsable').value;
            const estado = document.getElementById('estado').value;

            if (!fechaMantenimiento) {
                mostrarMensaje('Debe ingresar la fecha de mantenimiento', 'error');
                return false;
            }
            if (!tecnicoResponsable) {
                mostrarMensaje('Debe ingresar el técnico responsable', 'error');
                return false;
            }
            if (!estado) {
                mostrarMensaje('Debe seleccionar el estado del mantenimiento', 'error');
                return false;
            }
            return true;

        case 4:
        case 5:
            return true;

        case 6:
            if (signaturePadTecnico && signaturePadTecnico.isEmpty()) {
                mostrarMensaje('Debe firmar como técnico responsable', 'error');
                return false;
            }
            if (signaturePadResponsable && signaturePadResponsable.isEmpty()) {
                mostrarMensaje('Debe obtener la firma del responsable del área', 'error');
                return false;
            }
            return true;

        default:
            return true;
    }
}

/**
 * Guardar datos del paso actual en sessionStorage
 */
function guardarDatosPasoActual() {
    // Implementar según necesidad
}

/**
 * Guardar mantenimiento completo
 */
async function guardarMantenimiento() {
    const btnGuardar = document.getElementById('btn-guardar-mantenimiento');

    try {
        // Deshabilitar botón y mostrar loading
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        // Preparar FormData
        const formData = new FormData();

        // Si es modo edición, agregar el ID del mantenimiento
        if (window.MODO_EDICION && window.MANTENIMIENTO_DATA) {
            formData.append('mantenimiento_id', window.MANTENIMIENTO_DATA.id);
        }

        // Datos básicos
        formData.append('activo_id', document.getElementById('activo_id').value);
        formData.append('tipo_id', obtenerTipoId(tipoMantenimientoSeleccionado));
        formData.append('fecha_mantenimiento', document.getElementById('fecha_mantenimiento').value);
        formData.append('duracion_minutos', document.getElementById('duracion_minutos').value || '');
        formData.append('observaciones', document.getElementById('observaciones').value || '');
        formData.append('estado', document.getElementById('estado').value);

        // Datos del reporte técnico (según tipo)
        const reporteTecnico = obtenerDatosReporteTecnico();
        formData.append('atributos_reporte_json', JSON.stringify(reporteTecnico));

        // Accesorios
        formData.append('accesorios', JSON.stringify(accesorios));

        // Firmas (convertir a base64)
        if (signaturePadTecnico && !signaturePadTecnico.isEmpty()) {
            formData.append('firma_tecnico', signaturePadTecnico.toDataURL());
        }
        if (signaturePadResponsable && !signaturePadResponsable.isEmpty()) {
            formData.append('firma_responsable', signaturePadResponsable.toDataURL());
        }

        // Enviar al servidor
        const response = await fetch('/biomedicos/api/mantenimientos', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            const mensaje = window.MODO_EDICION
                ? 'Mantenimiento actualizado exitosamente'
                : 'Mantenimiento creado exitosamente';
            mostrarMensaje(mensaje, 'success');

            // Limpiar sessionStorage
            sessionStorage.removeItem('tipo_mantenimiento');
            sessionStorage.removeItem('accesorios');

            // Redirigir después de 1 segundo
            setTimeout(() => {
                if (window.MODO_EDICION && result.mantenimiento_id) {
                    // En modo edición, redirigir al detalle del mantenimiento
                    window.location.href = `/biomedicos/mantenimiento/detalle/${result.mantenimiento_id}`;
                } else {
                    // En modo creación, redirigir a la lista
                    window.location.href = '/biomedicos/mantenimientos';
                }
            }, 1000);
        } else {
            const errorMsg = window.MODO_EDICION
                ? 'Error al actualizar el mantenimiento'
                : 'Error al crear el mantenimiento';
            throw new Error(result.message || errorMsg);
        }

    } catch (error) {
        console.error('Error al guardar mantenimiento:', error);
        mostrarMensaje(error.message || 'Error al guardar el mantenimiento', 'error');

        // Restaurar botón
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = '<i class="bi bi-check-circle"></i> Guardar Mantenimiento';
    }
}

/**
 * Obtener ID del tipo de mantenimiento
 */
function obtenerTipoId(tipo) {
    // Mapeo de tipos a IDs (ajustar según tu base de datos)
    const mapaTipos = {
        'preventivo': 1,
        'correctivo': 2,
        'calibracion': 3
    };
    return mapaTipos[tipo] || 1;
}

/**
 * Obtener datos del reporte técnico
 */
function obtenerDatosReporteTecnico() {
    const tipo = tipoMantenimientoSeleccionado;
    const datos = {};

    if (tipo === 'preventivo') {
        datos.actividades_realizadas = document.getElementById('actividades_realizadas')?.value || '';
        datos.limpieza_general = document.getElementById('limpieza_general')?.checked || false;
        datos.revision_electrica = document.getElementById('revision_electrica')?.checked || false;
        datos.lubricacion = document.getElementById('lubricacion')?.checked || false;
        datos.pruebas_funcionamiento = document.getElementById('pruebas_funcionamiento')?.checked || false;
    } else if (tipo === 'correctivo') {
        datos.descripcion_falla = document.getElementById('descripcion_falla')?.value || '';
        datos.causa_falla = document.getElementById('causa_falla')?.value || '';
        datos.solucion_aplicada = document.getElementById('solucion_aplicada')?.value || '';
        datos.recomendaciones = document.getElementById('recomendaciones')?.value || '';
    } else if (tipo === 'calibracion') {
        datos.parametro_calibrado = document.getElementById('parametro_calibrado')?.value || '';
        datos.patron_referencia = document.getElementById('patron_referencia')?.value || '';
        datos.valor_antes = document.getElementById('valor_antes')?.value || '';
        datos.valor_despues = document.getElementById('valor_despues')?.value || '';
        datos.incertidumbre = document.getElementById('incertidumbre')?.value || '';
        datos.equipo_cumple = document.getElementById('equipo_cumple')?.value || '';
    }

    return datos;
}

/**
 * Mostrar mensaje de notificación
 */
function mostrarMensaje(mensaje, tipo = 'info') {
    const alertClass = tipo === 'success' ? 'alert-success' : tipo === 'error' ? 'alert-danger' : 'alert-warning';
    const iconClass = tipo === 'success' ? 'bi-check-circle' : tipo === 'error' ? 'bi-exclamation-circle' : 'bi-info-circle';

    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi ${iconClass}"></i> ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const container = document.querySelector('.wizard-content-container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHTML);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Cargar datos en modo edición
 * Precarga todos los campos del wizard con los datos existentes del mantenimiento
 */
function cargarDatosEdicion() {
    console.log('Cargando datos de edición...');
    const data = window.MANTENIMIENTO_DATA;

    // PASO 1: Seleccionar activo
    // Crear una opción en Select2 con los datos del activo
    const activoOption = new Option(
        `${data.activo_placa} - ${data.activo_nombre}`,
        data.activo_id,
        true,
        true
    );
    $('#activo_id').append(activoOption).trigger('change');

    // Mostrar info del activo
    mostrarInfoActivo({
        placa_codigo_interno: data.activo_placa,
        nombre_activo: data.activo_nombre,
        marca: '',
        modelo: '',
        serie: '',
        ubicacion: ''
    });

    // Habilitar botón siguiente
    document.getElementById('btn-paso1-siguiente').disabled = false;

    // PASO 2: Tipo de mantenimiento
    tipoMantenimientoSeleccionado = data.tipo_nombre;

    // PASO 3: Datos del mantenimiento
    if (data.fecha_mantenimiento) {
        document.getElementById('fecha_mantenimiento').value = data.fecha_mantenimiento;
    }
    if (data.duracion_minutos) {
        document.getElementById('duracion_minutos').value = data.duracion_minutos;
    }
    if (data.estado) {
        document.getElementById('estado').value = data.estado;
    }
    if (data.observaciones) {
        document.getElementById('observaciones').value = data.observaciones;
    }

    // PASO 4: Accesorios (si existen en el reporte técnico)
    if (data.reporte_tecnico && data.reporte_tecnico.accesorios) {
        const accesoriosData = typeof data.reporte_tecnico.accesorios === 'string'
            ? JSON.parse(data.reporte_tecnico.accesorios)
            : data.reporte_tecnico.accesorios;

        accesorios = accesoriosData.map(acc => ({
            nombre: acc.nombre || '',
            cantidad: acc.cantidad || 1,
            referencia: acc.referencia || ''
        }));
    }

    // PASO 5: Reporte técnico dinámico
    // Se cargará cuando se renderice el formulario dinámico

    // Guardar reporte técnico completo para cargarlo después
    window.REPORTE_TECNICO_EDICION = data.reporte_tecnico || {};

    console.log('Datos de edición cargados correctamente');
    console.log('Tipo:', tipoMantenimientoSeleccionado);
    console.log('Accesorios:', accesorios);
    console.log('Reporte técnico:', window.REPORTE_TECNICO_EDICION);
}

/**
 * Cargar datos del reporte técnico en el formulario dinámico
 */
function cargarDatosReporteTecnico(reporte) {
    console.log('Cargando datos del reporte técnico en el formulario...', reporte);

    // Campos comunes
    if (reporte.tecnico_responsable) {
        const campo = document.getElementById('tecnico_responsable');
        if (campo) campo.value = reporte.tecnico_responsable;
    }

    // Mantenimiento Preventivo
    if (tipoMantenimientoSeleccionado === 'preventivo') {
        if (reporte.actividades_realizadas) {
            const campo = document.getElementById('actividades_realizadas');
            if (campo) campo.value = reporte.actividades_realizadas;
        }
        if (reporte.limpieza_general) {
            const campo = document.getElementById('limpieza_general');
            if (campo) campo.checked = true;
        }
        if (reporte.revision_electrica) {
            const campo = document.getElementById('revision_electrica');
            if (campo) campo.checked = true;
        }
        if (reporte.lubricacion) {
            const campo = document.getElementById('lubricacion');
            if (campo) campo.checked = true;
        }
        if (reporte.pruebas_funcionamiento) {
            const campo = document.getElementById('pruebas_funcionamiento');
            if (campo) campo.checked = true;
        }
    }

    // Mantenimiento Correctivo
    if (tipoMantenimientoSeleccionado === 'correctivo') {
        if (reporte.descripcion_falla) {
            const campo = document.getElementById('descripcion_falla');
            if (campo) campo.value = reporte.descripcion_falla;
        }
        if (reporte.causa_falla) {
            const campo = document.getElementById('causa_falla');
            if (campo) campo.value = reporte.causa_falla;
        }
        if (reporte.solucion_aplicada) {
            const campo = document.getElementById('solucion_aplicada');
            if (campo) campo.value = reporte.solucion_aplicada;
        }
        if (reporte.recomendaciones) {
            const campo = document.getElementById('recomendaciones');
            if (campo) campo.value = reporte.recomendaciones;
        }
    }

    // Calibración
    if (tipoMantenimientoSeleccionado === 'calibracion') {
        if (reporte.parametro_calibrado) {
            const campo = document.getElementById('parametro_calibrado');
            if (campo) campo.value = reporte.parametro_calibrado;
        }
        if (reporte.patron_utilizado || reporte.patron_referencia) {
            const campo = document.getElementById('patron_referencia');
            if (campo) campo.value = reporte.patron_utilizado || reporte.patron_referencia;
        }
        if (reporte.valor_antes) {
            const campo = document.getElementById('valor_antes');
            if (campo) campo.value = reporte.valor_antes;
        }
        if (reporte.valor_despues) {
            const campo = document.getElementById('valor_despues');
            if (campo) campo.value = reporte.valor_despues;
        }
        if (reporte.incertidumbre) {
            const campo = document.getElementById('incertidumbre');
            if (campo) campo.value = reporte.incertidumbre;
        }
        if (reporte.equipo_cumple) {
            const campo = document.getElementById('equipo_cumple');
            if (campo) campo.value = reporte.equipo_cumple;
        }
    }

    console.log('Datos del reporte técnico cargados en el formulario');
}
