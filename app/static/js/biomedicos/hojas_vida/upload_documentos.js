/**
 * Sistema de Carga de Documentos - Dropzone.js
 * Sistema de Gestión de Activos Fijos - Módulo Biomédico
 */

// Deshabilitar auto-discover de Dropzone
Dropzone.autoDiscover = false;

// Instancias de Dropzone
const dropzones = {};

/**
 * Inicializar Dropzones cuando el DOM esté listo
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeDropzone('calibraciones', 'Calibraciones');
    initializeDropzone('preventivo', 'Mantenimiento Preventivo');
    initializeDropzone('correctivo', 'Mantenimiento Correctivo');
    initializeDropzone('legal', 'Documentación Legal');
});

/**
 * Inicializar una instancia de Dropzone
 */
function initializeDropzone(categoria, nombreCategoria) {
    const dropzoneElement = document.getElementById(`dropzone-${categoria}`);

    if (!dropzoneElement) {
        console.error(`No se encontró el elemento dropzone-${categoria}`);
        return;
    }

    const myDropzone = new Dropzone(dropzoneElement, {
        url: '/biomedicos/api/hojas-vida/upload-temp', // Endpoint temporal
        paramName: 'file',
        maxFilesize: 10, // MB
        acceptedFiles: '.pdf,application/pdf',
        addRemoveLinks: true,
        clickable: true, // IMPORTANTE: Hacer clickeable
        dictDefaultMessage: '', // Vacío porque ya tenemos HTML en el template
        dictRemoveFile: 'Eliminar',
        dictCancelUpload: 'Cancelar',
        dictFileTooBig: 'El archivo es demasiado grande (máx. 10MB)',
        dictInvalidFileType: 'Solo se permiten archivos PDF',
        autoProcessQueue: true, // Procesar inmediatamente
        parallelUploads: 1,
        uploadMultiple: false,
        previewsContainer: `#file-list-${categoria}`, // Mostrar previews en contenedor específico
        previewTemplate: `
            <div class="file-item">
                <div class="file-item-info">
                    <i class="bi bi-file-pdf file-item-icon"></i>
                    <div class="file-item-details">
                        <div class="file-item-name" data-dz-name></div>
                        <div class="file-item-size" data-dz-size></div>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-danger" data-dz-remove>
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `,

        init: function() {
            const dz = this;

            // Cuando un archivo se agrega
            this.on('addedfile', function(file) {
                console.log(`Archivo agregado en ${categoria}:`, file.name);
            });

            // Cuando la carga es exitosa
            this.on('success', function(file, response) {
                console.log(`Archivo subido exitosamente en ${categoria}:`, response);

                // Guardar referencia del archivo temporal en datosWizard
                if (!datosWizard.paso3[categoria]) {
                    datosWizard.paso3[categoria] = [];
                }

                datosWizard.paso3[categoria].push({
                    nombre_original: file.name,
                    nombre_temporal: response.filename,
                    ruta_temporal: response.filepath,
                    tamano: file.size,
                    checksum: response.checksum
                });

                // Guardar en sessionStorage
                sessionStorage.setItem('datosWizard', JSON.stringify(datosWizard));

                showSuccess(`Archivo cargado: ${file.name}`);
            });

            // Cuando hay un error
            this.on('error', function(file, errorMessage) {
                console.error(`Error al subir archivo en ${categoria}:`, errorMessage);

                let mensaje = 'Error al cargar el archivo';
                if (typeof errorMessage === 'string') {
                    mensaje = errorMessage;
                } else if (errorMessage.message) {
                    mensaje = errorMessage.message;
                }

                showError(mensaje);
            });

            // Cuando se elimina un archivo
            this.on('removedfile', function(file) {
                console.log(`Archivo eliminado en ${categoria}:`, file.name);

                // Eliminar del array datosWizard.paso3
                if (datosWizard.paso3[categoria]) {
                    datosWizard.paso3[categoria] = datosWizard.paso3[categoria].filter(
                        archivo => archivo.nombre_original !== file.name
                    );

                    // Actualizar sessionStorage
                    sessionStorage.setItem('datosWizard', JSON.stringify(datosWizard));
                }

                showInfo(`Archivo eliminado: ${file.name}`);
            });

            // Cuando se envía un archivo
            this.on('sending', function(file, xhr, formData) {
                // Agregar metadatos adicionales
                formData.append('categoria', categoria);
            });
        }
    });

    // Guardar instancia
    dropzones[categoria] = myDropzone;
}

/**
 * Obtener archivos de una categoría
 */
function obtenerArchivosCategoria(categoria) {
    if (dropzones[categoria]) {
        return dropzones[categoria].files;
    }
    return [];
}

/**
 * Limpiar todos los dropzones
 */
function limpiarTodosDropzones() {
    Object.keys(dropzones).forEach(categoria => {
        if (dropzones[categoria]) {
            dropzones[categoria].removeAllFiles(true);
        }
    });

    // Limpiar datos
    datosWizard.paso3 = {
        calibraciones: [],
        preventivo: [],
        correctivo: [],
        legal: []
    };

    sessionStorage.setItem('datosWizard', JSON.stringify(datosWizard));
}

/**
 * Obtener resumen de archivos cargados
 */
function obtenerResumenArchivos() {
    const resumen = {
        total: 0,
        categorias: {}
    };

    Object.keys(dropzones).forEach(categoria => {
        const archivos = dropzones[categoria].files.length;
        resumen.categorias[categoria] = archivos;
        resumen.total += archivos;
    });

    return resumen;
}
