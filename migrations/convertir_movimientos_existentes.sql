-- ============================================================================
-- SCRIPT OPCIONAL: Convertir movimientos existentes a estado "completo"
-- Ejecutar DESPUÉS de aplicar la migración principal
-- ============================================================================

-- Este script actualiza todos los movimientos existentes que no tienen
-- estado_completitud definido y los marca como "completo"

-- Ver cuántos movimientos hay sin estado definido
SELECT
    COUNT(*) as movimientos_sin_estado
FROM movimientos
WHERE estado_completitud IS NULL
   OR estado_completitud = ''
   OR estado_completitud NOT IN ('borrador', 'completo');

-- Actualizar todos a "completo" (asumiendo que ya están completos)
UPDATE movimientos
SET estado_completitud = 'completo'
WHERE estado_completitud IS NULL
   OR estado_completitud = ''
   OR estado_completitud NOT IN ('borrador', 'completo');

-- Verificar resultado
SELECT
    estado_completitud,
    COUNT(*) as total
FROM movimientos
GROUP BY estado_completitud;

-- Resultado esperado:
-- +---------------------+-------+
-- | estado_completitud  | total |
-- +---------------------+-------+
-- | completo            |   XXX |
-- +---------------------+-------+
