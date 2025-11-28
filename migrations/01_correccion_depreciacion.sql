-- ============================================================================
-- MIGRACIÓN: Corrección del sistema de depreciación para activos legacy
-- Fecha: 2025-11-25
-- Descripción: Agrega campos necesarios para calcular depreciación correcta
--              de activos migrados de sistemas anteriores
-- ============================================================================

USE jerosmart_activos;

-- PASO 1: Agregar columnas nuevas
-- ============================================================================
ALTER TABLE activos
ADD COLUMN fecha_adquisicion DATE NULL COMMENT 'Fecha real de compra/adquisición del activo' AFTER created_at,
ADD COLUMN depreciacion_acumulada_historica DECIMAL(15,2) DEFAULT 0 COMMENT 'Depreciación acumulada al momento de migrar al sistema' AFTER valor_comercial,
ADD COLUMN es_activo_legacy BOOLEAN DEFAULT FALSE COMMENT 'Indica si el activo fue migrado de sistema anterior' AFTER tipo_propiedad,
ADD COLUMN metodo_depreciacion ENUM('linea_recta', 'unidades_produccion', 'saldos_decrecientes', 'manual', 'totalmente_depreciado') DEFAULT 'linea_recta' AFTER depreciacion_acumulada_historica,
ADD COLUMN valor_residual DECIMAL(15,2) DEFAULT 0 COMMENT 'Valor residual estimado al final de vida útil' AFTER metodo_depreciacion,
ADD COLUMN vida_util_restante_meses INT NULL COMMENT 'Meses de vida útil restante (NULL = calcular automáticamente)' AFTER valor_residual,
ADD COLUMN observaciones_depreciacion TEXT NULL COMMENT 'Notas sobre cálculo de depreciación o situaciones especiales' AFTER vida_util_restante_meses;

-- PASO 2: Crear índices para optimizar consultas
-- ============================================================================
CREATE INDEX idx_activos_fecha_adquisicion ON activos(fecha_adquisicion);
CREATE INDEX idx_activos_es_legacy ON activos(es_activo_legacy);
CREATE INDEX idx_activos_metodo_depreciacion ON activos(metodo_depreciacion);

-- PASO 3: Inicializar datos para activos existentes
-- ============================================================================

-- 3.1 Marcar todos los activos actuales como legacy
UPDATE activos
SET es_activo_legacy = TRUE,
    fecha_adquisicion = created_at,
    observaciones_depreciacion = CONCAT(
        IFNULL(observaciones_depreciacion, ''),
        IF(observaciones_depreciacion IS NOT NULL, ' | ', ''),
        'MIGRADO: Fecha de adquisición inicializada con fecha de registro en sistema'
    )
WHERE fecha_adquisicion IS NULL;

-- 3.2 Identificar activos con más de 10 años (totalmente depreciados)
UPDATE activos
SET metodo_depreciacion = 'totalmente_depreciado',
    depreciacion_acumulada_historica = valor_comercial,
    valor_residual = 0,
    vida_util_restante_meses = 0,
    observaciones_depreciacion = CONCAT(
        IFNULL(observaciones_depreciacion, ''),
        IF(observaciones_depreciacion IS NOT NULL, ' | ', ''),
        'ACTIVO TOTALMENTE DEPRECIADO - Vida útil superada (>10 años)'
    )
WHERE TIMESTAMPDIFF(YEAR, created_at, NOW()) >= 10
  AND metodo_depreciacion != 'totalmente_depreciado';

-- 3.3 Para equipos TICs (clase_id = 3) con más de 5 años
UPDATE activos
SET metodo_depreciacion = 'totalmente_depreciado',
    depreciacion_acumulada_historica = valor_comercial,
    valor_residual = 0,
    vida_util_restante_meses = 0,
    observaciones_depreciacion = CONCAT(
        IFNULL(observaciones_depreciacion, ''),
        IF(observaciones_depreciacion IS NOT NULL, ' | ', ''),
        'ACTIVO TOTALMENTE DEPRECIADO - TICs con vida útil superada (>5 años)'
    )
WHERE clase_id = 3
  AND TIMESTAMPDIFF(YEAR, created_at, NOW()) >= 5
  AND metodo_depreciacion != 'totalmente_depreciado';

-- PASO 4: Crear vista para cálculo correcto de valoración
-- ============================================================================
CREATE OR REPLACE VIEW vista_activos_valoracion AS
SELECT
    a.id,
    a.placa_codigo_interno,
    a.nombre_activo,
    a.marca,
    a.modelo,
    a.valor_comercial,
    a.fecha_adquisicion,
    a.depreciacion_acumulada_historica,
    a.metodo_depreciacion,
    a.es_activo_legacy,

    -- Cálculo de depreciación según método
    CASE
        WHEN a.metodo_depreciacion = 'totalmente_depreciado' THEN
            a.valor_comercial

        WHEN a.metodo_depreciacion = 'manual' THEN
            a.depreciacion_acumulada_historica

        WHEN a.metodo_depreciacion = 'linea_recta' AND a.fecha_adquisicion IS NOT NULL THEN
            CASE
                -- Equipos TICs (vida útil 5 años)
                WHEN a.clase_id = 3 THEN
                    LEAST(a.valor_comercial, (a.valor_comercial / 5) * (TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())))

                -- Equipos Biomédicos (obtener de JSON o default 10 años)
                WHEN a.clase_id = 1 THEN
                    LEAST(a.valor_comercial,
                        (a.valor_comercial / COALESCE(JSON_UNQUOTE(JSON_EXTRACT(a.atributos_dinamicos_json, '$.vida_util')), 10)) *
                        (TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW()))
                    )

                -- Otros activos (vida útil 10 años)
                ELSE
                    LEAST(a.valor_comercial, (a.valor_comercial / 10) * (TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())))
            END

        ELSE
            a.depreciacion_acumulada_historica
    END AS depreciacion_acumulada,

    -- Valor en libros
    a.valor_comercial - (
        CASE
            WHEN a.metodo_depreciacion = 'totalmente_depreciado' THEN
                a.valor_comercial

            WHEN a.metodo_depreciacion = 'manual' THEN
                a.depreciacion_acumulada_historica

            WHEN a.metodo_depreciacion = 'linea_recta' AND a.fecha_adquisicion IS NOT NULL THEN
                CASE
                    WHEN a.clase_id = 3 THEN
                        LEAST(a.valor_comercial, (a.valor_comercial / 5) * (TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())))
                    WHEN a.clase_id = 1 THEN
                        LEAST(a.valor_comercial,
                            (a.valor_comercial / COALESCE(JSON_UNQUOTE(JSON_EXTRACT(a.atributos_dinamicos_json, '$.vida_util')), 10)) *
                            (TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW()))
                        )
                    ELSE
                        LEAST(a.valor_comercial, (a.valor_comercial / 10) * (TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW())))
                END
            ELSE
                a.depreciacion_acumulada_historica
        END
    ) AS valor_libros,

    a.estado,
    a.ubicacion,
    f.nombres AS responsable_nombres,
    f.apellidos AS responsable_apellidos,
    CONCAT(f.nombres, ' ', f.apellidos) AS responsable_completo,
    c.nombre_clase AS clase

FROM activos a
LEFT JOIN funcionarios f ON a.funcionario_id = f.id
LEFT JOIN clases_activo c ON a.clase_id = c.id;

-- PASO 5: Verificación de resultados
-- ============================================================================
SELECT
    'RESUMEN DE MIGRACIÓN' AS seccion,
    COUNT(*) AS total_activos,
    SUM(CASE WHEN es_activo_legacy = TRUE THEN 1 ELSE 0 END) AS activos_legacy,
    SUM(CASE WHEN metodo_depreciacion = 'totalmente_depreciado' THEN 1 ELSE 0 END) AS totalmente_depreciados,
    SUM(CASE WHEN fecha_adquisicion IS NOT NULL THEN 1 ELSE 0 END) AS con_fecha_adquisicion
FROM activos;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================

-- ROLLBACK (si necesitas revertir):
/*
ALTER TABLE activos
DROP COLUMN fecha_adquisicion,
DROP COLUMN depreciacion_acumulada_historica,
DROP COLUMN es_activo_legacy,
DROP COLUMN metodo_depreciacion,
DROP COLUMN valor_residual,
DROP COLUMN vida_util_restante_meses,
DROP COLUMN observaciones_depreciacion;

DROP VIEW IF EXISTS vista_activos_valoracion;
*/
