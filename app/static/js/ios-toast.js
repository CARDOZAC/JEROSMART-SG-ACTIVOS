/**
 * Sistema de Notificaciones Toast - Estilo iOS
 * JeroSmart Activos Fijos
 */

class iOSToast {
    /**
     * Muestra una notificación toast
     * @param {string} mensaje - Texto a mostrar
     * @param {string} tipo - Tipo: 'success', 'error', 'warning', 'info'
     * @param {number} duracion - Duración en milisegundos (default: 3000)
     */
    static show(mensaje, tipo = 'info', duracion = 3000) {
        // Crear elemento toast
        const toast = document.createElement('div');
        toast.className = `ios-toast ios-toast-${tipo}`;
        toast.innerHTML = `
            <div class="ios-toast-content">
                <i class="bi ${this.getIcon(tipo)}"></i>
                <span>${mensaje}</span>
            </div>
        `;

        // Agregar al body
        document.body.appendChild(toast);

        // Animar entrada
        setTimeout(() => toast.classList.add('show'), 100);

        // Animar salida y eliminar
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duracion);
    }

    /**
     * Obtiene el icono según el tipo
     * @param {string} tipo - Tipo de notificación
     * @returns {string} - Clase del icono Bootstrap
     */
    static getIcon(tipo) {
        const icons = {
            'success': 'bi-check-circle-fill',
            'error': 'bi-x-circle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'info': 'bi-info-circle-fill'
        };
        return icons[tipo] || icons['info'];
    }
}

// Crear alias globales para facilitar uso
window.showSuccess = function(mensaje, duracion) {
    iOSToast.show(mensaje, 'success', duracion);
};

window.showError = function(mensaje, duracion) {
    iOSToast.show(mensaje, 'error', duracion);
};

window.showWarning = function(mensaje, duracion) {
    iOSToast.show(mensaje, 'warning', duracion);
};

window.showInfo = function(mensaje, duracion) {
    iOSToast.show(mensaje, 'info', duracion);
};

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = iOSToast;
}
