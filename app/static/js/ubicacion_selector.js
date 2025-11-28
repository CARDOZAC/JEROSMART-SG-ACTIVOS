// =====================================================================
// SELECTOR DE UBICACIÓN CON AUTOCOMPLETADO
// Implementación: Estilo Petr - Componente reutilizable y eficiente
// =====================================================================

/**
 * Lista maestra de ubicaciones de la Clínica Primavera
 * Organizada por áreas para facilitar mantenimiento
 */
const UBICACIONES_CLINICA = [
    'AUDITORIO PISO 1 GESTION AMBIENTAL',
    'Bodega CEDI S1',
    'Central de Esterilización',
    'Clínica de Heridas',
    'Consulta Externa',
    'Farmacia',
    'Gastroenterología',
    'Hemodinamia',
    'Hospitalización 2P VIP',
    'Hospitalización 5A',
    'Hospitalización 5B',
    'Hospitalización 6A',
    'Hospitalización 6B',
    'Imagenología',
    'Isla de Enfermería Urgencias',
    'Laboratorio Primer Piso',
    'Oficina de Sistemas',
    'Oficina de Terapia',
    'Oncología',
    'PAD',
    'PAD 4 PISO ',
    'PAD PISO 4',
    'Pendiente de Asignación',
    'SOTANO 1 ',
    'SOTANO 1 OFICINA ACTIVOS FIJOS',
    'Salas de CX',
    'Sin Ubicación Asignada',
    'Taller Biomédico',
    'UCI',
    'UCI A',
    'UCI B',
    'Unidad de Diagnóstico Cardiovascular y Neumológico',
    'Urgencias Séptimo Piso',
    'Vacunación'
].sort(); // Ordenar alfabéticamente para facilitar búsqueda // Ordenar alfabéticamente para facilitar búsqueda // Ordenar alfabéticamente para facilitar búsqueda

/**
 * Inicializa un selector de ubicación con autocompletado
 * @param {string} selectId - ID del elemento select
 * @param {string} valorActual - Valor preseleccionado (opcional)
 */
function initUbicacionSelector(selectId, valorActual = '') {
    const select = document.getElementById(selectId);
    if (!select) {
        console.error(`Selector de ubicación no encontrado: ${selectId}`);
        return;
    }

    // Limpiar opciones existentes
    select.innerHTML = '';

    // Opción por defecto
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Seleccione una ubicación...';
    select.appendChild(defaultOption);

    // Agregar todas las ubicaciones
    UBICACIONES_CLINICA.forEach(ubicacion => {
        const option = document.createElement('option');
        option.value = ubicacion;
        option.textContent = ubicacion;

        // Preseleccionar si coincide con el valor actual
        if (valorActual && ubicacion.toLowerCase() === valorActual.toLowerCase()) {
            option.selected = true;
        }

        select.appendChild(option);
    });

    // Agregar opción "Otra ubicación" al final
    const otraOption = document.createElement('option');
    otraOption.value = '__otra__';
    otraOption.textContent = '➕ Otra ubicación (escribir)';
    select.appendChild(otraOption);
}

/**
 * Inicializa un selector con búsqueda avanzada usando Select2 (si está disponible)
 * @param {string} selectId - ID del elemento select
 * @param {string} valorActual - Valor preseleccionado (opcional)
 */
function initUbicacionSelectorConBusqueda(selectId, valorActual = '') {
    initUbicacionSelector(selectId, valorActual);

    const select = document.getElementById(selectId);
    if (!select) return;

    // Si Select2 está disponible, úsalo para búsqueda avanzada
    if (typeof $ !== 'undefined' && $.fn.select2) {
        $(select).select2({
            placeholder: 'Seleccione o busque una ubicación...',
            allowClear: true,
            width: '100%',
            language: {
                noResults: function() {
                    return "No se encontró la ubicación";
                },
                searching: function() {
                    return "Buscando...";
                }
            },
            // Permitir crear nueva opción si no existe
            tags: true,
            createTag: function(params) {
                const term = $.trim(params.term);
                if (term === '') {
                    return null;
                }
                return {
                    id: term,
                    text: term,
                    newTag: true
                };
            }
        });
    } else {
        // Fallback: Usar datalist HTML5 para autocompletado nativo
        convertToDatalist(selectId);
    }
}

/**
 * Convierte un select en un input con datalist para autocompletado nativo
 * @param {string} selectId - ID del elemento select
 */
function convertToDatalist(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const valorActual = select.value;
    const parent = select.parentNode;

    // Crear input de texto
    const input = document.createElement('input');
    input.type = 'text';
    input.id = selectId;
    input.name = select.name;
    input.className = select.className;
    input.value = valorActual;
    input.placeholder = 'Escriba para buscar o seleccione...';
    input.setAttribute('list', `${selectId}_datalist`);
    input.setAttribute('autocomplete', 'off');

    // Copiar atributos required si existen
    if (select.hasAttribute('required')) {
        input.setAttribute('required', 'required');
    }

    // Crear datalist
    const datalist = document.createElement('datalist');
    datalist.id = `${selectId}_datalist`;

    UBICACIONES_CLINICA.forEach(ubicacion => {
        const option = document.createElement('option');
        option.value = ubicacion;
        datalist.appendChild(option);
    });

    // Reemplazar select con input + datalist
    parent.replaceChild(input, select);
    parent.appendChild(datalist);
}

/**
 * Obtiene el valor seleccionado de un selector de ubicación
 * @param {string} selectId - ID del elemento
 * @returns {string} Valor seleccionado
 */
function getUbicacionValue(selectId) {
    const element = document.getElementById(selectId);
    if (!element) return '';

    // Si es Select2
    if (typeof $ !== 'undefined' && $.fn.select2 && $(element).data('select2')) {
        return $(element).val() || '';
    }

    // Si es select o input normal
    return element.value || '';
}

/**
 * Establece el valor de un selector de ubicación
 * @param {string} selectId - ID del elemento
 * @param {string} valor - Valor a establecer
 */
function setUbicacionValue(selectId, valor) {
    const element = document.getElementById(selectId);
    if (!element) return;

    // Si es Select2
    if (typeof $ !== 'undefined' && $.fn.select2 && $(element).data('select2')) {
        // Si el valor no existe en las opciones, crearlo
        if (!UBICACIONES_CLINICA.includes(valor) && valor) {
            const newOption = new Option(valor, valor, true, true);
            $(element).append(newOption);
        }
        $(element).val(valor).trigger('change');
    } else {
        // Si es select o input normal
        element.value = valor;
    }
}

// =====================================================================
// EXPORTAR FUNCIONES GLOBALMENTE
// =====================================================================

// Hacer funciones disponibles globalmente
window.UBICACIONES_CLINICA = UBICACIONES_CLINICA;
window.initUbicacionSelector = initUbicacionSelector;
window.initUbicacionSelectorConBusqueda = initUbicacionSelectorConBusqueda;
window.getUbicacionValue = getUbicacionValue;
window.setUbicacionValue = setUbicacionValue;

// Auto-inicializar selectores con clase 'ubicacion-selector'
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.ubicacion-selector').forEach(select => {
        if (select.id) {
            initUbicacionSelectorConBusqueda(select.id, select.value);
        }
    });
});

console.log('✅ Selector de ubicaciones cargado. Total de ubicaciones:', UBICACIONES_CLINICA.length);
