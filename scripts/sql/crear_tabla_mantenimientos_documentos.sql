-- ==============================================================================
-- TABLA: mantenimientos_documentos
-- Propósito: Almacenar documentos escaneados de mantenimientos físicos
-- Compatible con: Módulo de Mantenimientos (No Biomédicos) y Biomédicos
-- ==============================================================================

USE `jerosmart_activos`;

CREATE TABLE IF NOT EXISTS `mantenimientos_documentos` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID único del documento',
  `mantenimiento_id` INT NOT NULL COMMENT 'ID del mantenimiento al que pertenece',

  -- Información del archivo
  `nombre_archivo` VARCHAR(255) NOT NULL COMMENT 'Nombre del archivo original',
  `ruta_archivo` VARCHAR(500) NOT NULL COMMENT 'Ruta relativa donde se almacena',
  `tipo_documento` ENUM('pdf', 'imagen', 'excel', 'word', 'otro') DEFAULT 'pdf' COMMENT 'Tipo de documento',
  `tamano_archivo` INT COMMENT 'Tamaño del archivo en bytes',

  -- Metadatos del mantenimiento escaneado
  `fecha_documento` DATE COMMENT 'Fecha del mantenimiento físico escaneado',
  `tecnico_responsable` VARCHAR(200) COMMENT 'Técnico que realizó el mantenimiento',
  `descripcion` TEXT COMMENT 'Descripción o notas sobre el documento',

  -- Auditoría
  `uploaded_by` INT COMMENT 'Usuario que subió el documento',
  `uploaded_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de carga',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  KEY `idx_mantenimiento` (`mantenimiento_id`),
  KEY `idx_fecha_documento` (`fecha_documento`),
  KEY `idx_tipo` (`tipo_documento`),

  CONSTRAINT `fk_doc_mantenimiento`
    FOREIGN KEY (`mantenimiento_id`)
    REFERENCES `mantenimientos` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT `fk_doc_uploader`
    FOREIGN KEY (`uploaded_by`)
    REFERENCES `users` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Documentos escaneados de mantenimientos físicos realizados';

-- Índices adicionales para optimización
CREATE INDEX `idx_uploaded_at` ON `mantenimientos_documentos` (`uploaded_at`);
CREATE INDEX `idx_composite_mant_fecha` ON `mantenimientos_documentos` (`mantenimiento_id`, `fecha_documento`);

-- Verificar creación
SELECT
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM
    information_schema.TABLES
WHERE
    TABLE_SCHEMA = 'jerosmart_activos'
    AND TABLE_NAME = 'mantenimientos_documentos';

SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_KEY,
    COLUMN_COMMENT
FROM
    information_schema.COLUMNS
WHERE
    TABLE_SCHEMA = 'jerosmart_activos'
    AND TABLE_NAME = 'mantenimientos_documentos'
ORDER BY
    ORDINAL_POSITION;
