// ==============================================================================
// WIZARD COMPONENT UNIVERSAL
// ==============================================================================
/**
 * Componente universal para formularios multi-paso (wizards).
 * Proporciona navegación, validación y gestión de estado para formularios complejos.
 *
 * @example
 * const wizard = new WizardComponent({
 *   steps: [
 *     { id: 'step-1', title: 'Información Básica', validate: () => validateStep1() },
 *     { id: 'step-2', title: 'Detalles', validate: () => validateStep2() },
 *     { id: 'step-3', title: 'Confirmación', validate: () => true }
 *   ],
 *   onComplete: (data) => submitForm(data),
 *   progressBarId: 'wizard-progress',
 *   nextButtonId: 'btn-next',
 *   prevButtonId: 'btn-prev',
 *   submitButtonId: 'btn-submit'
 * });
 */
class WizardComponent {
    /**
     * Crea una nueva instancia del wizard.
     * @param {Object} config - Configuración del wizard
     * @param {Array} config.steps - Array de pasos del wizard
     * @param {Function} config.onComplete - Callback cuando se completa el wizard
     * @param {string} config.progressBarId - ID del elemento de barra de progreso
     * @param {string} config.stepLabelId - ID del elemento para el título del paso
     * @param {string} config.stepCountId - ID del elemento para el contador de pasos
     * @param {string} config.nextButtonId - ID del botón siguiente
     * @param {string} config.prevButtonId - ID del botón anterior
     * @param {string} config.submitButtonId - ID del botón de envío
     * @param {string} config.stepIndicatorId - ID del contenedor de indicadores de paso
     */
    constructor(config) {
        this.steps = config.steps || [];
        this.currentStep = 0;
        this.data = {};
        this.onComplete = config.onComplete || (() => {});

        // Referencias a elementos DOM
        this.progressBar = document.getElementById(config.progressBarId || 'wizard-progress-bar');
        this.stepLabel = document.getElementById(config.stepLabelId || 'wizard-step-label');
        this.stepCount = document.getElementById(config.stepCountId || 'wizard-step-count');
        this.nextButton = document.getElementById(config.nextButtonId || 'wizard-btn-next');
        this.prevButton = document.getElementById(config.prevButtonId || 'wizard-btn-prev');
        this.submitButton = document.getElementById(config.submitButtonId || 'wizard-btn-submit');
        this.stepIndicator = document.getElementById(config.stepIndicatorId || 'wizard-step-indicator');

        this.init();
    }

    /**
     * Inicializa el wizard y configura los event listeners.
     */
    init() {
        if (this.nextButton) {
            this.nextButton.addEventListener('click', () => this.nextStep());
        }

        if (this.prevButton) {
            this.prevButton.addEventListener('click', () => this.prevStep());
        }

        if (this.submitButton) {
            this.submitButton.addEventListener('click', () => this.complete());
        }

        this.render();
        this.renderStepIndicators();
    }

    /**
     * Valida el paso actual.
     * @returns {boolean} true si el paso es válido
     */
    validateCurrentStep() {
        const currentStepConfig = this.steps[this.currentStep];
        if (currentStepConfig && currentStepConfig.validate) {
            return currentStepConfig.validate();
        }
        return true;
    }

    /**
     * Guarda los datos del paso actual.
     */
    saveStepData() {
        const currentStepConfig = this.steps[this.currentStep];
        if (currentStepConfig && currentStepConfig.onSave) {
            const stepData = currentStepConfig.onSave();
            this.data[currentStepConfig.id] = stepData;
        }
    }

    /**
     * Avanza al siguiente paso.
     */
    nextStep() {
        if (!this.validateCurrentStep()) {
            return;
        }

        this.saveStepData();

        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.render();
            this.renderStepIndicators();
        }
    }

    /**
     * Retrocede al paso anterior.
     */
    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.render();
            this.renderStepIndicators();
        }
    }

    /**
     * Completa el wizard y ejecuta el callback.
     */
    complete() {
        if (!this.validateCurrentStep()) {
            return;
        }

        this.saveStepData();
        this.onComplete(this.data);
    }

    /**
     * Renderiza el estado actual del wizard.
     */
    render() {
        // Ocultar todos los pasos
        this.steps.forEach((step, index) => {
            const stepElement = document.getElementById(step.id);
            if (stepElement) {
                stepElement.classList.toggle('hidden', index !== this.currentStep);
                stepElement.classList.toggle('wizard-step-active', index === this.currentStep);
            }
        });

        // Actualizar barra de progreso
        const progress = this.getProgressPercentage();
        if (this.progressBar) {
            this.progressBar.style.width = `${progress}%`;
            this.progressBar.setAttribute('aria-valuenow', progress);
            this.progressBar.textContent = `Paso ${this.currentStep + 1} de ${this.steps.length} (${Math.round(progress)}%)`;
        }

        // Actualizar etiquetas
        if (this.stepLabel) {
            const currentStepConfig = this.steps[this.currentStep];
            this.stepLabel.textContent = currentStepConfig.title || `Paso ${this.currentStep + 1}`;
        }

        if (this.stepCount) {
            this.stepCount.textContent = `${this.currentStep + 1} de ${this.steps.length}`;
        }

        // Controlar visibilidad de botones
        if (this.prevButton) {
            this.prevButton.disabled = this.currentStep === 0;
        }

        if (this.nextButton) {
            this.nextButton.classList.toggle('hidden', this.currentStep === this.steps.length - 1);
        }

        if (this.submitButton) {
            this.submitButton.classList.toggle('hidden', this.currentStep !== this.steps.length - 1);
        }

        // Ejecutar callback de renderizado del paso si existe
        const currentStepConfig = this.steps[this.currentStep];
        if (currentStepConfig && currentStepConfig.onRender) {
            currentStepConfig.onRender();
        }
    }

    /**
     * Renderiza los indicadores visuales de pasos.
     */
    renderStepIndicators() {
        if (!this.stepIndicator) return;

        this.stepIndicator.innerHTML = '';

        this.steps.forEach((step, index) => {
            const indicator = document.createElement('div');
            indicator.className = 'wizard-step-indicator';

            if (index < this.currentStep) {
                indicator.classList.add('completed');
                indicator.innerHTML = `
                    <i class="fas fa-check-circle"></i>
                    <span>${step.title || `Paso ${index + 1}`}</span>
                `;
            } else if (index === this.currentStep) {
                indicator.classList.add('active');
                indicator.innerHTML = `
                    <i class="fas fa-circle"></i>
                    <span>${step.title || `Paso ${index + 1}`}</span>
                `;
            } else {
                indicator.innerHTML = `
                    <i class="far fa-circle"></i>
                    <span>${step.title || `Paso ${index + 1}`}</span>
                `;
            }

            this.stepIndicator.appendChild(indicator);
        });
    }

    /**
     * Calcula el porcentaje de progreso actual.
     * @returns {number} Porcentaje de progreso (0-100)
     */
    getProgressPercentage() {
        return ((this.currentStep + 1) / this.steps.length) * 100;
    }

    /**
     * Navega a un paso específico.
     * @param {number} stepIndex - Índice del paso (0-based)
     */
    goToStep(stepIndex) {
        if (stepIndex >= 0 && stepIndex < this.steps.length) {
            this.currentStep = stepIndex;
            this.render();
            this.renderStepIndicators();
        }
    }

    /**
     * Resetea el wizard al primer paso.
     */
    reset() {
        this.currentStep = 0;
        this.data = {};
        this.render();
        this.renderStepIndicators();
    }
}

// ==============================================================================
// INICIALIZACIÓN GLOBAL
// ==============================================================================
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

    // ==============================================================================
    // MICRO-INTERACCIONES iOS - EFECTOS AVANZADOS
    // ==============================================================================

    // Efecto Ripple en tarjetas iOS
    const iosCards = document.querySelectorAll('.ios-card, .ios-btn-primary, .ios-btn-success');
    iosCards.forEach(card => {
        card.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple-effect');

            const existingRipple = this.querySelector('.ripple-effect');
            if (existingRipple) {
                existingRipple.remove();
            }

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Agregar estilos dinámicos para el efecto ripple
    if (!document.getElementById('ripple-styles')) {
        const style = document.createElement('style');
        style.id = 'ripple-styles';
        style.textContent = `
            .ripple-effect {
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: scale(0);
                animation: ripple-animation 0.6s ease-out;
                pointer-events: none;
            }
            @keyframes ripple-animation {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Efecto de parallax suave en el scroll
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                const scrolled = window.pageYOffset;
                const parallaxElements = document.querySelectorAll('.hero-gradient');

                parallaxElements.forEach(element => {
                    const speed = 0.5;
                    const yPos = -(scrolled * speed);
                    element.style.transform = `translateY(${yPos}px)`;
                });

                ticking = false;
            });
            ticking = true;
        }
    });

    // Contador animado para estadísticas
    const animateValue = (element, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };

    // Iniciar animación de contadores cuando sean visibles
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                const target = entry.target.querySelector('.ios-stat-value');
                if (target) {
                    const finalValue = parseInt(target.textContent);
                    target.textContent = '0';
                    animateValue(target, 0, finalValue, 1500);
                    entry.target.classList.add('animated');
                }
            }
        });
    }, observerOptions);

    const statCards = document.querySelectorAll('.ios-stat-card');
    statCards.forEach(card => observer.observe(card));

    // Efecto de hover mejorado para tarjetas de acción
    const actionCards = document.querySelectorAll('.ios-card');
    actionCards.forEach(card => {
        card.addEventListener('mouseenter', function(e) {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function(e) {
            this.style.transform = 'translateY(0) scale(1)';
        });

        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            this.style.transform = `translateY(-8px) scale(1.02) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
    });

    // Smooth scroll para enlaces internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    console.log('✨ JeroSmart - Sistema de Gestión de Activos Fijos');
    console.log('🎨 Diseño iOS mejorado cargado correctamente');
    console.log('💫 Micro-interacciones activadas');
});

// ==============================================================================
// DARK MODE TOGGLE
// ==============================================================================
/**
 * Función para cambiar entre modo claro y oscuro
 * Guarda la preferencia en localStorage para persistencia
 */
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Animación suave
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
}

/**
 * Inicializar tema al cargar la página
 * Verifica localStorage o usa preferencia del sistema
 */
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

// Ejecutar al cargar la página
initTheme();

// Escuchar cambios en la preferencia del sistema
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
});

