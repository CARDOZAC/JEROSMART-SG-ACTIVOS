-- ============================================================================
-- MIGRACIÓN: Agregar campo estado a la tabla funcionarios
-- Fecha: 2025-11-19
-- Descripción: Agrega columna 'estado' para marcar funcionarios activos/inactivos
-- ============================================================================

USE jerosmart_activos;

-- ============================================================================
-- PASO 1: Agregar columna estado a la tabla funcionarios
-- ============================================================================
ALTER TABLE funcionarios
ADD COLUMN estado VARCHAR(50) NOT NULL DEFAULT 'Activo'
COMMENT 'Estado del funcionario: Activo, Inactivo, Desvinculado';

-- ============================================================================
-- PASO 2: Agregar índice para mejorar consultas filtradas por estado
-- ============================================================================
CREATE INDEX idx_funcionarios_estado ON funcionarios(estado);

-- ============================================================================
-- PASO 3: Actualizar funcionarios existentes a estado 'Activo'
-- ============================================================================
UPDATE funcionarios
SET estado = 'Activo'
WHERE estado IS NULL OR estado = '';

-- ============================================================================
-- PASO 4: Verificar cambios realizados
-- ============================================================================
SELECT
    COLUMN_NAME,
    IS_NULLABLE,
    COLUMN_TYPE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'jerosmart_activos'
  AND TABLE_NAME = 'funcionarios'
  AND COLUMN_NAME = 'estado';

-- ============================================================================
-- PASO 5: Verificar resultado final
-- ============================================================================
SELECT
    estado,
    COUNT(*) as total_funcionarios
FROM funcionarios
GROUP BY estado;

SELECT
    'Migración completada exitosamente' AS STATUS,
    NOW() AS TIMESTAMP;

-- ============================================================================
-- ROLLBACK (en caso de necesitar revertir)
-- ============================================================================
/*
-- Para revertir esta migración, ejecuta los siguientes comandos:

USE jerosmart_activos;

-- Eliminar índice
DROP INDEX idx_funcionarios_estado ON funcionarios;

-- Eliminar columna
ALTER TABLE funcionarios DROP COLUMN estado;

SELECT 'Rollback completado' AS STATUS;
*/
