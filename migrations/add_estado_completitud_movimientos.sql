-- ============================================================================
-- MIGRACIÓN: Agregar campo de estado de completitud a movimientos
-- Fecha: 2025-11-18
-- Descripción: Permite guardar movimientos incompletos como borradores
-- ============================================================================

-- Seleccionar la base de datos
USE jerosmart_activos;

-- ============================================================================
-- PASO 1: Agregar columna estado_completitud a la tabla movimientos
-- ============================================================================
ALTER TABLE movimientos
ADD COLUMN estado_completitud VARCHAR(20) NOT NULL DEFAULT 'completo'
COMMENT 'Estado del movimiento: borrador, completo';

-- ============================================================================
-- PASO 2: Agregar índice para mejorar consultas filtradas por estado
-- ============================================================================
CREATE INDEX idx_movimientos_estado_completitud ON movimientos(estado_completitud);

-- ============================================================================
-- PASO 3: Hacer que el campo 'motivo' en detalles_entrada_salida sea nullable
-- ============================================================================
ALTER TABLE detalles_entrada_salida
MODIFY COLUMN motivo TEXT NULL
COMMENT 'Motivo de la entrada/salida (puede ser NULL si está en borrador)';

-- ============================================================================
-- PASO 4: Hacer otros campos opcionales en detalles_entrada_salida para borradores
-- ============================================================================
ALTER TABLE detalles_entrada_salida
MODIFY COLUMN ciudad VARCHAR(100) NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN sede VARCHAR(100) NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN solicitante_responsable_nombre VARCHAR(150) NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN solicitante_responsable_cc VARCHAR(50) NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN tipo_operacion VARCHAR(20) NULL
COMMENT 'Tipo de operación: Entrada o Salida (puede ser NULL si está en borrador)';

-- ============================================================================
-- PASO 5: Verificar cambios realizados
-- ============================================================================
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    IS_NULLABLE,
    COLUMN_TYPE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'jerosmart_activos'
  AND TABLE_NAME IN ('movimientos', 'detalles_entrada_salida')
  AND COLUMN_NAME IN ('estado_completitud', 'motivo', 'tipo_operacion', 'ciudad', 'sede')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- ============================================================================
-- PASO 6 (OPCIONAL): Convertir movimientos existentes a "completo"
-- ============================================================================
-- Solo ejecutar si tienes movimientos existentes sin estado_completitud
UPDATE movimientos
SET estado_completitud = 'completo'
WHERE estado_completitud IS NULL
   OR estado_completitud = '';

-- ============================================================================
-- PASO 7: Verificar resultado final
-- ============================================================================
SELECT
    estado_completitud,
    COUNT(*) as total_movimientos
FROM movimientos
GROUP BY estado_completitud;

SELECT
    'Migración completada exitosamente' AS STATUS,
    NOW() AS TIMESTAMP;

-- ============================================================================
-- ROLLBACK (en caso de necesitar revertir)
-- ============================================================================
/*
-- Para revertir esta migración, ejecuta los siguientes comandos:

USE jerosmart_activos;

-- Eliminar columna
ALTER TABLE movimientos DROP COLUMN estado_completitud;

-- Eliminar índice
DROP INDEX idx_movimientos_estado_completitud ON movimientos;

-- Volver motivo a NOT NULL
ALTER TABLE detalles_entrada_salida
MODIFY COLUMN motivo TEXT NOT NULL;

-- Volver tipo_operacion a NOT NULL
ALTER TABLE detalles_entrada_salida
MODIFY COLUMN tipo_operacion VARCHAR(20) NOT NULL;

-- Volver otros campos a NOT NULL
ALTER TABLE detalles_entrada_salida
MODIFY COLUMN ciudad VARCHAR(100) NOT NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN sede VARCHAR(100) NOT NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN solicitante_responsable_nombre VARCHAR(150) NOT NULL;

ALTER TABLE detalles_entrada_salida
MODIFY COLUMN solicitante_responsable_cc VARCHAR(50) NOT NULL;

SELECT 'Rollback completado' AS STATUS;
*/
