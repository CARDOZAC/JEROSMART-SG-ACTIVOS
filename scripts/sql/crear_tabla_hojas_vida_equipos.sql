-- ================================================================================
-- SQL para crear la tabla faltante: hojas_vida_equipos
-- Base de datos: jerosmart_activos
-- Generado por: Claude Code - Profesional en Activos Fijos Clínicos
-- Fecha: 2025-11-28
-- ================================================================================

-- Tabla para hojas de vida de equipos no biomédicos (TICs, Mobiliario, Industriales)
DROP TABLE IF EXISTS `hojas_vida_equipos`;

CREATE TABLE `hojas_vida_equipos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `activo_id` INT NOT NULL,

  -- Características Comerciales
  `proveedor_nombre` VARCHAR(255) DEFAULT NULL,
  `fecha_adquisicion` DATE DEFAULT NULL,
  `costo_adquisicion` DECIMAL(15, 2) DEFAULT NULL,
  `numero_factura` VARCHAR(100) DEFAULT NULL,
  `numero_orden_compra` VARCHAR(100) DEFAULT NULL,
  `garantia_meses` INT DEFAULT NULL,
  `fecha_vencimiento_garantia` DATE DEFAULT NULL,
  `vida_util_anios` INT DEFAULT NULL,

  -- Características Técnicas Generales
  `voltaje` VARCHAR(50) DEFAULT NULL,
  `potencia` VARCHAR(50) DEFAULT NULL,
  `corriente` VARCHAR(50) DEFAULT NULL,
  `frecuencia` VARCHAR(50) DEFAULT NULL,
  `dimensiones` VARCHAR(100) DEFAULT NULL,
  `peso` VARCHAR(50) DEFAULT NULL,
  `color` VARCHAR(50) DEFAULT NULL,
  `material` VARCHAR(100) DEFAULT NULL,

  -- Documentación Técnica
  `manual_usuario` TINYINT(1) DEFAULT 0,
  `manual_servicio` TINYINT(1) DEFAULT 0,
  `manual_instalacion` TINYINT(1) DEFAULT 0,

  -- Características Específicas (JSON para flexibilidad según tipo de equipo)
  -- Para TICs: sistema_operativo, procesador, ram, disco, tipo_equipo
  -- Para Electro-Industrial: capacidad, tipo_combustible, tipo_motor, tipo_refrigerante
  -- Para Muebles: tipo_mueble, numero_cajones, acabado, tapiceria
  `caracteristicas_especificas_json` JSON DEFAULT NULL,

  -- Observaciones y Notas
  `observaciones_tecnicas` TEXT DEFAULT NULL,
  `condiciones_uso` TEXT DEFAULT NULL,
  `restricciones` TEXT DEFAULT NULL,

  -- Fotos del equipo (hasta 3 fotos)
  `foto_url` VARCHAR(255) DEFAULT NULL,
  `foto_2_url` VARCHAR(255) DEFAULT NULL,
  `foto_3_url` VARCHAR(255) DEFAULT NULL,

  -- Auditoría
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  `updated_by` INT DEFAULT NULL,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_activo_id` (`activo_id`),

  -- Relaciones
  CONSTRAINT `fk_hoja_vida_equipo_activo`
    FOREIGN KEY (`activo_id`)
    REFERENCES `activos` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT `fk_hoja_vida_equipo_creator`
    FOREIGN KEY (`created_by`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  CONSTRAINT `fk_hoja_vida_equipo_updater`
    FOREIGN KEY (`updated_by`)
    REFERENCES `usuarios` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  -- Índices para optimización
  INDEX `idx_hoja_vida_equipo_activo` (`activo_id`),
  INDEX `idx_hoja_vida_equipo_created_at` (`created_at`),
  INDEX `idx_hoja_vida_equipo_updated_at` (`updated_at`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Hojas de vida para equipos no biomédicos (TICs, Mobiliario, Equipos Industriales)';

-- ================================================================================
-- Verificación
-- ================================================================================
SELECT 'Tabla hojas_vida_equipos creada exitosamente' AS resultado;

-- Para verificar la estructura:
-- DESCRIBE hojas_vida_equipos;

-- Para verificar las relaciones:
-- SHOW CREATE TABLE hojas_vida_equipos;
