-- ============================================================================
-- MIGRACIÓN: Sistema de ingreso rápido para activos legacy
-- Fecha: 2025-11-25
-- Descripción: Crea infraestructura para registrar activos encontrados
--              que no están en el sistema y requieren investigación
-- ============================================================================

USE jerosmart_activos;

-- PASO 1: Crear tabla para activos en investigación
-- ============================================================================
CREATE TABLE IF NOT EXISTS activos_legacy_temporal (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Identificación básica (campos mínimos requeridos)
    placa_codigo_interno VARCHAR(100) NOT NULL COMMENT 'Placa o código del activo encontrado',
    nombre_activo VARCHAR(200) NOT NULL COMMENT 'Nombre o descripción del activo',
    marca VARCHAR(100) NULL,
    modelo VARCHAR(100) NULL,
    serie VARCHAR(100) NULL,
    ubicacion VARCHAR(200) NOT NULL COMMENT 'Dónde se encontró el activo',

    -- Clasificación inicial
    clase_id INT NULL COMMENT 'Clasificación tentativa del activo',

    -- Estado físico
    estado_fisico ENUM('Operativo', 'Requiere Mantenimiento', 'Inoperativo', 'Desconocido') DEFAULT 'Desconocido',
    anios_uso_estimado INT NULL COMMENT 'Años aproximados de uso (estimación visual)',

    -- Valoración estimada
    valor_estimado_actual DECIMAL(15,2) DEFAULT 0 COMMENT 'Valor comercial estimado actual',
    valor_original_estimado DECIMAL(15,2) NULL COMMENT 'Valor original estimado de compra',

    -- Proceso de investigación
    requiere_investigacion BOOLEAN DEFAULT TRUE,
    fecha_hallazgo DATE NOT NULL COMMENT 'Fecha en que se encontró el activo',
    encontrado_por_usuario_id INT NOT NULL COMMENT 'Usuario que reportó el hallazgo',
    notas_hallazgo TEXT NULL COMMENT 'Descripción del hallazgo y contexto',

    -- Resultados de investigación
    notas_investigacion TEXT NULL COMMENT 'Hallazgos durante la investigación',
    fecha_inicio_investigacion DATE NULL,
    fecha_fin_investigacion DATE NULL,
    investigado_por_usuario_id INT NULL,

    -- Fuentes de información encontradas
    tiene_factura BOOLEAN DEFAULT FALSE,
    ruta_factura VARCHAR(500) NULL,
    tiene_orden_compra BOOLEAN DEFAULT FALSE,
    ruta_orden_compra VARCHAR(500) NULL,
    encontrado_en_erp BOOLEAN DEFAULT FALSE COMMENT '¿Se encontró en el ERP de la clínica?',
    numero_erp VARCHAR(100) NULL COMMENT 'Número de referencia en ERP si se encontró',

    -- Aprobación e incorporación
    estado_incorporacion ENUM(
        'pendiente',
        'en_investigacion',
        'aprobado_para_incorporar',
        'rechazado',
        'incorporado',
        'dado_de_baja'
    ) DEFAULT 'pendiente',
    aprobado_por_usuario_id INT NULL,
    fecha_aprobacion DATE NULL,
    motivo_rechazo TEXT NULL COMMENT 'Razón si fue rechazado',

    -- Activo definitivo (después de incorporación)
    activo_definitivo_id INT NULL COMMENT 'ID en tabla activos después de incorporar',

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign Keys
    FOREIGN KEY (encontrado_por_usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (investigado_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (aprobado_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (clase_id) REFERENCES clases_activo(id) ON DELETE SET NULL,
    FOREIGN KEY (activo_definitivo_id) REFERENCES activos(id) ON DELETE SET NULL,

    -- Índices
    INDEX idx_placa (placa_codigo_interno),
    INDEX idx_estado_incorporacion (estado_incorporacion),
    INDEX idx_requiere_investigacion (requiere_investigacion),
    INDEX idx_fecha_hallazgo (fecha_hallazgo),
    INDEX idx_encontrado_por (encontrado_por_usuario_id),

    -- Constraints
    UNIQUE KEY uk_placa_temporal (placa_codigo_interno),
    CHECK (estado_fisico IN ('Operativo', 'Requiere Mantenimiento', 'Inoperativo', 'Desconocido'))

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla temporal para activos legacy encontrados que requieren investigación antes de incorporación definitiva';

-- PASO 2: Crear tabla de historial de cambios de estado
-- ============================================================================
CREATE TABLE IF NOT EXISTS activos_legacy_historial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activo_legacy_id INT NOT NULL,

    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50) NOT NULL,

    usuario_id INT NULL,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notas TEXT NULL,

    FOREIGN KEY (activo_legacy_id) REFERENCES activos_legacy_temporal(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,

    INDEX idx_activo_legacy (activo_legacy_id),
    INDEX idx_fecha (fecha_cambio)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- PASO 3: Crear vistas útiles
-- ============================================================================

-- Vista de activos pendientes de investigación
CREATE OR REPLACE VIEW vista_activos_legacy_pendientes AS
SELECT
    alt.id,
    alt.placa_codigo_interno,
    alt.nombre_activo,
    alt.marca,
    alt.modelo,
    alt.ubicacion,
    alt.estado_fisico,
    alt.anios_uso_estimado,
    alt.fecha_hallazgo,
    DATEDIFF(NOW(), alt.fecha_hallazgo) AS dias_sin_investigar,
    CONCAT(u.email) AS encontrado_por,
    alt.estado_incorporacion,
    c.nombre_clase
FROM activos_legacy_temporal alt
JOIN usuarios u ON alt.encontrado_por_usuario_id = u.id
LEFT JOIN clases_activo c ON alt.clase_id = c.id
WHERE alt.estado_incorporacion IN ('pendiente', 'en_investigacion')
ORDER BY alt.fecha_hallazgo ASC;

-- Vista de activos aprobados listos para incorporar
CREATE OR REPLACE VIEW vista_activos_legacy_aprobados AS
SELECT
    alt.id,
    alt.placa_codigo_interno,
    alt.nombre_activo,
    alt.marca,
    alt.modelo,
    alt.serie,
    alt.ubicacion,
    alt.valor_original_estimado,
    alt.valor_estimado_actual,
    alt.anios_uso_estimado,
    alt.fecha_hallazgo,
    alt.fecha_aprobacion,
    CONCAT(u_aprobador.email) AS aprobado_por,
    c.nombre_clase,
    alt.tiene_factura,
    alt.tiene_orden_compra,
    alt.encontrado_en_erp
FROM activos_legacy_temporal alt
JOIN usuarios u_aprobador ON alt.aprobado_por_usuario_id = u_aprobador.id
LEFT JOIN clases_activo c ON alt.clase_id = c.id
WHERE alt.estado_incorporacion = 'aprobado_para_incorporar'
ORDER BY alt.fecha_aprobacion ASC;

-- PASO 4: Crear stored procedure para incorporación automática
-- ============================================================================
DELIMITER $$

CREATE PROCEDURE sp_incorporar_activo_legacy(
    IN p_activo_legacy_id INT,
    IN p_usuario_incorporacion_id INT,
    OUT p_activo_definitivo_id INT,
    OUT p_mensaje VARCHAR(500)
)
proc_label: BEGIN
    DECLARE v_placa VARCHAR(100);
    DECLARE v_existe_placa INT;
    DECLARE v_estado_actual VARCHAR(50);
    DECLARE v_fecha_adquisicion DATE;
    DECLARE v_depreciacion_historica DECIMAL(15,2);

    -- Verificar que el activo legacy existe y está aprobado
    SELECT
        placa_codigo_interno,
        estado_incorporacion,
        DATE_SUB(NOW(), INTERVAL IFNULL(anios_uso_estimado, 10) YEAR)
    INTO
        v_placa,
        v_estado_actual,
        v_fecha_adquisicion
    FROM activos_legacy_temporal
    WHERE id = p_activo_legacy_id;

    IF v_placa IS NULL THEN
        SET p_mensaje = 'ERROR: Activo legacy no encontrado';
        LEAVE proc_label;
    END IF;

    IF v_estado_actual != 'aprobado_para_incorporar' THEN
        SET p_mensaje = CONCAT('ERROR: Activo no está aprobado. Estado actual: ', v_estado_actual);
        LEAVE proc_label;
    END IF;

    -- Verificar que la placa no exista en activos definitivos
    SELECT COUNT(*) INTO v_existe_placa
    FROM activos
    WHERE placa_codigo_interno = v_placa;

    IF v_existe_placa > 0 THEN
        SET p_mensaje = CONCAT('ERROR: Ya existe un activo con la placa ', v_placa);
        LEAVE proc_label;
    END IF;

    -- Iniciar transacción
    START TRANSACTION;

    -- Calcular depreciación histórica estimada
    SELECT
        CASE
            WHEN valor_original_estimado > 0 THEN
                valor_original_estimado - valor_estimado_actual
            ELSE
                0
        END
    INTO v_depreciacion_historica
    FROM activos_legacy_temporal
    WHERE id = p_activo_legacy_id;

    -- Insertar en tabla definitiva de activos
    INSERT INTO activos (
        nombre_activo,
        placa_codigo_interno,
        marca,
        modelo,
        serie,
        ubicacion,
        valor_comercial,
        estado,
        clase_id,
        tipo_propiedad,
        fecha_adquisicion,
        depreciacion_acumulada_historica,
        es_activo_legacy,
        metodo_depreciacion,
        observaciones,
        created_at
    )
    SELECT
        nombre_activo,
        placa_codigo_interno,
        marca,
        modelo,
        serie,
        ubicacion,
        IFNULL(valor_original_estimado, valor_estimado_actual) AS valor_comercial,
        CASE estado_fisico
            WHEN 'Operativo' THEN 'Operativo'
            WHEN 'Requiere Mantenimiento' THEN 'Requiere Mantenimiento'
            WHEN 'Inoperativo' THEN 'Inoperativo'
            ELSE 'Operativo'
        END AS estado,
        clase_id,
        'Propio' AS tipo_propiedad,
        v_fecha_adquisicion AS fecha_adquisicion,
        v_depreciacion_historica AS depreciacion_acumulada_historica,
        TRUE AS es_activo_legacy,
        IF(anios_uso_estimado >= 10, 'totalmente_depreciado', 'manual') AS metodo_depreciacion,
        CONCAT(
            'ACTIVO INCORPORADO DESDE HALLAZGO LEGACY\n',
            'Fecha hallazgo: ', DATE_FORMAT(fecha_hallazgo, '%Y-%m-%d'), '\n',
            'Notas hallazgo: ', IFNULL(notas_hallazgo, 'N/A'), '\n',
            'Notas investigación: ', IFNULL(notas_investigacion, 'N/A')
        ) AS observaciones,
        NOW() AS created_at
    FROM activos_legacy_temporal
    WHERE id = p_activo_legacy_id;

    -- Obtener ID del activo recién creado
    SET p_activo_definitivo_id = LAST_INSERT_ID();

    -- Actualizar registro legacy con referencia al activo definitivo
    UPDATE activos_legacy_temporal
    SET
        estado_incorporacion = 'incorporado',
        activo_definitivo_id = p_activo_definitivo_id,
        updated_at = NOW()
    WHERE id = p_activo_legacy_id;

    -- Registrar en historial
    INSERT INTO activos_legacy_historial (
        activo_legacy_id,
        estado_anterior,
        estado_nuevo,
        usuario_id,
        notas
    ) VALUES (
        p_activo_legacy_id,
        'aprobado_para_incorporar',
        'incorporado',
        p_usuario_incorporacion_id,
        CONCAT('Activo incorporado como ID: ', p_activo_definitivo_id)
    );

    COMMIT;

    SET p_mensaje = CONCAT('Activo incorporado exitosamente con ID: ', p_activo_definitivo_id);

END$$

DELIMITER ;

-- PASO 5: Crear triggers para auditoría automática
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_activos_legacy_estado_cambio
AFTER UPDATE ON activos_legacy_temporal
FOR EACH ROW
BEGIN
    IF OLD.estado_incorporacion != NEW.estado_incorporacion THEN
        INSERT INTO activos_legacy_historial (
            activo_legacy_id,
            estado_anterior,
            estado_nuevo,
            usuario_id,
            notas
        ) VALUES (
            NEW.id,
            OLD.estado_incorporacion,
            NEW.estado_incorporacion,
            NULL,  -- Usuario será capturado desde la aplicación
            'Cambio automático de estado'
        );
    END IF;
END$$

DELIMITER ;

-- PASO 6: Datos de prueba (opcional - comentar en producción)
-- ============================================================================
/*
INSERT INTO activos_legacy_temporal (
    placa_codigo_interno,
    nombre_activo,
    marca,
    modelo,
    ubicacion,
    estado_fisico,
    anios_uso_estimado,
    valor_estimado_actual,
    fecha_hallazgo,
    encontrado_por_usuario_id,
    notas_hallazgo
) VALUES (
    'AFX-LEGACY-001',
    'Monitor de Signos Vitales',
    'Philips',
    'IntelliVue MP30',
    'UCI - Piso 3',
    'Operativo',
    12,
    0,
    CURDATE(),
    1,
    'Encontrado durante inspección de UCI. Equipo operativo pero no registrado en sistema.'
);
*/

-- PASO 7: Verificación de instalación
-- ============================================================================
SELECT
    'Verificación de instalación del sistema de ingreso rápido legacy' AS mensaje,
    (SELECT COUNT(*) FROM activos_legacy_temporal) AS activos_legacy_registrados,
    (SELECT COUNT(*) FROM activos_legacy_historial) AS eventos_historial,
    (SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_NAME = 'sp_incorporar_activo_legacy') AS sp_instalado;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================

-- ROLLBACK (si necesitas revertir):
/*
DROP TRIGGER IF EXISTS trg_activos_legacy_estado_cambio;
DROP PROCEDURE IF EXISTS sp_incorporar_activo_legacy;
DROP VIEW IF EXISTS vista_activos_legacy_aprobados;
DROP VIEW IF EXISTS vista_activos_legacy_pendientes;
DROP TABLE IF EXISTS activos_legacy_historial;
DROP TABLE IF EXISTS activos_legacy_temporal;
*/
