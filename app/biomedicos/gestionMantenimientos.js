document.addEventListener('DOMContentLoaded', function () {
    const mantenimientosTableBody = document.querySelector('#mantenimientos-table tbody');
    const loadingSpinner = document.getElementById('mantenimientos-loading-spinner');
    const searchInput = document.getElementById('mantenimientos-search-input');
    const editModalElement = document.getElementById('editMantenimientoModal');
    const editModal = new bootstrap.Modal(editModalElement);
    const editForm = document.getElementById('editMantenimientoForm');
    const modalTitle = document.getElementById('editMantenimientoModalLabel');

    let allMantenimientos = [];
    let mantenimientoTipos = [];

    const toggleLoading = (show) => {
        if (loadingSpinner) {
            loadingSpinner.style.display = show ? 'flex' : 'none';
        }
    };

    const fetchMantenimientoTipos = async () => {
        try {
            const response = await fetch('/biomedicos/api/mantenimiento-tipos');
            if (!response.ok) throw new Error('No se pudieron cargar los tipos de mantenimiento.');
            mantenimientoTipos = await response.json();
            populateTipoSelect(document.getElementById('edit-tipo-id'));
        } catch (error) {
            console.error(error);
            showToast(error.message, 'error');
        }
    };

    const populateTipoSelect = (selectElement, selectedId) => {
        if (!selectElement) return;
        selectElement.innerHTML = '<option value="">Seleccione un tipo...</option>';
        mantenimientoTipos.forEach(tipo => {
            const option = document.createElement('option');
            option.value = tipo.id;
            option.textContent = tipo.nombre;
            if (tipo.id === selectedId) {
                option.selected = true;
            }
            selectElement.appendChild(option);
        });
    };

    const renderTable = (data) => {
        if (!mantenimientosTableBody) return;
        mantenimientosTableBody.innerHTML = '';

        if (!data || data.length === 0) {
            mantenimientosTableBody.innerHTML = `
                <tr><td colspan="5" class="text-center text-muted py-5">No se encontraron mantenimientos.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'fade-in-item';

            const estadoBadge = {
                'Completado': 'bg-success-soft',
                'Pendiente': 'bg-warning-soft',
                'En Proceso': 'bg-info-soft',
            };
            const badgeClass = estadoBadge[item.estado] || 'bg-secondary-soft';

            row.innerHTML = `
                <td>${item.nombre_activo}<br><small class="text-muted">${item.placa_codigo_interno}</small></td>
                <td>${item.tipo_reporte}</td>
                <td>${new Date(item.fecha_mantenimiento + 'T00:00:00').toLocaleDateString()}</td>
                <td><span class="badge badge-ios ${badgeClass}">${item.estado}</span></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary btn-edit" data-id="${item.id}" title="Editar Mantenimiento">
                        <i class="bi bi-pencil-fill"></i> Editar
                    </button>
                </td>
            `;
            mantenimientosTableBody.appendChild(row);
        });
    };

    const fetchMantenimientos = async () => {
        toggleLoading(true);
        try {
            const response = await fetch('/biomedicos/api/mantenimientos');
            if (!response.ok) throw new Error(`Error en la red: ${response.statusText}`);
            allMantenimientos = await response.json();
            renderTable(allMantenimientos);
        } catch (error) {
            console.error('Error al obtener mantenimientos:', error);
            showToast(error.message || 'Error al cargar los datos.', 'error');
            if (mantenimientosTableBody) {
                mantenimientosTableBody.innerHTML = `
                    <tr><td colspan="5" class="text-center text-danger py-5">Error al cargar los datos. Intente de nuevo.</td></tr>`;
            }
        } finally {
            toggleLoading(false);
        }
    };

    const handleEditClick = async (id) => {
        try {
            const response = await fetch(`/biomedicos/api/mantenimientos/${id}`);
            if (!response.ok) throw new Error('No se pudo cargar la información del mantenimiento.');
            const data = await response.json();

            modalTitle.textContent = `Editar Mantenimiento: ${data.nombre_activo}`;
            document.getElementById('edit-mantenimiento-id').value = data.id;
            document.getElementById('edit-nombre-activo').value = `${data.nombre_activo} (${data.placa_codigo_interno})`;
            populateTipoSelect(document.getElementById('edit-tipo-id'), data.tipo_id);
            document.getElementById('edit-fecha-mantenimiento').value = data.fecha_mantenimiento;
            document.getElementById('edit-duracion-minutos').value = data.duracion_minutos || '';
            document.getElementById('edit-observaciones').value = data.observaciones || '';
            document.getElementById('edit-estado').value = data.estado;

            editModal.show();
        } catch (error) {
            console.error('Error al abrir modal de edición:', error);
            showToast(error.message, 'error');
        }
    };

    const handleFormSubmit = async (e) => {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const id = formData.get('id');

        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';

        try {
            const response = await fetch(`/biomedicos/api/mantenimientos/${id}`, {
                method: 'PUT',
                body: formData,
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || 'Error al actualizar.');

            showToast(result.message || 'Mantenimiento actualizado con éxito', 'success');
            editModal.hide();
            fetchMantenimientos(); // Recargar la tabla
        } catch (error) {
            console.error('Error al guardar:', error);
            showToast(error.message, 'error');
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Guardar Cambios';
        }
    };

    // Carga inicial
    fetchMantenimientoTipos();
    fetchMantenimientos();

    // Event Listeners
    searchInput?.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredData = allMantenimientos.filter(item =>
            item.nombre_activo.toLowerCase().includes(searchTerm) ||
            item.placa_codigo_interno.toLowerCase().includes(searchTerm) ||
            item.tipo_reporte.toLowerCase().includes(searchTerm)
        );
        renderTable(filteredData);
    });

    mantenimientosTableBody?.addEventListener('click', (e) => {
        const editButton = e.target.closest('.btn-edit');
        if (editButton) {
            const id = editButton.dataset.id;
            handleEditClick(id);
        }
    });

    editForm?.addEventListener('submit', handleFormSubmit);
});