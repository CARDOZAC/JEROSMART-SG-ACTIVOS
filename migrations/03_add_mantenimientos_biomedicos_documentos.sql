-- ==============================================================================
-- TABLA: mantenimientos_biomedicos_documentos
-- Propósito: Almacenar documentos escaneados de mantenimientos para equipos BIOMÉDICOS
-- ==============================================================================

USE `jerosmart_activos`;

CREATE TABLE IF NOT EXISTS `mantenimientos_biomedicos_documentos` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID único del documento',
  `mantenimiento_biomedico_id` INT NOT NULL COMMENT 'ID del mantenimiento biomédico al que pertenece',

  -- Información del archivo
  `nombre_archivo` VARCHAR(255) NOT NULL COMMENT 'Nombre del archivo original',
  `ruta_archivo` VARCHAR(500) NOT NULL COMMENT 'Ruta relativa donde se almacena',
  `tipo_documento` ENUM('pdf', 'imagen', 'excel', 'word', 'otro') DEFAULT 'pdf' COMMENT 'Tipo de documento',
  `tamano_archivo` INT COMMENT 'Tamaño del archivo en bytes',

  -- Metadatos del mantenimiento escaneado
  `fecha_documento` DATE COMMENT 'Fecha del mantenimiento físico escaneado',
  `descripcion` TEXT COMMENT 'Descripción o notas sobre el documento',

  -- Auditoría
  `uploaded_by` INT COMMENT 'Usuario que subió el documento',
  `uploaded_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de carga',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  KEY `idx_mantenimiento_biomedico` (`mantenimiento_biomedico_id`),

  CONSTRAINT `fk_doc_mantenimiento_biomedico`
    FOREIGN KEY (`mantenimiento_biomedico_id`)
    REFERENCES `mantenimientos_biomedicos` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT `fk_doc_biomedico_uploader`
    FOREIGN KEY (`uploaded_by`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Documentos escaneados para mantenimientos de equipos biomédicos';
