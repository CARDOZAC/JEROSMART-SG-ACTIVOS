-- Esquema de la base de datos para la aplicación de gestión de activos fijos

-- Tabla para almacenar los activos
CREATE TABLE IF NOT EXISTS activos (
    id_activo INTEGER PRIMARY KEY AUTOINCREMENT,
    placa_codigo_interno TEXT NOT NULL UNIQUE,
    nombre_activo TEXT NOT NULL,
    marca_referencia_modelo TEXT,
    serial TEXT,
    ubicacion TEXT,
    registro_invima TEXT,
    forma_adquisicion TEXT,
    vida_util_anios INTEGER,
    clasificacion_activo TEXT,
    observaciones TEXT,
    especificaciones_del_activo TEXT,
    clase_de_activo TEXT,
    responsable TEXT,
    estado_actual TEXT,
    fecha_adquisicion TEXT, -- Formato YYYY-MM-DD
    valor_adquisicion REAL
);

-- Tabla para almacenar los movimientos de los activos
-- Incluye columnas para todos los tipos de movimiento, permitiendo NULL donde no aplique.
CREATE TABLE IF NOT EXISTS movimientos (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_movimiento TEXT NOT NULL, -- 'entrada_salida', 'traslado', 'entrega'
    fecha_movimiento TEXT NOT NULL, -- Formato YYYY-MM-DD
    hora_movimiento TEXT NOT NULL,   -- Formato HH:MM
    motivo TEXT,
    observaciones_generales TEXT,

    -- Campos específicos para 'entrada_salida'
    ciudad TEXT,
    sede TEXT,
    nombre_responsable_solicitante TEXT,
    cedula_solicitante TEXT,
    cargo_area_solicitante TEXT,
    entidad_persona_tercero TEXT,
    nit_cc_tercero TEXT,
    direccion_tercero TEXT,
    movil_tercero TEXT,
    entrada_salida_selector TEXT,
    entrada_subtipo TEXT,
    entrada_otro TEXT,
    salida_subtipo TEXT,
    salida_otro TEXT,

    -- Campos específicos para 'traslado'
    numero_traslado TEXT,
    tipo_traslado TEXT,
    caracteristicas_traslado TEXT,
    ubicacion_inicial TEXT,
    ubicacion_final TEXT,
    funcionario_responsable_actual_traslado TEXT,
    cedula_responsable_actual_traslado TEXT,
    cargo_responsable_actual_traslado TEXT,
    area_responsable_actual_traslado TEXT,
    funcionario_responsable_nuevo_traslado TEXT,
    cedula_responsable_nuevo_traslado TEXT,
    cargo_responsable_nuevo_traslado TEXT,
    area_responsable_nuevo_traslado TEXT,
    
    -- Campos específicos para 'entrega' (algunos compartidos con 'traslado', como lugar_evento_destino)
    lugar_evento_destino TEXT, -- Usado en 'traslado' y 'entrega'
    numero_acta TEXT,
    valor_contrato_factura REAL,
    orden_compra_numero TEXT,
    fecha_orden_compra TEXT, -- Formato YYYY-MM-DD
    tipo_contrato TEXT,
    objeto_entrega TEXT,
    centro_costo TEXT,
    proveedor TEXT,
    nit_proveedor TEXT,
    factura TEXT,
    tipo_elemento_entregado TEXT,
    requiere_capacitacion INTEGER, -- 0 para Falso, 1 para Verdadero
    requiere_montaje INTEGER,     -- 0 para Falso, 1 para Verdadero
    tipo_asignacion_entrega TEXT,
    es_propio_ajeno TEXT
);

-- Tabla para la relación muchos a muchos entre movimientos y activos
CREATE TABLE IF NOT EXISTS movimiento_activos (
    id_movimiento INTEGER NOT NULL,
    id_activo INTEGER NOT NULL,
    cantidad INTEGER,
    estado_activo_al_momento_movimiento TEXT,
    observaciones_movimiento_activo TEXT,
    descripcion_accesorios TEXT,
    PRIMARY KEY (id_movimiento, id_activo),
    FOREIGN KEY (id_movimiento) REFERENCES movimientos (id_movimiento) ON DELETE CASCADE,
    FOREIGN KEY (id_activo) REFERENCES activos (id_activo) ON DELETE CASCADE
);

-- Tabla para almacenar las firmas asociadas a los movimientos
CREATE TABLE IF NOT EXISTS firmas (
    id_firma INTEGER PRIMARY KEY AUTOINCREMENT,
    id_movimiento INTEGER NOT NULL,
    rol TEXT NOT NULL, -- Ej: 'responsable', 'jefe_inmediato', 'vobo_activos'
    ruta_firma TEXT, -- Ruta al archivo de la firma guardado en el sistema de archivos
    UNIQUE (id_movimiento, rol), -- Asegura que solo haya una firma por rol para un movimiento
    FOREIGN KEY (id_movimiento) REFERENCES movimientos (id_movimiento) ON DELETE CASCADE
);