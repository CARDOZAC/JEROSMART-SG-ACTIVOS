-- Migración: Agregar columnas temporales a la tabla activos
-- Fecha: 2025-01-27
-- Descripción: Agregar soporte para activos de ingreso temporal

-- Agregar columnas para manejo de ingresos temporales
ALTER TABLE activos
ADD COLUMN es_ingreso_temporal TINYINT(1) DEFAULT 0 NULL COMMENT 'Indica si el activo es un ingreso temporal',
ADD COLUMN fecha_inicio_temporal DATETIME NULL COMMENT 'Fecha de inicio del ingreso temporal',
ADD COLUMN fecha_fin_temporal DATETIME NULL COMMENT 'Fecha de fin del ingreso temporal';

-- Verificar que las columnas se agregaron correctamente
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'activos'
  AND COLUMN_NAME IN ('es_ingreso_temporal', 'fecha_inicio_temporal', 'fecha_fin_temporal');
