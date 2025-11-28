/**
 * Detalle de Hoja de Vida - Estilo iOS
 * Sistema de Gestión de Activos Fijos - Módulo Biomédico
 */

/**
 * Generar PDF de la hoja de vida
 */
async function generarPDF(activoId) {
    try {
        showInfo('Generando PDF...');

        const response = await fetch(`/biomedicos/api/hojas-vida/pdf/${activoId}`);

        if (response.ok) {
            // Descargar el PDF
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `Hoja_Vida_${activoId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showSuccess('PDF generado exitosamente');
        } else {
            const error = await response.json();
            showError(error.message || 'Error al generar el PDF');
        }
    } catch (error) {
        console.error('Error al generar PDF:', error);
        showError('Error de conexión al generar el PDF');
    }
}

/**
 * Eliminar hoja de vida
 */
async function eliminarHojaVida(activoId) {
    // Confirmar eliminación
    const confirmar = confirm(
        '¿Está seguro de eliminar esta hoja de vida?\n\n' +
        'Esta acción no se puede deshacer y eliminará:\n' +
        '- Todos los datos de la hoja de vida\n' +
        '- Documentos adjuntos\n' +
        '- Historial de mantenimientos\n\n' +
        '¿Desea continuar?'
    );

    if (!confirmar) return;

    try {
        showInfo('Eliminando hoja de vida...');

        const response = await fetch(`/biomedicos/api/hojas-vida/${activoId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showSuccess('Hoja de vida eliminada exitosamente');

            // Redirigir a la lista después de 1.5 segundos
            setTimeout(() => {
                window.location.href = '/biomedicos/hojas-vida';
            }, 1500);
        } else {
            showError(data.message || 'Error al eliminar la hoja de vida');
        }
    } catch (error) {
        console.error('Error al eliminar:', error);
        showError('Error de conexión al eliminar la hoja de vida');
    }
}

/**
 * Inicialización
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Vista de detalle de hoja de vida cargada');

    // Animar entrada de acordeones
    const accordionItems = document.querySelectorAll('.ios-accordion-item');
    accordionItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(10px)';
            item.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, 50);
        }, index * 50);
    });
});
