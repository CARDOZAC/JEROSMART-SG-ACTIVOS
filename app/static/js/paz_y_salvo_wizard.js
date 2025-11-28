// ================================================================
// FUNCIONALIDAD PAZ Y SALVO - UX NIVEL DIOS
// Estilo James Gosling: Robusto, intuitivo, con validación exhaustiva
// ================================================================

(function() {
    'use strict';

    // Estado global
    let funcionarioSeleccionado = null;
    let activosAsignados = [];
    let activosAdicionales = [];
    let estadosActivos = {};

    // Referencias a elementos DOM
    const searchInput = document.getElementById('funcionario-paz-salvo-search');
    const searchResults = document.getElementById('funcionario-paz-salvo-results');
    const infoDisplay = document.getElementById('funcionario-info-display');
    const estadosSection = document.getElementById('estados-activos-section');
    const estadosContainer = document.getElementById('activos-estados-container');
    const adicionalesContainer = document.getElementById('activos-adicionales-container');
    const btnAgregarAdicional = document.getElementById('btn-agregar-activo-adicional');

    // Utilidades
    const debounce = (fn, delay = 300) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn(...args), delay);
        };
    };

    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // ================================================================
    // BÚSQUEDA INTELIGENTE DE FUNCIONARIOS
    // ================================================================
    if (searchInput && searchResults) {
        const buscarFuncionarios = debounce(async (term) => {
            if (term.length < 2) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`/funcionarios/api/buscar-con-activos?term=${encodeURIComponent(term)}`);
                const funcionarios = await response.json();

                if (funcionarios.length === 0) {
                    searchResults.innerHTML = `
                        <div class="list-group-item text-muted text-center">
                            <i class="bi bi-search me-2"></i>
                            No se encontraron funcionarios con ese criterio
                        </div>
                    `;
                    searchResults.style.display = 'block';
                    return;
                }

                searchResults.innerHTML = funcionarios.map(func => `
                    <div class="list-group-item list-group-item-action funcionario-resultado"
                         data-funcionario='${JSON.stringify(func)}'>
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1">
                                    <i class="bi bi-person-fill text-primary me-2"></i>
                                    ${escapeHtml(func.nombre_completo)}
                                </h6>
                                <p class="mb-1 small text-muted">
                                    <strong>CC:</strong> ${escapeHtml(func.cedula)} |
                                    <strong>Cargo:</strong> ${escapeHtml(func.cargo)}
                                </p>
                                <p class="mb-0 small text-muted">
                                    <strong>Área:</strong> ${escapeHtml(func.area)}
                                </p>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-success">
                                    ${func.activos_count} activo${func.activos_count !== 1 ? 's' : ''}
                                </span>
                            </div>
                        </div>
                    </div>
                `).join('');

                searchResults.style.display = 'block';

                // Event listeners para selección
                document.querySelectorAll('.funcionario-resultado').forEach(item => {
                    item.addEventListener('click', () => {
                        const func = JSON.parse(item.dataset.funcionario);
                        seleccionarFuncionario(func);
                    });
                });

            } catch (error) {
                console.error('Error buscando funcionarios:', error);
                searchResults.innerHTML = `
                    <div class="list-group-item text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al buscar. Por favor, intenta de nuevo.
                    </div>
                `;
                searchResults.style.display = 'block';
            }
        });

        searchInput.addEventListener('input', (e) => {
            buscarFuncionarios(e.target.value);
        });

        // Cerrar resultados al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }

    // ================================================================
    // SELECCIONAR FUNCIONARIO
    // ================================================================
    function seleccionarFuncionario(func) {
        funcionarioSeleccionado = func;
        activosAsignados = func.activos || [];
        estadosActivos = {};

        // Llenar campos ocultos
        document.getElementById('funcionario_desvinculado_id').value = func.id;
        document.getElementById('nombre_funcionario').value = func.nombre_completo;
        document.getElementById('cargo_funcionario').value = func.cargo;
        document.getElementById('area_funcionario').value = func.area;

        // Actualizar input de búsqueda
        searchInput.value = func.nombre_completo;
        searchResults.style.display = 'none';

        // Mostrar info del funcionario
        document.getElementById('display-nombre').textContent = func.nombre_completo;
        document.getElementById('display-cedula').textContent = func.cedula;
        document.getElementById('display-cargo').textContent = func.cargo;
        document.getElementById('display-area').textContent = func.area;
        document.getElementById('display-activos-count').textContent = `${func.activos_count} activo${func.activos_count !== 1 ? 's' : ''}`;

        infoDisplay.style.display = 'block';

        // Renderizar tabla de activos
        if (func.activos_count > 0) {
            renderizarTablaActivos();
            estadosSection.style.display = 'block';
        } else {
            estadosSection.style.display = 'none';
        }

        actualizarResumen();
    }

    // ================================================================
    // RENDERIZAR TABLA DE ACTIVOS CON ESTADOS
    // ================================================================
    function renderizarTablaActivos() {
        const todosActivos = [...activosAsignados, ...activosAdicionales];

        if (todosActivos.length === 0) {
            estadosContainer.innerHTML = '<p class="text-muted text-center">No hay activos para mostrar.</p>';
            return;
        }

        estadosContainer.innerHTML = `
            <table class="table table-bordered table-hover">
                <thead class="table-light">
                    <tr>
                        <th style="width: 5%;">#</th>
                        <th style="width: 30%;">Descripción</th>
                        <th style="width: 15%;">Placa</th>
                        <th style="width: 12%;">Marca</th>
                        <th style="width: 12%;">Modelo</th>
                        <th style="width: 12%;">Serie</th>
                        <th style="width: 14%;" class="text-center">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    ${todosActivos.map((activo, index) => {
                        const estadoActual = estadosActivos[activo.id] || '';
                        return `
                            <tr class="asset-state-row">
                                <td class="text-center">${index + 1}</td>
                                <td>${escapeHtml(activo.nombre_activo)}</td>
                                <td>${escapeHtml(activo.placa_codigo_interno)}</td>
                                <td>${escapeHtml(activo.marca)}</td>
                                <td>${escapeHtml(activo.modelo)}</td>
                                <td>${escapeHtml(activo.serie)}</td>
                                <td>
                                    <div class="estado-radio-group">
                                        <label class="me-2" title="Bueno">
                                            <input type="radio" name="estado_${activo.id}" value="Bueno"
                                                   ${estadoActual === 'Bueno' ? 'checked' : ''}
                                                   onchange="window.pazYSalvoChangeEstado(${activo.id}, 'Bueno')">
                                            <span class="text-success">✓</span>
                                        </label>
                                        <label class="me-2" title="Regular">
                                            <input type="radio" name="estado_${activo.id}" value="Regular"
                                                   ${estadoActual === 'Regular' ? 'checked' : ''}
                                                   onchange="window.pazYSalvoChangeEstado(${activo.id}, 'Regular')">
                                            <span class="text-warning">~</span>
                                        </label>
                                        <label title="Malo">
                                            <input type="radio" name="estado_${activo.id}" value="Malo"
                                                   ${estadoActual === 'Malo' ? 'checked' : ''}
                                                   onchange="window.pazYSalvoChangeEstado(${activo.id}, 'Malo')">
                                            <span class="text-danger">✗</span>
                                        </label>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    }

    // ================================================================
    // CAMBIAR ESTADO DE ACTIVO
    // ================================================================
    window.pazYSalvoChangeEstado = function(activoId, estado) {
        estadosActivos[activoId] = estado;
        actualizarResumen();
        actualizarCampoOculto();
    };

    // ================================================================
    // AGREGAR ACTIVO ADICIONAL
    // ================================================================
    if (btnAgregarAdicional) {
        btnAgregarAdicional.addEventListener('click', () => {
            mostrarModalActivoAdicional();
        });
    }

    function mostrarModalActivoAdicional() {
        // Reutilizar el modal de búsqueda de activos del paso 2
        const activoSearchInput = document.getElementById('activo-search');
        if (activoSearchInput) {
            // Scroll al paso 2
            alert('Utiliza la búsqueda de activos en el Paso 2 para agregar activos adicionales. Estos activos se marcarán automáticamente como "en custodia" cuando selecciones Paz y Salvo.');
        }
    }

    // ================================================================
    // ACTUALIZAR RESUMEN
    // ================================================================
    function actualizarResumen() {
        const total = Object.keys(estadosActivos).length;
        const buenos = Object.values(estadosActivos).filter(e => e === 'Bueno').length;
        const maloRegular = Object.values(estadosActivos).filter(e => e === 'Malo' || e === 'Regular').length;

        document.getElementById('summary-total-activos').textContent = total;
        document.getElementById('summary-buenos').textContent = buenos;
        document.getElementById('summary-malo-regular').textContent = maloRegular;
    }

    // ================================================================
    // ACTUALIZAR CAMPO OCULTO CON ESTADOS
    // ================================================================
    function actualizarCampoOculto() {
        document.getElementById('estados_activos_data').value = JSON.stringify(estadosActivos);
    }

    // ================================================================
    // INICIALIZACIÓN
    // ================================================================
    console.log('[Paz y Salvo] Módulo cargado correctamente');

})();
