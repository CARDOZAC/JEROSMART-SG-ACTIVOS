document.addEventListener('DOMContentLoaded', function () {
    const hojasVidaTableBody = document.querySelector('#hojas-vida-table tbody');
    const loadingSpinner = document.getElementById('loading-spinner');
    const searchInput = document.getElementById('search-input');

    let allHojasVida = [];

    /**
     * Muestra u oculta el spinner de carga.
     * @param {boolean} show - True para mostrar, false para ocultar.
     */
    const toggleLoading = (show) => {
        if (loadingSpinner) {
            loadingSpinner.style.display = show ? 'flex' : 'none';
        }
    };

    /**
     * Renderiza las filas de la tabla con los datos filtrados.
     * @param {Array} data - Array de objetos de hojas de vida.
     */
    const renderTable = (data) => {
        if (!hojasVidaTableBody) return;
        hojasVidaTableBody.innerHTML = '';

        if (!data || data.length === 0) {
            hojasVidaTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted py-5">
                        No se encontraron equipos biomédicos.
                    </td> 
                </tr>
            `;
            return;
        }

        data.forEach(item => {
            const tieneHojaVida = item.tiene_hoja_vida === 1;
            const row = document.createElement('tr');
            row.className = 'fade-in-item';

            const statusBadge = tieneHojaVida
                ? `<span class="badge badge-ios bg-success-soft">Completa</span>`
                : `<span class="badge badge-ios bg-warning-soft">Pendiente</span>`;

            const actionsHtml = tieneHojaVida 
                ? `
                    <a href="/biomedicos/hoja-vida/crear-wizard/${item.activo_id}" class="btn btn-sm btn-outline-primary me-1" title="Editar Hoja de Vida">
                        <i class="bi bi-pencil-fill"></i>
                    </a>
                    <a href="/biomedicos/api/hojas-vida/pdf/${item.activo_id}" target="_blank" class="btn btn-sm btn-outline-info me-1" title="Ver PDF">
                        <i class="bi bi-file-earmark-pdf-fill"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger btn-delete" data-activo-id="${item.activo_id}" title="Eliminar Hoja de Vida">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                `
                : `
                    <a href="/biomedicos/hoja-vida/crear-wizard/${item.activo_id}" class="btn btn-sm btn-success ios-button">
                        <i class="bi bi-plus-circle-fill me-1"></i> Crear Hoja de Vida
                    </a>
                `;

            row.innerHTML = `
                <td>${item.nombre_activo}</td>
                <td>${item.placa_codigo_interno}</td>
                <td>${statusBadge}</td>
                <td>${actionsHtml}</td>
            `;
            hojasVidaTableBody.appendChild(row);
        });
    };

    /**
     * Obtiene los datos de las hojas de vida desde la API.
     */
    const fetchHojasVida = async () => {
        toggleLoading(true);
        try {
            const response = await fetch('/biomedicos/api/hojas-vida');
            if (!response.ok) {
                throw new Error(`Error en la red: ${response.statusText}`);
            }
            allHojasVida = await response.json();
            renderTable(allHojasVida);
        } catch (error) {
            console.error('Error al obtener las hojas de vida:', error);
            showToast(error.message || 'Error al cargar los datos.', 'error');
            if (hojasVidaTableBody) {
                hojasVidaTableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-danger py-5">
                            Error al cargar los datos. Por favor, intente de nuevo más tarde.
                        </td>
                    </tr>
                `;
            }
        } finally {
            toggleLoading(false);
        }
    };

    /**
     * Maneja la eliminación de una hoja de vida.
     * @param {number} activoId - El ID del activo cuya hoja de vida se eliminará.
     */
    const handleDelete = async (activoId) => {
        const confirmed = await showConfirmationModal({
            title: 'Confirmar Eliminación',
            message: '¿Estás seguro de que quieres eliminar esta Hoja de Vida? Esta acción no se puede deshacer y eliminará todos los registros asociados.',
            confirmText: 'Sí, Eliminar',
            isDestructive: true
        });

        if (!confirmed) {
            return;
        }

        toggleLoading(true);
        try {
            const response = await fetch(`/biomedicos/api/hojas-vida/${activoId}`, {
                method: 'DELETE',
            });
            const result = await response.json();
            if (response.ok && result.success) {
                showToast(result.message || 'Hoja de Vida eliminada con éxito', 'success');
                fetchHojasVida(); // Recargar la tabla
            } else {
                throw new Error(result.message || 'Error al eliminar la hoja de vida.');
            }
        } catch (error) {
            console.error('Error al eliminar:', error);
            showToast(error.message, 'error');
        } finally {
            toggleLoading(false);
        }
    };

    // Carga inicial de datos
    fetchHojasVida();

    // Event listener para la búsqueda
    searchInput?.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredData = allHojasVida.filter(item =>
            item.nombre_activo.toLowerCase().includes(searchTerm) ||
            item.placa_codigo_interno.toLowerCase().includes(searchTerm)
        );
        renderTable(filteredData);
    });

    // Event listener para los botones de eliminar (delegación de eventos)
    hojasVidaTableBody?.addEventListener('click', (e) => {
        const deleteButton = e.target.closest('.btn-delete');
        if (deleteButton) {
            const activoId = deleteButton.dataset.activoId;
            handleDelete(activoId);
        }
    });
});