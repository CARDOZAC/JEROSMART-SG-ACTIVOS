/**
 * Gestión de Tabla de Hojas de Vida - Estilo iOS
 * Sistema de Gestión de Activos Fijos - Módulo Biomédico
 */

let paginaActual = 1;
let totalPaginas = 1;
const itemsPorPagina = 20;

/**
 * Carga las hojas de vida desde el backend con filtros
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
            console.log('Datos recibidos:', response);
            renderizarHojasVida(response);
        },
        error: function(xhr, status, error) {
            console.error('Error al cargar hojas de vida:', error);
            mostrarError('No se pudieron cargar las hojas de vida. Por favor, intenta de nuevo.');
            mostrarListaVacia('Error al cargar datos');
        }
    });
}

/**
 * Renderiza la lista de hojas de vida estilo iOS
 */
function renderizarHojasVida(data) {
    const container = document.getElementById('lista-hojas-vida');
    const activos = Array.isArray(data) ? data : (data.hojas_vida || data.activos || []);

    // Actualizar contador
    actualizarContador(activos.length);

    if (activos.length === 0) {
        mostrarListaVacia('No hay equipos biomédicos registrados');
        return;
    }

    let html = '<div class="ios-list-header">Equipos Biomédicos</div>';

    activos.forEach(item => {
        const tieneHojaVida = item.tiene_hoja_vida === 1 || item.tiene_hoja_vida === true;

        const badge = tieneHojaVida
            ? '<span class="badge" style="background: var(--ios-green); color: white; font-size: 11px; padding: 4px 8px; border-radius: 6px;">Completo</span>'
            : '<span class="badge" style="background: var(--ios-orange); color: white; font-size: 11px; padding: 4px 8px; border-radius: 6px;">Pendiente</span>';

        const ubicacion = item.ubicacion || 'Sin ubicación';
        const marca = item.marca ? ` • ${item.marca}` : '';

        html += `
            <div class="ios-list-item" onclick="verDetalleHdV(${item.activo_id || item.id})" style="cursor: pointer;">
                <div class="ios-list-content">
                    <div class="d-flex justify-content-between align-items-start">
                        <div style="flex: 1;">
                            <div class="ios-list-title">${item.nombre_activo}</div>
                            <div class="ios-list-subtitle">
                                ${item.placa_codigo_interno}${marca} • ${ubicacion}
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

    // Renderizar paginación si hay más de una página
    if (data.total && data.total > itemsPorPagina) {
        renderizarPaginacion(data.total, data.pagina_actual || paginaActual);
    }
}

/**
 * Actualiza el contador de resultados
 */
function actualizarContador(total) {
    const contador = document.getElementById('contador-resultados');
    if (total === 0) {
        contador.textContent = 'No se encontraron resultados';
    } else if (total === 1) {
        contador.textContent = '1 equipo encontrado';
    } else {
        contador.textContent = `${total} equipos encontrados`;
    }
}

/**
 * Muestra mensaje cuando no hay datos
 */
function mostrarListaVacia(mensaje) {
    const container = document.getElementById('lista-hojas-vida');
    container.innerHTML = `
        <div class="text-center py-5" style="background: var(--ios-bg-secondary); border-radius: var(--ios-radius-md); padding: 48px 24px;">
            <i class="bi bi-inbox" style="font-size: 64px; color: var(--ios-gray-3);"></i>
            <h4 class="mt-3" style="color: var(--ios-label-secondary); font-weight: 600;">${mensaje}</h4>
            <p class="text-muted" style="font-size: var(--ios-font-size-subhead);">
                Los equipos biomédicos registrados aparecerán aquí
            </p>
            <a href="/activos/add" class="btn mt-3" style="background: var(--ios-blue); color: white; border-radius: var(--ios-radius-sm);">
                <i class="bi bi-plus-circle"></i> Registrar Activo
            </a>
        </div>
    `;
    actualizarContador(0);
}

/**
 * Ver detalle de hoja de vida o crear si no existe
 */
function verDetalleHdV(activoId) {
    // Redirigir a la vista de detalle
    // El backend se encarga de redirigir al wizard si no existe la hoja de vida
    window.location.href = `/biomedicos/hoja-vida/detalle/${activoId}`;
}

/**
 * Obtener filtros del formulario
 */
function obtenerFiltros() {
    return {
        q: document.getElementById('filtro-busqueda').value.trim(),
        ubicacion: document.getElementById('filtro-ubicacion').value,
        estado: document.getElementById('filtro-estado').value
    };
}

/**
 * Limpiar todos los filtros
 */
function limpiarFiltros() {
    document.getElementById('filtro-busqueda').value = '';
    document.getElementById('filtro-ubicacion').value = '';
    document.getElementById('filtro-estado').value = '';
    paginaActual = 1;
    cargarHojasVida();
}

/**
 * Mostrar loading
 */
function mostrarLoading() {
    const container = document.getElementById('lista-hojas-vida');
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border" style="color: var(--ios-blue);" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-3 text-muted" style="font-size: var(--ios-font-size-subhead);">
                Cargando hojas de vida...
            </p>
        </div>
    `;
}

/**
 * Renderizar paginación
 */
function renderizarPaginacion(total, paginaActualNum) {
    totalPaginas = Math.ceil(total / itemsPorPagina);
    paginaActual = paginaActualNum;

    const container = document.getElementById('paginacion');
    const paginacionWrapper = document.getElementById('paginacion-container');

    if (totalPaginas <= 1) {
        paginacionWrapper.style.display = 'none';
        return;
    }

    paginacionWrapper.style.display = 'block';

    let html = '';

    // Botón anterior
    html += `
        <li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;

    // Números de página (máximo 5 páginas visibles)
    const inicio = Math.max(1, paginaActual - 2);
    const fin = Math.min(totalPaginas, paginaActual + 2);

    if (inicio > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(1); return false;">1</a></li>`;
        if (inicio > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }

    for (let i = inicio; i <= fin; i++) {
        html += `
            <li class="page-item ${i === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" onclick="cambiarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }

    if (fin < totalPaginas) {
        if (fin < totalPaginas - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(${totalPaginas}); return false;">${totalPaginas}</a></li>`;
    }

    // Botón siguiente
    html += `
        <li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(${paginaActual + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;

    container.innerHTML = html;
}

/**
 * Cambiar de página
 */
function cambiarPagina(nuevaPagina) {
    if (nuevaPagina < 1 || nuevaPagina > totalPaginas) return;
    paginaActual = nuevaPagina;
    cargarHojasVida();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Mostrar mensaje de error con toast iOS
 */
function mostrarError(mensaje) {
    if (typeof showError === 'function') {
        showError(mensaje);
    } else {
        alert(mensaje);
    }
}

/**
 * Mostrar mensaje de éxito con toast iOS
 */
function mostrarExito(mensaje) {
    if (typeof showSuccess === 'function') {
        showSuccess(mensaje);
    } else {
        alert(mensaje);
    }
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Filtro de búsqueda con debounce
    let timeoutBusqueda;
    document.getElementById('filtro-busqueda').addEventListener('input', function() {
        clearTimeout(timeoutBusqueda);
        timeoutBusqueda = setTimeout(() => {
            paginaActual = 1;
            cargarHojasVida();
        }, 500);
    });

    // Filtros de select en tiempo real
    document.getElementById('filtro-ubicacion').addEventListener('change', function() {
        paginaActual = 1;
        cargarHojasVida();
    });

    document.getElementById('filtro-estado').addEventListener('change', function() {
        paginaActual = 1;
        cargarHojasVida();
    });

    // Tecla Enter en búsqueda
    document.getElementById('filtro-busqueda').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            paginaActual = 1;
            cargarHojasVida();
        }
    });
});
