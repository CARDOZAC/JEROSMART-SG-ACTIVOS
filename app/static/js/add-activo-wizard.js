/**
 * Lógica para el Wizard de Creación/Edición de Activos.
 * Estilo "Petr": Separación de intereses. El HTML es solo estructura, el JS es solo comportamiento.
 */
document.addEventListener('DOMContentLoaded', function() {
    // --- ELEMENTOS DEL DOM ---
    const form = document.getElementById('wizard-form');
    const steps = document.querySelectorAll('.ios-wizard-step');
    const progressSteps = document.querySelectorAll('.ios-progress-step');
    const progressFill = document.getElementById('progress-fill');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const btnSubmit = document.getElementById('btn-submit');
    const funcionarioSearch = document.getElementById('funcionario_search');
    const funcionarioResults = document.getElementById('funcionario_results');
    const funcionarioIdInput = document.getElementById('funcionario_id');
    const selectedBadge = document.getElementById('selected_funcionario');

    // --- DATOS Y ESTADO ---
    let currentStep = 1;
    const totalSteps = 4;
    const modoEdicion = document.body.dataset.modoEdicion === 'true';
    const activoDataEl = document.getElementById('activo-data-json');
    const activoData = activoDataEl ? JSON.parse(activoDataEl.textContent || '{}') : {};
    let searchTimeout;

    // --- FUNCIONES ---

    /**
     * Precarga el formulario con datos existentes en modo edición.
     * Mejorado para ser más robusto y claro.
     */
    function preloadForm() {
        if (!modoEdicion || !activoData || Object.keys(activoData).length === 0) return;

        for (const key in activoData) {
            const input = form.querySelector(`[name="${key}"]`);
            if (!input) continue;

            switch (input.type) {
                case 'file':
                    const filePath = activoData[key];
                    if (filePath) {
                        const fileName = filePath.split(/[\\/]/).pop();
                        const fileInfoDiv = document.createElement('div');
                        fileInfoDiv.innerHTML = `<small style="color: #007AFF; margin-top: 5px;">Archivo actual: <strong>${fileName}</strong>. Subir uno nuevo lo reemplazará.</small>`;
                        input.parentNode.insertBefore(fileInfoDiv, input.nextSibling);
                    }
                    break;
                case 'select-one':
                    input.value = activoData[key];
                    break;
                case 'textarea':
                default:
                    input.value = activoData[key];
                    break;
            }
        }

        if (activoData.funcionario_id && activoData.funcionario_responsable) {
            selectFuncionario(activoData.funcionario_id, activoData.funcionario_responsable);
        }

        btnSubmit.querySelector('#submit-text').textContent = 'Actualizar Activo';
    }

    /**
     * Actualiza la interfaz de usuario del wizard (pasos, progreso, botones).
     */
    function updateUI() {
        steps.forEach((step, index) => step.classList.toggle('active', index === currentStep - 1));

        const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
        progressFill.style.width = `${progress}%`;

        progressSteps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index + 1 < currentStep) step.classList.add('completed');
            else if (index + 1 === currentStep) step.classList.add('active');
        });

        btnPrev.disabled = currentStep === 1;
        btnNext.style.display = currentStep === totalSteps ? 'none' : 'inline-flex';
        btnSubmit.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';

        document.querySelector('.ios-wizard-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /**
     * Valida los campos requeridos en el paso actual.
     * @returns {boolean} - True si el paso es válido, de lo contrario false.
     */
    function validateStep() {
        const currentStepElement = steps[currentStep - 1];
        const requiredInputs = currentStepElement.querySelectorAll('[required]');
        let isValid = true;

        for (const input of requiredInputs) {
            if (!input.value.trim()) {
                input.focus();
                input.style.borderColor = '#FF3B30';
                setTimeout(() => { input.style.borderColor = ''; }, 2000);
                isValid = false;
                break; // Detener en el primer error
            }
        }
        return isValid;
    }

    /**
     * Genera y muestra el resumen de los datos del formulario.
     * CORREGIDO: Obtiene el responsable del badge seleccionado, no de un select inexistente.
     */
    function generateSummary() {
        const summaryContainer = document.getElementById('summary-container');
        const formData = new FormData(form);
        const responsableText = selectedBadge.style.display !== 'none'
            ? selectedBadge.querySelector('.badge-text').textContent
            : 'Sin asignar';

        const sections = [
            {
                title: 'Información Principal',
                fields: [
                    { label: 'Nombre', value: formData.get('nombre_activo') },
                    { label: 'Placa', value: formData.get('placa_codigo_interno') },
                    { label: 'Tipo', value: formData.get('tipo_propiedad') }
                ]
            },
            {
                title: 'Detalles Técnicos',
                fields: [
                    { label: 'Marca', value: formData.get('marca') || 'N/A' },
                    { label: 'Modelo', value: formData.get('modelo') || 'N/A' },
                    { label: 'Serie', value: formData.get('serie') || 'N/A' },
                    { label: 'Valor', value: formData.get('valor_comercial') ? `$ ${parseFloat(formData.get('valor_comercial')).toLocaleString('es-CO')}` : null }
                ]
            },
            {
                title: 'Ubicación y Responsable',
                fields: [
                    { label: 'Ubicación', value: formData.get('ubicacion') || 'N/A' },
                    { label: 'Responsable', value: responsableText }
                ]
            }
        ];

        summaryContainer.innerHTML = sections.map(section => `
            <div class="ios-summary-section">
                <h3 class="ios-summary-title">${section.title}</h3>
                ${section.fields
                    .filter(field => field.value) // Solo mostrar campos con valor
                    .map(field => `
                        <div class="ios-summary-item">
                            <span class="ios-summary-label">${field.label}:</span>
                            <span class="ios-summary-value">${field.value}</span>
                        </div>
                    `).join('')}
            </div>
        `).join('');
    }

    /**
     * Selecciona un funcionario y actualiza la UI.
     * @param {string} id - El ID del funcionario.
     * @param {string} nombre - El nombre completo del funcionario.
     */
    function selectFuncionario(id, nombre) {
        funcionarioIdInput.value = id;
        funcionarioSearch.value = '';
        funcionarioResults.classList.remove('show');
        selectedBadge.querySelector('.badge-text').textContent = nombre;
        selectedBadge.style.display = 'inline-flex';
    }

    // --- MANEJO DE EVENTOS ---

    btnNext.addEventListener('click', () => {
        if (validateStep() && currentStep < totalSteps) {
            currentStep++;
            if (currentStep === totalSteps) generateSummary();
            updateUI();
        }
    });

    btnPrev.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep--;
            updateUI();
        }
    });

    form.addEventListener('submit', (e) => {
        btnSubmit.disabled = true;
        btnSubmit.querySelector('#submit-text').style.display = 'none';
        btnSubmit.querySelector('#submit-spinner').style.display = 'block';
    });

    form.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            if (currentStep < totalSteps) btnNext.click();
        }
    });

    funcionarioSearch.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(searchTimeout);
        if (query.length < 2) {
            funcionarioResults.classList.remove('show');
            return;
        }
        funcionarioResults.innerHTML = '<div class="ios-autocomplete-loading">Buscando...</div>';
        funcionarioResults.classList.add('show');
        searchTimeout = setTimeout(() => {
            fetch(`/activos/api/buscar-funcionarios?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    funcionarioResults.innerHTML = data.length === 0
                        ? '<div class="ios-autocomplete-empty">No se encontraron resultados</div>'
                        : data.map(f => `
                            <div class="ios-autocomplete-item" data-id="${f.id}" data-nombre="${f.nombre_completo}">
                                <div class="autocomplete-name">${f.nombre_completo}</div>
                                <div class="autocomplete-details"><span>CC: ${f.cedula}</span><span>${f.cargo}</span></div>
                            </div>`).join('');
                })
                .catch(error => {
                    console.error('Error en búsqueda de funcionarios:', error);
                    funcionarioResults.innerHTML = '<div class="ios-autocomplete-empty">Error al buscar</div>';
                });
        }, 300);
    });

    funcionarioResults.addEventListener('click', (e) => {
        const item = e.target.closest('.ios-autocomplete-item');
        if (item) selectFuncionario(item.dataset.id, item.dataset.nombre);
    });

    selectedBadge.querySelector('.badge-remove').addEventListener('click', () => {
        funcionarioIdInput.value = '';
        selectedBadge.style.display = 'none';
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.ios-autocomplete-container')) {
            funcionarioResults.classList.remove('show');
        }
    });

    // --- INICIALIZACIÓN ---
    document.body.dataset.modoEdicion = modoEdicion; // Para referencia futura si es necesario
    updateUI();
    preloadForm();
});