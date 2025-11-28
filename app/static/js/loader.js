/**
 * JeroSmart Activos - Loader Controller
 * Controla la visualización y ocultación del loading screen
 * Autor: David Cardoza + Claude
 * Fecha: 2025-11-22
 */

class JeroSmartLoader {
    constructor(options = {}) {
        this.options = {
            minimumDisplayTime: options.minimumDisplayTime || 800, // Tiempo mínimo en ms
            theme: options.theme || 'default', // 'default', 'dark-theme', 'corporate-theme'
            showParticles: options.showParticles !== undefined ? options.showParticles : true,
            showProgressBar: options.showProgressBar !== undefined ? options.showProgressBar : false,
            messages: options.messages || [
                'Cargando módulo...',
                'Preparando datos...',
                'Inicializando sistema...',
                'Casi listo...'
            ]
        };

        this.loaderElement = null;
        this.startTime = null;
        this.messageIndex = 0;
        this.messageInterval = null;
    }

    /**
     * Muestra el loader
     */
    show() {
        this.startTime = Date.now();

        // Si el loader ya existe, solo mostrarlo
        if (this.loaderElement) {
            this.loaderElement.classList.remove('hidden');
            return;
        }

        // Crear el loader
        this.loaderElement = this.createLoaderElement();
        document.body.appendChild(this.loaderElement);

        // Rotar mensajes si hay más de uno
        if (this.options.messages.length > 1) {
            this.startMessageRotation();
        }

        // Prevenir scroll del body
        document.body.style.overflow = 'hidden';
    }

    /**
     * Oculta el loader con tiempo mínimo garantizado
     */
    hide() {
        if (!this.loaderElement) return;

        const elapsedTime = Date.now() - this.startTime;
        const remainingTime = Math.max(0, this.options.minimumDisplayTime - elapsedTime);

        // Detener rotación de mensajes
        if (this.messageInterval) {
            clearInterval(this.messageInterval);
            this.messageInterval = null;
        }

        setTimeout(() => {
            if (this.loaderElement) {
                this.loaderElement.classList.add('hidden');

                // Restaurar scroll del body
                document.body.style.overflow = '';

                // Remover del DOM después de la transición
                setTimeout(() => {
                    if (this.loaderElement && this.loaderElement.parentNode) {
                        this.loaderElement.parentNode.removeChild(this.loaderElement);
                        this.loaderElement = null;
                    }
                }, 600); // Tiempo de la transición CSS
            }
        }, remainingTime);
    }

    /**
     * Actualiza el mensaje mostrado
     */
    updateMessage(message) {
        if (!this.loaderElement) return;

        const messageEl = this.loaderElement.querySelector('.loader-message');
        if (messageEl) {
            messageEl.style.animation = 'none';
            // Trigger reflow
            void messageEl.offsetWidth;
            messageEl.style.animation = 'fadeInUp 0.5s ease-out';
            messageEl.textContent = message;
        }
    }

    /**
     * Inicia la rotación automática de mensajes
     */
    startMessageRotation() {
        this.messageInterval = setInterval(() => {
            this.messageIndex = (this.messageIndex + 1) % this.options.messages.length;
            this.updateMessage(this.options.messages[this.messageIndex]);
        }, 2500);
    }

    /**
     * Crea el elemento HTML del loader
     */
    createLoaderElement() {
        const loader = document.createElement('div');
        loader.id = 'jerosmart-loader';
        loader.className = this.options.theme !== 'default' ? this.options.theme : '';

        loader.innerHTML = `
            ${this.options.showParticles ? this.createParticles() : ''}

            <div class="loader-logo-container">
                <div class="loader-glow-circle"></div>
                <img src="${this.getLogoPath()}" alt="JeroSmart Activos" class="loader-logo">
            </div>

            <div class="loader-text">LOADING...</div>

            <div class="loader-spinner-container">
                <div class="loader-spinner"></div>
                <div class="loader-spinner-secondary"></div>
            </div>

            <div class="loader-dots">
                <div class="loader-dot"></div>
                <div class="loader-dot"></div>
                <div class="loader-dot"></div>
            </div>

            ${this.options.showProgressBar ? `
                <div class="loader-progress-bar-container">
                    <div class="loader-progress-bar"></div>
                </div>
            ` : ''}

            <div class="loader-message">${this.options.messages[0]}</div>
        `;

        return loader;
    }

    /**
     * Crea las partículas de fondo
     */
    createParticles() {
        return `
            <div class="loader-particles">
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
            </div>
        `;
    }

    /**
     * Obtiene la ruta del logo
     */
    getLogoPath() {
        // Intentar detectar la ruta base del static
        const staticBase = window.STATIC_URL || '/static/';
        return `${staticBase}img/logosmartjero.png`;
    }
}

// =============================================================================
// INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
// =============================================================================

// Crear instancia global
window.jeroSmartLoader = new JeroSmartLoader({
    minimumDisplayTime: 800,
    theme: 'default',
    showParticles: true,
    showProgressBar: false,
    messages: [
        'Cargando módulo...',
        'Preparando interfaz...',
        'Sincronizando datos...',
        'Casi listo...'
    ]
});

// Funciones globales de conveniencia
window.showLoader = function(message) {
    if (message) {
        window.jeroSmartLoader.options.messages = [message];
    }
    window.jeroSmartLoader.show();
};

window.hideLoader = function() {
    window.jeroSmartLoader.hide();
};

// =============================================================================
// AUTO-LOADER PARA NAVEGACIÓN
// =============================================================================

/**
 * Mostrar loader automáticamente en navegación de páginas
 */
function setupAutoLoader() {
    // Mostrar loader al hacer click en enlaces internos
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');

        if (link &&
            link.href &&
            !link.hasAttribute('data-no-loader') &&
            !link.hasAttribute('target') &&
            link.href.startsWith(window.location.origin) &&
            !link.href.includes('#')) {

            showLoader('Cargando página...');
        }
    });

    // Mostrar loader en submit de formularios
    document.addEventListener('submit', function(e) {
        const form = e.target;

        if (form && !form.hasAttribute('data-no-loader')) {
            showLoader('Procesando...');
        }
    });

    // Ocultar loader cuando la página carga
    window.addEventListener('load', function() {
        // Pequeño delay para asegurar que todo está listo
        setTimeout(() => {
            hideLoader();
        }, 100);
    });

    // Ocultar loader si hay error de navegación
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            hideLoader();
        }
    });
}

// Inicializar auto-loader cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAutoLoader);
} else {
    setupAutoLoader();
}

// =============================================================================
// INTEGRACIÓN CON FETCH API
// =============================================================================

/**
 * Wrapper para fetch que muestra/oculta loader automáticamente
 */
window.fetchWithLoader = async function(url, options = {}, loaderMessage = 'Cargando...') {
    showLoader(loaderMessage);

    try {
        const response = await fetch(url, options);
        hideLoader();
        return response;
    } catch (error) {
        hideLoader();
        throw error;
    }
};

// =============================================================================
// UTILIDADES ADICIONALES
// =============================================================================

/**
 * Muestra loader por un tiempo específico (útil para demos)
 */
window.showLoaderFor = function(milliseconds, message = 'Cargando...') {
    showLoader(message);
    setTimeout(() => {
        hideLoader();
    }, milliseconds);
};

/**
 * Cambia el tema del loader dinámicamente
 */
window.setLoaderTheme = function(theme) {
    window.jeroSmartLoader.options.theme = theme;
};

console.log('✅ JeroSmart Loader inicializado correctamente');
