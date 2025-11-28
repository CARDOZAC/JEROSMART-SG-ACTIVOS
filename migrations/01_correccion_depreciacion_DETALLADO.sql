-- ============================================================================
-- MIGRACIÓN CRÍTICA: Sistema de Depreciación Correcto para Activos Legacy
-- ============================================================================
-- Fecha: 2025-11-25
-- Autor: Sistema JeroSmart
-- Base de datos: jerosmart_activos (MySQL 8.0+)
--
-- PROPÓSITO:
-- Este script agrega las columnas necesarias para calcular correctamente la
-- depreciación de activos que fueron migrados desde sistemas anteriores.
--
-- PROBLEMA QUE RESUELVE:
-- Los activos legacy tienen `created_at` = fecha de migración (2024), pero
-- fueron comprados hace 10+ años. Esto causa que aparezcan como "nuevos"
-- cuando en realidad están totalmente depreciados.
--
-- COLUMNAS CRÍTICAS QUE SE AGREGAN:
-- 1. fecha_adquisicion       → Fecha REAL de compra (formato: YYYY-MM-DD)
-- 2. fecha_alta_sistema      → Fecha de registro en JeroSmart
-- 3. costo_historico         → Valor original de compra
-- 4. depreciacion_acumulada_historica → Depreciación antes de migrar
-- 5. es_activo_legacy        → Marca si fue migrado (TRUE/FALSE)
--
-- IMPORTANTE: Este script es IDEMPOTENTE (se puede ejecutar múltiples veces)
-- ============================================================================

USE jerosmart_activos;

-- ============================================================================
-- PASO 1: AGREGAR COLUMNAS CRÍTICAS PARA DEPRECIACIÓN CORRECTA
-- ============================================================================

-- Verificar si las columnas ya existen (evitar error si se ejecuta dos veces)
SET @dbname = 'jerosmart_activos';
SET @tablename = 'activos';

-- Agregar columnas una por una con verificación

-- 1️⃣ FECHA_ADQUISICION (⭐ CAMPO MÁS CRÍTICO)
-- ============================================================================
-- Formato esperado: 'YYYY-MM-DD' (Ejemplo: '2015-03-15')
-- Descripción: Fecha REAL en que se compró/adquirió el activo
-- Uso: Para calcular años transcurridos y depreciación acumulada
-- Nullable: SÍ (puede ser NULL para activos sin fecha conocida)
-- ============================================================================
SELECT CONCAT('Agregando columna: fecha_adquisicion...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'fecha_adquisicion'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN fecha_adquisicion DATE NULL
    COMMENT "Fecha real de compra/adquisición (formato: YYYY-MM-DD, ej: 2015-03-15)"
    AFTER created_at',
    'SELECT "La columna fecha_adquisicion ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2️⃣ FECHA_ALTA_SISTEMA
-- ============================================================================
-- Formato esperado: 'YYYY-MM-DD' (Ejemplo: '2024-11-20')
-- Descripción: Fecha en que el activo se registró en JeroSmart
-- Uso: Para diferenciar entre fecha de compra y fecha de registro
-- Nullable: SÍ (se puede calcular automáticamente de created_at)
-- ============================================================================
SELECT CONCAT('Agregando columna: fecha_alta_sistema...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'fecha_alta_sistema'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN fecha_alta_sistema DATE NULL
    COMMENT "Fecha de registro en sistema JeroSmart (formato: YYYY-MM-DD)"
    AFTER fecha_adquisicion',
    'SELECT "La columna fecha_alta_sistema ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3️⃣ COSTO_HISTORICO (⭐ CAMPO CRÍTICO PARA CONTABILIDAD)
-- ============================================================================
-- Formato: DECIMAL(15,2) (Ejemplo: 125000000.00 = $125 millones COP)
-- Descripción: Valor ORIGINAL de compra del activo (puede diferir de valor_comercial)
-- Uso: Base para calcular depreciación
-- Nullable: SÍ (si es NULL, se usa valor_comercial)
-- Rango válido: 0.00 a 999,999,999,999.99
-- ============================================================================
SELECT CONCAT('Agregando columna: costo_historico...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'costo_historico'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN costo_historico DECIMAL(15,2) NULL
    COMMENT "Valor original de compra/adquisición (COP, ej: 125000000.00)"
    AFTER valor_comercial',
    'SELECT "La columna costo_historico ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4️⃣ DEPRECIACION_ACUMULADA_HISTORICA (⭐ CAMPO CRÍTICO)
-- ============================================================================
-- Formato: DECIMAL(15,2) (Ejemplo: 75000000.00)
-- Descripción: Depreciación acumulada ANTES de migrar al sistema JeroSmart
-- Uso: Para activos legacy que ya traen depreciación de sistemas anteriores
-- Default: 0.00 (para activos nuevos registrados en JeroSmart)
-- Nullable: NO (siempre tiene valor, mínimo 0)
-- ============================================================================
SELECT CONCAT('Agregando columna: depreciacion_acumulada_historica...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'depreciacion_acumulada_historica'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN depreciacion_acumulada_historica DECIMAL(15,2) DEFAULT 0.00
    COMMENT "Depreciación acumulada al migrar (COP, ej: 75000000.00)"
    AFTER costo_historico',
    'SELECT "La columna depreciacion_acumulada_historica ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5️⃣ ES_ACTIVO_LEGACY (⭐ MARCA CRÍTICA)
-- ============================================================================
-- Formato: BOOLEAN (TRUE/FALSE o 1/0)
-- Descripción: Indica si el activo fue migrado de sistema anterior
-- Valores válidos:
--   TRUE (1)  = Activo migrado de sistema anterior
--   FALSE (0) = Activo registrado directamente en JeroSmart
-- Default: FALSE
-- ============================================================================
SELECT CONCAT('Agregando columna: es_activo_legacy...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'es_activo_legacy'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN es_activo_legacy BOOLEAN DEFAULT FALSE
    COMMENT "TRUE=Migrado de sistema anterior | FALSE=Registrado en JeroSmart"
    AFTER tipo_propiedad',
    'SELECT "La columna es_activo_legacy ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6️⃣ METODO_DEPRECIACION
-- ============================================================================
-- Formato: ENUM (valores específicos permitidos)
-- Valores permitidos:
--   'linea_recta'          = Depreciación lineal estándar
--   'unidades_produccion'  = Por uso/producción
--   'saldos_decrecientes'  = Acelerada
--   'manual'               = Cálculo manual (ej: activos especiales)
--   'totalmente_depreciado'= Activo con valor en libros = 0
-- Default: 'linea_recta'
-- ============================================================================
SELECT CONCAT('Agregando columna: metodo_depreciacion...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'metodo_depreciacion'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN metodo_depreciacion
    ENUM("linea_recta", "unidades_produccion", "saldos_decrecientes", "manual", "totalmente_depreciado")
    DEFAULT "linea_recta"
    COMMENT "Método de cálculo de depreciación aplicado"
    AFTER depreciacion_acumulada_historica',
    'SELECT "La columna metodo_depreciacion ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 7️⃣ VALOR_RESIDUAL
-- ============================================================================
-- Formato: DECIMAL(15,2) (Ejemplo: 5000000.00)
-- Descripción: Valor estimado del activo al final de su vida útil
-- Uso: Para cálculos contables y baja de activos
-- Default: 0.00 (la mayoría de activos tienen valor residual = 0)
-- ============================================================================
SELECT CONCAT('Agregando columna: valor_residual...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'valor_residual'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN valor_residual DECIMAL(15,2) DEFAULT 0.00
    COMMENT "Valor residual al final de vida útil (COP)"
    AFTER metodo_depreciacion',
    'SELECT "La columna valor_residual ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 8️⃣ VIDA_UTIL_RESTANTE_MESES
-- ============================================================================
-- Formato: INT (Ejemplo: 36 = 3 años restantes)
-- Descripción: Meses de vida útil que le quedan al activo
-- Nullable: SÍ (NULL = calcular automáticamente)
-- Rango válido: 0 a 600 (0 a 50 años)
-- ============================================================================
SELECT CONCAT('Agregando columna: vida_util_restante_meses...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'vida_util_restante_meses'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN vida_util_restante_meses INT NULL
    COMMENT "Meses de vida útil restante (NULL=calcular automático)"
    AFTER valor_residual',
    'SELECT "La columna vida_util_restante_meses ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 9️⃣ OBSERVACIONES_DEPRECIACION
-- ============================================================================
-- Formato: TEXT (texto largo, sin límite práctico)
-- Descripción: Notas sobre situaciones especiales de depreciación
-- Ejemplos de uso:
--   - "Activo totalmente depreciado pero operativo"
--   - "Depreciación ajustada por revaluación 2023"
--   - "Valor histórico estimado por pérdida de factura"
-- Nullable: SÍ
-- ============================================================================
SELECT CONCAT('Agregando columna: observaciones_depreciacion...') AS paso;

SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = 'observaciones_depreciacion'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE activos ADD COLUMN observaciones_depreciacion TEXT NULL
    COMMENT "Notas sobre cálculo de depreciación o situaciones especiales"
    AFTER vida_util_restante_meses',
    'SELECT "La columna observaciones_depreciacion ya existe" AS resultado'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- PASO 2: CREAR ÍNDICES PARA OPTIMIZAR CONSULTAS
-- ============================================================================
SELECT CONCAT('Creando índices...') AS paso;

-- Índice para búsquedas por fecha de adquisición
-- Nota: Si el índice ya existe, ignorar el error manualmente
CREATE INDEX idx_activos_fecha_adquisicion
ON activos(fecha_adquisicion);

-- Índice para filtrar activos legacy
CREATE INDEX idx_activos_es_legacy
ON activos(es_activo_legacy);

-- Índice para filtrar por método de depreciación
CREATE INDEX idx_activos_metodo_depreciacion
ON activos(metodo_depreciacion);

-- Índice compuesto para reportes de depreciación
CREATE INDEX idx_activos_depreciacion_reporte
ON activos(es_activo_legacy, metodo_depreciacion, fecha_adquisicion);

SELECT 'Índices creados exitosamente' AS resultado;

-- ============================================================================
-- PASO 3: INICIALIZAR DATOS PARA ACTIVOS EXISTENTES
-- ============================================================================
-- Este paso migra los datos actuales a las nuevas columnas

SELECT CONCAT('Inicializando datos para activos existentes...') AS paso;

-- 3.1 Inicializar fecha_alta_sistema con created_at
-- ============================================================================
UPDATE activos
SET fecha_alta_sistema = DATE(created_at)
WHERE fecha_alta_sistema IS NULL;

SELECT CONCAT('✅ Inicializadas ', ROW_COUNT(), ' fechas de alta en sistema') AS resultado;

-- 3.2 Marcar TODOS los activos actuales como legacy
-- ============================================================================
-- RAZÓN: Todos los activos en el sistema fueron migrados desde SQLite
UPDATE activos
SET es_activo_legacy = TRUE,
    fecha_adquisicion = DATE(created_at),  -- Fecha tentativa (será corregida manualmente)
    observaciones_depreciacion = CONCAT(
        IFNULL(observaciones_depreciacion, ''),
        IF(observaciones_depreciacion IS NOT NULL, ' | ', ''),
        'MIGRADO: Fecha de adquisición inicializada con fecha de registro. VERIFICAR Y CORREGIR con fecha real de compra.'
    )
WHERE es_activo_legacy = FALSE;

SELECT CONCAT('✅ Marcados ', ROW_COUNT(), ' activos como legacy') AS resultado;

-- 3.3 Inicializar costo_historico con valor_comercial
-- ============================================================================
-- Si no se conoce el costo original, usar el valor comercial actual
UPDATE activos
SET costo_historico = valor_comercial
WHERE costo_historico IS NULL AND valor_comercial > 0;

SELECT CONCAT('✅ Inicializados ', ROW_COUNT(), ' costos históricos') AS resultado;

-- 3.4 Identificar activos con más de 10 años (TOTALMENTE DEPRECIADOS)
-- ============================================================================
-- CRITERIO: Activos registrados hace 10+ años están 100% depreciados
UPDATE activos
SET metodo_depreciacion = 'totalmente_depreciado',
    depreciacion_acumulada_historica = IFNULL(costo_historico, valor_comercial),
    valor_residual = 0,
    vida_util_restante_meses = 0,
    observaciones_depreciacion = CONCAT(
        IFNULL(observaciones_depreciacion, ''),
        IF(observaciones_depreciacion IS NOT NULL, ' | ', ''),
        'ACTIVO TOTALMENTE DEPRECIADO - Vida útil superada (>10 años desde registro en sistema). VERIFICAR estado operativo.'
    )
WHERE TIMESTAMPDIFF(YEAR, created_at, NOW()) >= 10
  AND metodo_depreciacion != 'totalmente_depreciado';

SELECT CONCAT('✅ Marcados ', ROW_COUNT(), ' activos como totalmente depreciados (>10 años)') AS resultado;

-- 3.5 Equipos TICs con más de 5 años (TOTALMENTE DEPRECIADOS)
-- ============================================================================
-- CRITERIO: TICs tienen vida útil de 5 años según NIIF
UPDATE activos
SET metodo_depreciacion = 'totalmente_depreciado',
    depreciacion_acumulada_historica = IFNULL(costo_historico, valor_comercial),
    valor_residual = 0,
    vida_util_restante_meses = 0,
    observaciones_depreciacion = CONCAT(
        IFNULL(observaciones_depreciacion, ''),
        IF(observaciones_depreciacion IS NOT NULL, ' | ', ''),
        'ACTIVO TOTALMENTE DEPRECIADO - TICs con vida útil superada (>5 años). VERIFICAR estado operativo.'
    )
WHERE clase_id = 3  -- TICs
  AND TIMESTAMPDIFF(YEAR, created_at, NOW()) >= 5
  AND metodo_depreciacion != 'totalmente_depreciado';

SELECT CONCAT('✅ Marcados ', ROW_COUNT(), ' equipos TICs como totalmente depreciados (>5 años)') AS resultado;

-- ============================================================================
-- PASO 4: CREAR VISTA PARA CÁLCULO CORRECTO DE VALORACIÓN
-- ============================================================================
SELECT CONCAT('Creando vista de valoración...') AS paso;

CREATE OR REPLACE VIEW vista_activos_valoracion AS
SELECT
    a.id,
    a.placa_codigo_interno,
    a.nombre_activo,
    a.marca,
    a.modelo,

    -- Valores base
    a.valor_comercial,
    IFNULL(a.costo_historico, a.valor_comercial) AS costo_base,
    a.fecha_adquisicion,
    a.fecha_alta_sistema,
    a.depreciacion_acumulada_historica,
    a.metodo_depreciacion,
    a.es_activo_legacy,

    -- Cálculo de años transcurridos
    CASE
        WHEN a.fecha_adquisicion IS NOT NULL THEN
            TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())
        ELSE
            NULL
    END AS anios_desde_adquisicion,

    -- Cálculo de vida útil según clase
    CASE
        WHEN a.clase_id = 3 THEN 5  -- TICs: 5 años
        WHEN a.clase_id = 1 THEN
            COALESCE(
                CAST(JSON_UNQUOTE(JSON_EXTRACT(a.atributos_dinamicos_json, '$.vida_util')) AS UNSIGNED),
                10
            )  -- Biomédicos: JSON o 10 años
        ELSE 10  -- Otros: 10 años
    END AS vida_util_anios,

    -- Cálculo de depreciación acumulada
    CASE
        -- Si está marcado como totalmente depreciado
        WHEN a.metodo_depreciacion = 'totalmente_depreciado' THEN
            IFNULL(a.costo_historico, a.valor_comercial)

        -- Si tiene depreciación manual
        WHEN a.metodo_depreciacion = 'manual' THEN
            a.depreciacion_acumulada_historica

        -- Si usa línea recta y tiene fecha de adquisición
        WHEN a.metodo_depreciacion = 'linea_recta' AND a.fecha_adquisicion IS NOT NULL THEN
            LEAST(
                IFNULL(a.costo_historico, a.valor_comercial),
                (IFNULL(a.costo_historico, a.valor_comercial) /
                    CASE
                        WHEN a.clase_id = 3 THEN 5
                        WHEN a.clase_id = 1 THEN COALESCE(
                            CAST(JSON_UNQUOTE(JSON_EXTRACT(a.atributos_dinamicos_json, '$.vida_util')) AS UNSIGNED),
                            10
                        )
                        ELSE 10
                    END
                ) * TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())
            )

        -- Fallback: usar depreciación histórica
        ELSE
            a.depreciacion_acumulada_historica
    END AS depreciacion_acumulada_calculada,

    -- Valor en libros
    IFNULL(a.costo_historico, a.valor_comercial) - (
        CASE
            WHEN a.metodo_depreciacion = 'totalmente_depreciado' THEN
                IFNULL(a.costo_historico, a.valor_comercial)
            WHEN a.metodo_depreciacion = 'manual' THEN
                a.depreciacion_acumulada_historica
            WHEN a.metodo_depreciacion = 'linea_recta' AND a.fecha_adquisicion IS NOT NULL THEN
                LEAST(
                    IFNULL(a.costo_historico, a.valor_comercial),
                    (IFNULL(a.costo_historico, a.valor_comercial) /
                        CASE
                            WHEN a.clase_id = 3 THEN 5
                            WHEN a.clase_id = 1 THEN COALESCE(
                                CAST(JSON_UNQUOTE(JSON_EXTRACT(a.atributos_dinamicos_json, '$.vida_util')) AS UNSIGNED),
                                10
                            )
                            ELSE 10
                        END
                    ) * TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())
                )
            ELSE
                a.depreciacion_acumulada_historica
        END
    ) AS valor_libros_calculado,

    -- Información adicional
    a.estado,
    a.ubicacion,
    f.nombres AS responsable_nombres,
    f.apellidos AS responsable_apellidos,
    CONCAT(f.nombres, ' ', f.apellidos) AS responsable_completo,
    c.nombre_clase AS clase,
    a.observaciones_depreciacion

FROM activos a
LEFT JOIN funcionarios f ON a.funcionario_id = f.id
LEFT JOIN clases_activo c ON a.clase_id = c.id;

SELECT '✅ Vista vista_activos_valoracion creada exitosamente' AS resultado;

-- ============================================================================
-- PASO 5: REPORTE DE VERIFICACIÓN
-- ============================================================================
SELECT '=' AS separador, 'REPORTE DE MIGRACIÓN COMPLETADA' AS titulo, '=' AS separador2;

-- Resumen general
SELECT
    '📊 RESUMEN GENERAL' AS seccion,
    COUNT(*) AS total_activos,
    SUM(CASE WHEN es_activo_legacy = TRUE THEN 1 ELSE 0 END) AS activos_legacy,
    SUM(CASE WHEN metodo_depreciacion = 'totalmente_depreciado' THEN 1 ELSE 0 END) AS totalmente_depreciados,
    SUM(CASE WHEN fecha_adquisicion IS NOT NULL THEN 1 ELSE 0 END) AS con_fecha_adquisicion,
    SUM(CASE WHEN costo_historico IS NOT NULL THEN 1 ELSE 0 END) AS con_costo_historico,
    SUM(CASE WHEN depreciacion_acumulada_historica > 0 THEN 1 ELSE 0 END) AS con_depreciacion_historica
FROM activos;

-- Resumen por método de depreciación
SELECT
    '📈 DISTRIBUCIÓN POR MÉTODO' AS seccion,
    metodo_depreciacion,
    COUNT(*) AS cantidad,
    CONCAT('$', FORMAT(SUM(IFNULL(costo_historico, valor_comercial)), 2)) AS costo_total,
    CONCAT('$', FORMAT(SUM(depreciacion_acumulada_historica), 2)) AS depreciacion_total
FROM activos
GROUP BY metodo_depreciacion
ORDER BY cantidad DESC;

-- Activos que requieren atención
SELECT
    '⚠️  ACTIVOS QUE REQUIEREN REVISIÓN' AS seccion,
    COUNT(*) AS cantidad_sin_fecha_real
FROM activos
WHERE fecha_adquisicion = fecha_alta_sistema
  AND es_activo_legacy = TRUE;

-- ============================================================================
-- PASO 6: INSTRUCCIONES POST-MIGRACIÓN
-- ============================================================================
SELECT '=' AS separador, '📝 INSTRUCCIONES POST-MIGRACIÓN' AS titulo, '=' AS separador2;

SELECT '
✅ MIGRACIÓN COMPLETADA EXITOSAMENTE

🔍 VERIFICACIONES REQUERIDAS:

1. REVISAR FECHAS DE ADQUISICIÓN:
   Los activos legacy tienen fecha_adquisicion = fecha de registro.
   Necesitas corregirlas con las fechas REALES de compra.

   Ejemplo de corrección:
   UPDATE activos
   SET fecha_adquisicion = "2015-03-15",  -- ← Formato: YYYY-MM-DD
       costo_historico = 125000000.00,    -- ← COP
       observaciones_depreciacion = "Fecha corregida según factura #12345"
   WHERE placa_codigo_interno = "AFX-001";

2. REVISAR COSTOS HISTÓRICOS:
   Algunos activos tienen costo_historico = valor_comercial.
   Corrige con valores reales de factura si los tienes.

3. ACTIVOS TOTALMENTE DEPRECIADOS:
   Revisa los activos marcados como "totalmente_depreciado".
   Si están operativos, agrega nota en observaciones_depreciacion.

4. ACTUALIZAR MODELO PYTHON:
   Edita app/models.py para agregar los nuevos campos.
   Ver: PLAN_DE_ACCION.md → Tarea 1.3

📊 REPORTES DISPONIBLES:

   -- Ver todos los activos con valoración correcta:
   SELECT * FROM vista_activos_valoracion LIMIT 10;

   -- Ver activos que necesitan corrección de fecha:
   SELECT placa_codigo_interno, nombre_activo, fecha_adquisicion, fecha_alta_sistema
   FROM activos
   WHERE fecha_adquisicion = fecha_alta_sistema AND es_activo_legacy = TRUE
   LIMIT 20;

   -- Ver totales por clase:
   SELECT clase, COUNT(*), SUM(valor_libros_calculado) AS valor_total
   FROM vista_activos_valoracion
   GROUP BY clase;

🎯 PRÓXIMOS PASOS:
   1. Ejecutar: migrations/02_sistema_ingreso_rapido_legacy.sql
   2. Actualizar: app/models.py
   3. Reiniciar aplicación Flask
   4. Probar eliminación de activos (debería funcionar)

📚 DOCUMENTACIÓN:
   - Análisis completo: ANALISIS_COMPLETO_SISTEMA.md
   - Plan detallado: PLAN_DE_ACCION.md
   - Resumen: RESUMEN_EJECUTIVO.md

' AS instrucciones;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================

SELECT '
🎉 MIGRACIÓN FINALIZADA CORRECTAMENTE

Las columnas críticas han sido agregadas:
✅ fecha_adquisicion (DATE, formato: YYYY-MM-DD)
✅ fecha_alta_sistema (DATE)
✅ costo_historico (DECIMAL, formato: 125000000.00)
✅ depreciacion_acumulada_historica (DECIMAL)
✅ es_activo_legacy (BOOLEAN: TRUE/FALSE)
✅ metodo_depreciacion (ENUM)
✅ valor_residual (DECIMAL)
✅ vida_util_restante_meses (INT)
✅ observaciones_depreciacion (TEXT)

Puedes consultar el estado con:
SELECT * FROM vista_activos_valoracion LIMIT 10;

' AS mensaje_final;

-- ============================================================================
-- ROLLBACK (Solo si necesitas revertir la migración)
-- ============================================================================
-- ⚠️ PELIGRO: Esto eliminará las columnas y la vista
-- Descomenta solo si necesitas deshacer la migración
/*
ALTER TABLE activos
DROP COLUMN IF EXISTS fecha_adquisicion,
DROP COLUMN IF EXISTS fecha_alta_sistema,
DROP COLUMN IF EXISTS costo_historico,
DROP COLUMN IF EXISTS depreciacion_acumulada_historica,
DROP COLUMN IF EXISTS es_activo_legacy,
DROP COLUMN IF EXISTS metodo_depreciacion,
DROP COLUMN IF EXISTS valor_residual,
DROP COLUMN IF EXISTS vida_util_restante_meses,
DROP COLUMN IF EXISTS observaciones_depreciacion;

DROP VIEW IF EXISTS vista_activos_valoracion;

SELECT '⚠️ MIGRACIÓN REVERTIDA' AS resultado;
*/
