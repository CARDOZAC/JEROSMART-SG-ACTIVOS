document.addEventListener('DOMContentLoaded', function() {
    // Año automático en footer
    const yearSpan = document.getElementById('year');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }

    // Autocierre de mensajes flash
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            // Comprobar si el elemento todavía existe y es visible antes de intentar cerrarlo
            if (message && message.classList.contains('show')) {
                const alertInstance = bootstrap.Alert.getOrCreateInstance(message);
                if (alertInstance) {
                    alertInstance.close();
                }
            }
        }, 5000);
    });
});
