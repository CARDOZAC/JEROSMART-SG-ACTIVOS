-- ================================================================================
-- SCRIPT DE CREACIÓN DE TABLAS FALTANTES - JEROSMART ACTIVOS
-- Autor: Claude Code - Profesional en Activos Fijos Clínicos Colombianos
-- Fecha: 2025-11-28
-- Base de datos: jerosmart_activos
-- Motor: MySQL 8.0+
-- ================================================================================

-- Seleccionar la base de datos
USE jerosmart_activos;

-- ================================================================================
-- CONFIGURACIÓN INICIAL
-- ================================================================================
SET FOREIGN_KEY_CHECKS = 0;

-- ================================================================================
-- TABLA 1: hojas_vida_equipos
-- Descripción: Hojas de vida para equipos no biomédicos (TICs, Mobiliario, Equipos Industriales)
-- Relación: 1:1 con tabla 'activos'
-- ================================================================================

DROP TABLE IF EXISTS `hojas_vida_equipos`;

CREATE TABLE `hojas_vida_equipos` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'Identificador único de la hoja de vida',
  `activo_id` INT NOT NULL COMMENT 'ID del activo (relación 1:1 con tabla activos)',

  -- ============================================================================
  -- SECCIÓN: CARACTERÍSTICAS COMERCIALES
  -- ============================================================================
  `proveedor_nombre` VARCHAR(255) DEFAULT NULL COMMENT 'Nombre del proveedor/distribuidor',
  `fecha_adquisicion` DATE DEFAULT NULL COMMENT 'Fecha de compra del equipo',
  `costo_adquisicion` DECIMAL(15, 2) DEFAULT NULL COMMENT 'Costo de adquisición en pesos colombianos',
  `numero_factura` VARCHAR(100) DEFAULT NULL COMMENT 'Número de factura de compra',
  `numero_orden_compra` VARCHAR(100) DEFAULT NULL COMMENT 'Número de orden de compra',
  `garantia_meses` INT DEFAULT NULL COMMENT 'Tiempo de garantía en meses',
  `fecha_vencimiento_garantia` DATE DEFAULT NULL COMMENT 'Fecha de vencimiento de la garantía',
  `vida_util_anios` INT DEFAULT NULL COMMENT 'Vida útil estimada en años',

  -- ============================================================================
  -- SECCIÓN: CARACTERÍSTICAS TÉCNICAS GENERALES
  -- ============================================================================
  `voltaje` VARCHAR(50) DEFAULT NULL COMMENT 'Voltaje de operación (ej: 110V, 220V)',
  `potencia` VARCHAR(50) DEFAULT NULL COMMENT 'Potencia en watts o HP',
  `corriente` VARCHAR(50) DEFAULT NULL COMMENT 'Corriente de operación en amperios',
  `frecuencia` VARCHAR(50) DEFAULT NULL COMMENT 'Frecuencia en Hz (ej: 60Hz)',
  `dimensiones` VARCHAR(100) DEFAULT NULL COMMENT 'Dimensiones físicas (largo x ancho x alto)',
  `peso` VARCHAR(50) DEFAULT NULL COMMENT 'Peso del equipo en kg',
  `color` VARCHAR(50) DEFAULT NULL COMMENT 'Color del equipo',
  `material` VARCHAR(100) DEFAULT NULL COMMENT 'Material de construcción',

  -- ============================================================================
  -- SECCIÓN: DOCUMENTACIÓN TÉCNICA
  -- ============================================================================
  `manual_usuario` TINYINT(1) DEFAULT 0 COMMENT 'Indica si tiene manual de usuario (1=Sí, 0=No)',
  `manual_servicio` TINYINT(1) DEFAULT 0 COMMENT 'Indica si tiene manual de servicio (1=Sí, 0=No)',
  `manual_instalacion` TINYINT(1) DEFAULT 0 COMMENT 'Indica si tiene manual de instalación (1=Sí, 0=No)',

  -- ============================================================================
  -- SECCIÓN: CARACTERÍSTICAS ESPECÍFICAS POR TIPO DE EQUIPO (JSON FLEXIBLE)
  -- ============================================================================
  -- Almacenamiento flexible usando JSON para diferentes categorías:
  --
  -- PARA TICs (clase_id = 3):
  --   {
  --     "sistema_operativo": "Windows 11 Pro",
  --     "procesador": "Intel Core i7-12700K",
  --     "ram": "32GB DDR4",
  --     "disco": "1TB NVMe SSD",
  --     "tipo_equipo": "Computador de escritorio"
  --   }
  --
  -- PARA EQUIPOS ELECTRO-INDUSTRIALES (clase_id = 2):
  --   {
  --     "capacidad": "500 litros",
  --     "tipo_combustible": "Diesel",
  --     "tipo_motor": "4 tiempos",
  --     "tipo_refrigerante": "Aire forzado"
  --   }
  --
  -- PARA MOBILIARIO Y ENSERES (clase_id = 4):
  --   {
  --     "tipo_mueble": "Escritorio ejecutivo",
  --     "numero_cajones": "3",
  --     "acabado": "Laminado melamínico",
  --     "tapiceria": "Cuero sintético negro"
  --   }
  --
  `caracteristicas_especificas_json` JSON DEFAULT NULL COMMENT 'Características específicas según tipo de equipo en formato JSON',

  -- ============================================================================
  -- SECCIÓN: OBSERVACIONES Y CONDICIONES DE USO
  -- ============================================================================
  `observaciones_tecnicas` TEXT DEFAULT NULL COMMENT 'Observaciones técnicas generales del equipo',
  `condiciones_uso` TEXT DEFAULT NULL COMMENT 'Condiciones especiales de uso y mantenimiento',
  `restricciones` TEXT DEFAULT NULL COMMENT 'Restricciones de uso o seguridad',

  -- ============================================================================
  -- SECCIÓN: FOTOGRAFÍAS DEL EQUIPO
  -- ============================================================================
  `foto_url` VARCHAR(255) DEFAULT NULL COMMENT 'URL de la foto principal del equipo',
  `foto_2_url` VARCHAR(255) DEFAULT NULL COMMENT 'URL de la foto secundaria del equipo',
  `foto_3_url` VARCHAR(255) DEFAULT NULL COMMENT 'URL de la foto terciaria del equipo',

  -- ============================================================================
  -- SECCIÓN: AUDITORÍA Y TRAZABILIDAD
  -- ============================================================================
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha y hora de creación del registro',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha y hora de última actualización',
  `created_by` INT DEFAULT NULL COMMENT 'ID del usuario que creó el registro',
  `updated_by` INT DEFAULT NULL COMMENT 'ID del usuario que actualizó el registro',

  -- ============================================================================
  -- CONSTRAINTS Y LLAVES
  -- ============================================================================
  PRIMARY KEY (`id`),

  -- Garantizar que cada activo tenga solo UNA hoja de vida
  UNIQUE KEY `uq_activo_id` (`activo_id`),

  -- ============================================================================
  -- RELACIONES (FOREIGN KEYS)
  -- ============================================================================

  -- Relación con la tabla activos (CASCADE para mantener integridad)
  CONSTRAINT `fk_hoja_vida_equipo_activo`
    FOREIGN KEY (`activo_id`)
    REFERENCES `activos` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- Relación con usuario creador
  CONSTRAINT `fk_hoja_vida_equipo_creator`
    FOREIGN KEY (`created_by`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  -- Relación con usuario actualizador
  CONSTRAINT `fk_hoja_vida_equipo_updater`
    FOREIGN KEY (`updated_by`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  -- ============================================================================
  -- ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS
  -- ============================================================================
  INDEX `idx_hoja_vida_equipo_activo` (`activo_id`),
  INDEX `idx_hoja_vida_equipo_created_at` (`created_at`),
  INDEX `idx_hoja_vida_equipo_updated_at` (`updated_at`)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Hojas de vida para equipos no biomédicos: TICs, Mobiliario y Equipos Electro-Industriales';


-- ================================================================================
-- TABLA 2: activos_fotos
-- Descripción: Galería de fotografías para cada activo (relación 1:N)
-- Permite almacenar múltiples fotos por activo de forma organizada
-- ================================================================================

DROP TABLE IF EXISTS `activos_fotos`;

CREATE TABLE `activos_fotos` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'Identificador único de la foto',
  `activo_id` INT NOT NULL COMMENT 'ID del activo al que pertenece la foto',

  -- ============================================================================
  -- DATOS DE LA FOTOGRAFÍA
  -- ============================================================================
  `nombre_archivo` VARCHAR(255) NOT NULL COMMENT 'Nombre del archivo de imagen',
  `ruta_archivo` VARCHAR(500) NOT NULL COMMENT 'Ruta completa del archivo en el servidor',
  `url_publica` VARCHAR(500) DEFAULT NULL COMMENT 'URL pública para acceder a la imagen',

  -- Metadatos de la imagen
  `tipo_foto` ENUM(
    'principal',
    'frontal',
    'lateral',
    'posterior',
    'detalle',
    'placa',
    'serie',
    'manual',
    'instalacion',
    'mantenimiento',
    'dano',
    'otro'
  ) DEFAULT 'otro' COMMENT 'Tipo o categoría de la fotografía',

  `descripcion` TEXT DEFAULT NULL COMMENT 'Descripción o notas sobre la fotografía',
  `orden` INT DEFAULT 0 COMMENT 'Orden de visualización (menor número = mayor prioridad)',

  -- Datos técnicos de la imagen
  `tamano_bytes` BIGINT DEFAULT NULL COMMENT 'Tamaño del archivo en bytes',
  `extension` VARCHAR(10) DEFAULT NULL COMMENT 'Extensión del archivo (jpg, png, etc.)',
  `ancho_px` INT DEFAULT NULL COMMENT 'Ancho de la imagen en píxeles',
  `alto_px` INT DEFAULT NULL COMMENT 'Alto de la imagen en píxeles',

  -- ============================================================================
  -- AUDITORÍA
  -- ============================================================================
  `fecha_captura` DATE DEFAULT NULL COMMENT 'Fecha en que se tomó la fotografía',
  `uploaded_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha y hora de carga al sistema',
  `uploaded_by` INT DEFAULT NULL COMMENT 'ID del usuario que subió la foto',

  -- ============================================================================
  -- CONSTRAINTS Y LLAVES
  -- ============================================================================
  PRIMARY KEY (`id`),

  -- ============================================================================
  -- RELACIONES (FOREIGN KEYS)
  -- ============================================================================

  -- Relación con activos (CASCADE para eliminar fotos si se elimina el activo)
  CONSTRAINT `fk_activo_foto_activo`
    FOREIGN KEY (`activo_id`)
    REFERENCES `activos` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- Relación con usuario que subió la foto
  CONSTRAINT `fk_activo_foto_uploader`
    FOREIGN KEY (`uploaded_by`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  -- ============================================================================
  -- ÍNDICES PARA OPTIMIZACIÓN
  -- ============================================================================
  INDEX `idx_activo_foto_activo` (`activo_id`),
  INDEX `idx_activo_foto_tipo` (`tipo_foto`),
  INDEX `idx_activo_foto_orden` (`orden`),
  INDEX `idx_activo_foto_uploaded` (`uploaded_at`)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Galería de fotografías para activos - Permite múltiples imágenes por activo';


-- ================================================================================
-- RESTAURAR CONFIGURACIÓN
-- ================================================================================
SET FOREIGN_KEY_CHECKS = 1;


-- ================================================================================
-- VERIFICACIÓN DE CREACIÓN
-- ================================================================================
SELECT
  'hojas_vida_equipos' AS tabla_creada,
  COUNT(*) AS total_columnas
FROM information_schema.COLUMNS
WHERE table_schema = 'jerosmart_activos'
  AND table_name = 'hojas_vida_equipos'

UNION ALL

SELECT
  'activos_fotos' AS tabla_creada,
  COUNT(*) AS total_columnas
FROM information_schema.COLUMNS
WHERE table_schema = 'jerosmart_activos'
  AND table_name = 'activos_fotos';


-- ================================================================================
-- COMANDOS DE VERIFICACIÓN OPCIONALES (descomenta para usar)
-- ================================================================================

-- Ver estructura de hojas_vida_equipos:
-- DESCRIBE hojas_vida_equipos;

-- Ver estructura de activos_fotos:
-- DESCRIBE activos_fotos;

-- Ver todas las foreign keys de hojas_vida_equipos:
-- SELECT
--   CONSTRAINT_NAME,
--   COLUMN_NAME,
--   REFERENCED_TABLE_NAME,
--   REFERENCED_COLUMN_NAME
-- FROM information_schema.KEY_COLUMN_USAGE
-- WHERE TABLE_NAME = 'hojas_vida_equipos'
--   AND TABLE_SCHEMA = 'jerosmart_activos'
--   AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Ver todas las foreign keys de activos_fotos:
-- SELECT
--   CONSTRAINT_NAME,
--   COLUMN_NAME,
--   REFERENCED_TABLE_NAME,
--   REFERENCED_COLUMN_NAME
-- FROM information_schema.KEY_COLUMN_USAGE
-- WHERE TABLE_NAME = 'activos_fotos'
--   AND TABLE_SCHEMA = 'jerosmart_activos'
--   AND REFERENCED_TABLE_NAME IS NOT NULL;


-- ================================================================================
-- EJEMPLOS DE INSERCIÓN (COMENTADOS - Solo para referencia)
-- ================================================================================

/*
-- Ejemplo 1: Insertar hoja de vida para un equipo TIC
INSERT INTO hojas_vida_equipos (
  activo_id,
  proveedor_nombre,
  fecha_adquisicion,
  costo_adquisicion,
  voltaje,
  caracteristicas_especificas_json,
  created_by
) VALUES (
  123, -- ID del activo
  'TechnoPC Colombia SAS',
  '2024-01-15',
  3500000.00,
  '110V',
  JSON_OBJECT(
    'sistema_operativo', 'Windows 11 Pro',
    'procesador', 'Intel Core i7',
    'ram', '16GB DDR4',
    'disco', '512GB SSD'
  ),
  1 -- ID del usuario
);

-- Ejemplo 2: Insertar foto de un activo
INSERT INTO activos_fotos (
  activo_id,
  nombre_archivo,
  ruta_archivo,
  tipo_foto,
  descripcion,
  orden,
  uploaded_by
) VALUES (
  123, -- ID del activo
  'computador_123_frontal.jpg',
  'uploads/activos/123/computador_123_frontal.jpg',
  'frontal',
  'Vista frontal del equipo de cómputo',
  1, -- Primera foto
  1 -- ID del usuario
);
*/


-- ================================================================================
-- FIN DEL SCRIPT
-- ================================================================================
-- Total de tablas creadas: 2
-- 1. hojas_vida_equipos (Hojas de vida para equipos no biomédicos)
-- 2. activos_fotos (Galería de fotografías por activo)
-- ================================================================================
