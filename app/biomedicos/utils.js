/**
 * Muestra una notificación toast estilo iOS.
 * @param {string} message - El mensaje a mostrar.
 * @param {string} [type='info'] - El tipo de toast ('success', 'warning', 'error', 'info').
 * @param {number} [duration=3000] - La duración en milisegundos.
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `ios-toast ios-toast-${type}`;

    const icons = {
        success: 'bi-check-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        error: 'bi-x-circle-fill',
        info: 'bi-info-circle-fill'
    };

    toast.innerHTML = `
        <i class="bi ${icons[type]}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    // Animar la entrada
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Animar la salida y eliminar
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 500); // Coincide con la duración de la transición CSS
    }, duration);
}

/**
 * Muestra un modal de confirmación estilo iOS.
 * @param {object} options - Opciones de configuración del modal.
 * @param {string} options.title - Título del modal.
 * @param {string} options.message - Mensaje principal del modal.
 * @param {string} [options.confirmText='Confirmar'] - Texto del botón de confirmación.
 * @param {string} [options.cancelText='Cancelar'] - Texto del botón de cancelación.
 * @param {boolean} [options.isDestructive=false] - Si la acción es destructiva (botón rojo).
 * @returns {Promise<boolean>} - Promesa que resuelve a `true` si se confirma, `false` si se cancela.
 */
function showConfirmationModal({ title, message, confirmText = 'Confirmar', cancelText = 'Cancelar', isDestructive = false }) {
    return new Promise((resolve) => {
        const modalId = `ios-modal-${Date.now()}`;
        const confirmClass = isDestructive ? 'btn-danger' : 'btn-primary';

        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}-label" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content ios-card">
                        <div class="modal-header border-0">
                            <h5 class="modal-title w-100 text-center" id="${modalId}-label">${title}</h5>
                        </div>
                        <div class="modal-body text-center text-muted">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer border-0 d-flex justify-content-center">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelText}</button>
                            <button type="button" class="btn ${confirmClass}" id="${modalId}-confirm">${confirmText}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modalElement = document.getElementById(modalId);
        const confirmButton = document.getElementById(`${modalId}-confirm`);
        const modal = new bootstrap.Modal(modalElement);

        const handleConfirm = () => {
            resolve(true);
            modal.hide();
        };

        const handleClose = () => {
            resolve(false);
            modalElement.remove();
        };

        confirmButton.addEventListener('click', handleConfirm);
        modalElement.addEventListener('hidden.bs.modal', handleClose);

        modal.show();
    });
}