-- ============================================================================
-- MIGRACIÓN: Agregar columna 'estado' a tabla 'funcionarios'
-- Fecha: 2025-11-21
-- Autor: Sistema JeroSmart
-- Razón: Sincronizar base de datos MySQL con modelo Python Funcionario
-- ============================================================================

-- Verificar que no exista la columna (comentar si ya existe)
-- SELECT COLUMN_NAME
-- FROM information_schema.COLUMNS
-- WHERE TABLE_SCHEMA = DATABASE()
-- AND TABLE_NAME = 'funcionarios'
-- AND COLUMN_NAME = 'estado';

-- [1/2] Agregar columna 'estado' con valor por defecto 'Activo'
ALTER TABLE funcionarios
ADD COLUMN estado VARCHAR(50) NOT NULL DEFAULT 'Activo'
AFTER centro_costo;

-- [2/2] Crear índice para optimizar consultas por estado
CREATE INDEX idx_funcionarios_estado
ON funcionarios(estado);

-- Verificar que la migración fue exitosa
SELECT
    COUNT(*) as total_funcionarios,
    SUM(CASE WHEN estado = 'Activo' THEN 1 ELSE 0 END) as funcionarios_activos
FROM funcionarios;

-- ============================================================================
-- MIGRACIÓN COMPLETADA
-- ============================================================================
-- Todos los funcionarios existentes ahora tienen estado = 'Activo' por defecto
-- El índice optimiza las consultas que filtran por estado
-- ============================================================================

-- ROLLBACK (en caso de necesitar revertir):
-- DROP INDEX idx_funcionarios_estado ON funcionarios;
-- ALTER TABLE funcionarios DROP COLUMN estado;
