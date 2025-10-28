document.addEventListener('DOMContentLoaded', function() {
    // Lógica para resaltar el enlace de navegación activo
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');

    navLinks.forEach(link => {
        if (link.getAttribute('href').endsWith(currentLocation.substring(currentLocation.lastIndexOf('/') + 1))) {
            link.classList.add('active');
        }
    });
});