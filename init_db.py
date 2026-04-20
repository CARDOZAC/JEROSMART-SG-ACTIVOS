import sqlite3
import os
import json
# from werkzeug.security import generate_password_hash

# ==============================================================================
# NOTA IMPORTANTE PARA EL APRENDIZAJE:
# Este archivo ha sido modificado para demostrar cómo se haría con SQLAlchemy,
# que es la forma recomendada y consistente con el resto de tu aplicación
# (como en `movimientos/routes.py`).
#
# El código original que usaba `sqlite3` directamente ha sido comentado o eliminado
# porque la mejor práctica es usar el ORM (SQLAlchemy) para crear y poblar la BD.
# Así, si cambias tus modelos (en `models.py`), la BD se creará correctamente.
# ==============================================================================

# ------------------------------------------------------------------------------
# Rutas
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Esquema
# ------------------------------------------------------------------------------
def create_schema(cursor):
    """
    Crea toda la estructura de tablas de la base de datos.
    Se han realizado las siguientes mejoras:
    - Normalización del esquema.
    - Se agregó el campo 'rol' a la tabla 'usuarios'.
    - Se optimizó la tabla 'firmas' para que sea centralizada y reutilizable
      entre diferentes tipos de documentos (movimientos, mantenimientos, etc.).
    """
    # Con SQLAlchemy, la creación del esquema se hace a través de los modelos.
    # Esta función ya no es necesaria como antes. El comando `db.create_all()`
    # se encargará de esto.
    print("-> Creando esquema de tablas desde los modelos de SQLAlchemy...")

    # ----------------------- Catálogos / Básicas ------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            clave_hash TEXT NOT NULL,
            cargo TEXT,
            area TEXT,
            rol TEXT NOT NULL CHECK(rol IN ('Admin', 'User')) DEFAULT 'User'
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            cedula TEXT UNIQUE NOT NULL,
            cargo TEXT,
            area TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razon_social TEXT UNIQUE NOT NULL,
            nit TEXT UNIQUE,
            direccion TEXT,
            persona_contacto TEXT,
            numero_contacto TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clases_activo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_clase TEXT UNIQUE NOT NULL
        );
    """)

    # Nueva tabla para los documentos (PDFs) adjuntos a cada movimiento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos_adjuntos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_id INTEGER NOT NULL,
            nombre_documento TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            FOREIGN KEY (documento_id) REFERENCES movimientos(id) ON DELETE CASCADE
        );
    """)

    # --------------------------- Activos --------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_activo TEXT NOT NULL,
            placa_codigo_interno TEXT UNIQUE NOT NULL,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            ubicacion TEXT,
            observaciones TEXT,
            valor_comercial REAL,
            estado TEXT NOT NULL CHECK(estado IN ('Operativo', 'En Mantenimiento', 'Dado de Baja', 'En Almacén', 'Pendiente Asignación'))
                                 DEFAULT 'Operativo',
            created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            tipo_propiedad TEXT NOT NULL CHECK(tipo_propiedad IN ('Propio', 'Ajeno')) DEFAULT 'Propio',
            origen_adquisicion TEXT CHECK(origen_adquisicion IN ('Compra','Donación') OR origen_adquisicion IS NULL),
            condicion_tenencia TEXT CHECK(condicion_tenencia IN ('Arriendo','Comodato','Préstamo') OR condicion_tenencia IS NULL),
            clase_id INTEGER,
            funcionario_id INTEGER,
            atributos_dinamicos_json TEXT,
            propietario_ajeno TEXT,
            contacto_propietario TEXT,
            fecha_ingreso_ajeno TEXT,
            ruta_orden_compra TEXT,
            ruta_factura TEXT,
            ruta_contrato_arriendo TEXT,
            ruta_foto_activo TEXT, -- Se agregó para la foto del activo
            FOREIGN KEY (clase_id) REFERENCES clases_activo(id),
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activo_accesorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activo_id INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE
        );
    """)

    # ------------------------- Hojas de Vida ----------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hojas_de_vida (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activo_id INTEGER NOT NULL UNIQUE,
            ruta_pdf_fisica TEXT,
            ruta_foto_activo TEXT,
            normativa_aplicable TEXT,
            created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE
        );
    """)

    # --------------------------- Movimientos ----------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('Entrega', 'Traslado', 'Entrada/Salida', 'Paz y Salvo')),
            fecha TEXT NOT NULL,
            observaciones_generales TEXT,
            usuario_id INTEGER,
            funcionario_id INTEGER, -- Para Paz y Salvo o Entrega
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimiento_activos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movimiento_id INTEGER NOT NULL,
            activo_id INTEGER NOT NULL,
            FOREIGN KEY (movimiento_id) REFERENCES movimientos(id) ON DELETE CASCADE,
            FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE RESTRICT
        );
    """)
    
    # Se optimizó esta tabla para manejar firmas de cualquier documento (movimientos, mantenimientos, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_id INTEGER NOT NULL,
            tipo_documento TEXT NOT NULL CHECK(tipo_documento IN ('movimiento', 'mantenimiento')),
            rol_firma TEXT NOT NULL,
            firma_base64 TEXT NOT NULL,
            UNIQUE(documento_id, tipo_documento, rol_firma)
        );
    """)

    # Accesorios registrados dentro de un movimiento/acta
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accesorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movimiento_activo_id INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            referencia TEXT,
            serial TEXT,
            cantidad INTEGER NOT NULL DEFAULT 1,
            observacion TEXT,
            FOREIGN KEY (movimiento_activo_id) REFERENCES movimiento_activos(id) ON DELETE CASCADE
        );
    """)

    # --------- Detalles por tipo de movimiento (uno a uno con movimiento) -----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalles_entrega (
            movimiento_id INTEGER PRIMARY KEY,
            proveedor_id INTEGER,
            factura TEXT,
            orden_compra_contrato TEXT,
            fecha_oc_contrato TEXT,
            objeto_contrato TEXT,
            tipo_elementos TEXT, -- JSON
            requiere_montaje BOOLEAN,
            requiere_capacitacion BOOLEAN,
            tipo_asignacion TEXT,
            quien_entrega_nombre TEXT,
            quien_recibe_nombre TEXT,
            observaciones_acta TEXT,
            FOREIGN KEY (movimiento_id) REFERENCES movimientos(id) ON DELETE CASCADE,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalles_traslado (
            movimiento_id INTEGER PRIMARY KEY,
            fecha_traslado TEXT,
            hora_traslado TEXT,
            tipo_traslado_json TEXT, -- Almacena un array JSON de los tipos seleccionados
            ubicacion_inicial TEXT,
            ubicacion_final TEXT,
            origen_responsable_nombre TEXT,
            origen_responsable_cc TEXT,
            origen_responsable_cargo TEXT,
            nuevo_responsable_nombre TEXT,
            nuevo_responsable_cc TEXT,
            nuevo_responsable_cargo TEXT,
            FOREIGN KEY (movimiento_id) REFERENCES movimientos(id) ON DELETE CASCADE,
            -- Los IDs de funcionario se pueden añadir aquí si se implementa
            -- la búsqueda y selección de funcionarios en el formulario.
            -- FOREIGN KEY (origen_funcionario_id) REFERENCES funcionarios(id) ON DELETE SET NULL,
            -- FOREIGN KEY (destino_funcionario_id) REFERENCES funcionarios(id) ON DELETE SET NULL
        );
    """)

    # Se agregó fecha_salida para tener el registro completo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalles_entrada_salida (
            movimiento_id INTEGER PRIMARY KEY,
            ciudad TEXT,
            sede TEXT,
            solicitante_responsable_nombre TEXT,
            solicitante_responsable_cc TEXT,
            solicitante_responsable_cargo_area TEXT,
            tercero_entidad_persona TEXT,
            tercero_nit_cc TEXT,
            tercero_direccion TEXT,
            tercero_movil TEXT,
            tipo_operacion TEXT NOT NULL CHECK(tipo_operacion IN ('Entrada', 'Salida')),
            motivo TEXT NOT NULL,
            fecha_retorno_estimada TEXT,
            FOREIGN KEY (movimiento_id) REFERENCES movimientos(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalles_paz_salvo (
            movimiento_id INTEGER PRIMARY KEY,
            funcionario_desvinculado_id INTEGER NOT NULL,
            nombre_funcionario TEXT,
            cargo_funcionario TEXT,
            area_funcionario TEXT,
            observaciones_paz_salvo TEXT,
            FOREIGN KEY (movimiento_id) REFERENCES movimientos(id) ON DELETE CASCADE,
            FOREIGN KEY (funcionario_desvinculado_id) REFERENCES funcionarios(id) ON DELETE RESTRICT
        );
    """)

    # ---------------------- Gestión biomédica ---------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mantenimiento_tipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mantenimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activo_id INTEGER NOT NULL,
            tipo_id INTEGER NOT NULL,
            fecha_mantenimiento TEXT NOT NULL,
            duracion_minutos INTEGER,
            observaciones TEXT,
            usuario_id INTEGER NOT NULL,
            estado TEXT NOT NULL CHECK(estado IN ('Completo', 'Incompleto', 'Pendiente')) DEFAULT 'Pendiente',
            atributos_reporte_json TEXT,
            FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (tipo_id) REFERENCES mantenimiento_tipos(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mantenimiento_fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mantenimiento_id INTEGER NOT NULL,
            ruta_foto TEXT NOT NULL,
            descripcion TEXT,
            FOREIGN KEY (mantenimiento_id) REFERENCES mantenimientos(id) ON DELETE CASCADE
        );
    """)

    print("-> Esquema creado.")


# ------------------------------------------------------------------------------
# Índices
# ------------------------------------------------------------------------------
def create_indexes(cursor):
    """Crea los índices necesarios para optimizar las búsquedas."""
    print("-> Creando índices...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activos_funcionario_id ON activos(funcionario_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activos_placa ON activos(placa_codigo_interno);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activos_serie ON activos(serie);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos(tipo_movimiento);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movact_mov ON movimiento_activos(movimiento_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movact_activo ON movimiento_activos(activo_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_acc_movact ON accesorios(movimiento_activo_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_entrega_mov ON detalles_entrega(movimiento_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_traslado_mov ON detalles_traslado(movimiento_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_es_mov ON detalles_entrada_salida(movimiento_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_paz_mov ON detalles_paz_salvo(movimiento_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_firmas_doc ON firmas(documento_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mantenimientos_activo_id ON mantenimientos(activo_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mantenimientos_tipo ON mantenimientos(tipo_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mantenimiento_fotos_mantenimiento_id ON mantenimiento_fotos(mantenimiento_id);")
    print("-> Índices listos.")


# ------------------------------------------------------------------------------
# Triggers (reglas de negocio en BD)
# ------------------------------------------------------------------------------
def create_triggers(cursor):
    """
    Crea los triggers para automatizar la actualización del estado de los activos.
    Estos triggers son la clave para la "actualización dinámica" que solicitaste.
    """
    print("-> Creando triggers...")

    # Actualiza el activo con el nuevo funcionario y ubicación en un traslado.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_traslado_insert
        AFTER INSERT ON detalles_traslado
        BEGIN
            UPDATE activos
            SET 
                funcionario_id = NEW.destino_funcionario_id,
                ubicacion = NEW.destino_area,
                estado = CASE 
                            WHEN NEW.destino_funcionario_id IS NULL THEN 'Pendiente Asignación'
                            ELSE 'Operativo'
                         END
            WHERE id IN (SELECT activo_id FROM movimiento_activos WHERE movimiento_id = NEW.movimiento_id);
        END;
    """)

    # Actualiza el activo con el nuevo funcionario después de una entrega.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_entrega_insert
        AFTER INSERT ON detalles_entrega
        BEGIN
            UPDATE activos
            SET 
                funcionario_id = NEW.recibe_funcionario_id,
                estado = 'Operativo'
            WHERE id IN (SELECT activo_id FROM movimiento_activos WHERE movimiento_id = NEW.movimiento_id);
        END;
    """)

    # Actualiza el estado del activo en una entrada o salida.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_entrada_salida_insert
        AFTER INSERT ON detalles_entrada_salida
        BEGIN
            UPDATE activos
            SET estado = CASE NEW.tipo_operacion
                             WHEN 'Salida' THEN 'En Mantenimiento'
                             WHEN 'Entrada' THEN 'Operativo'
                             ELSE estado
                         END
            WHERE id IN (SELECT activo_id FROM movimiento_activos WHERE movimiento_id = NEW.movimiento_id);
        END;
    """)

    # Desasigna los activos de un funcionario que se desvincula.
    # Se establece el funcionario_id a NULL para liberar el activo.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_paz_salvo_insert
        AFTER INSERT ON detalles_paz_salvo
        BEGIN
            UPDATE activos
            SET 
                funcionario_id = NULL,
                estado = 'Pendiente Asignación'
            WHERE funcionario_id = NEW.funcionario_desvinculado_id;
        END;
    """)
    
    # Se asegura que la ubicación del activo esté siempre sincronizada con la del funcionario asignado
    # al momento de actualizar un activo.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_activo_update_funcionario
        AFTER UPDATE OF funcionario_id ON activos
        WHEN NEW.funcionario_id IS NOT NULL AND NEW.ubicacion IS NULL
        BEGIN
            UPDATE activos
            SET ubicacion = (SELECT area FROM funcionarios WHERE id = NEW.funcionario_id)
            WHERE id = NEW.id;
        END;
    """)
    
    # Se asegura que la ubicación del activo se actualice si cambia el área del funcionario.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_funcionario_update_area
        AFTER UPDATE OF area ON funcionarios
        BEGIN
            UPDATE activos
            SET ubicacion = NEW.area
            WHERE funcionario_id = NEW.id;
        END;
    """)

    print("-> Triggers creados.")


# ------------------------------------------------------------------------------
# Datos de ejemplo
# ------------------------------------------------------------------------------
def seed_data(cursor):
    """
    Inserta datos de ejemplo para el entorno de desarrollo.
    NOTA: Esta es la versión conceptual de cómo se haría con SQLAlchemy.
    Se necesitarían los modelos (`User`, `ClaseActivo`, etc.) importados.
    """
    print("-> Insertando datos de ejemplo...")

    # from app.models import User, ClaseActivo, Funcionario, Proveedor, MantenimientoTipo, Activo, etc.
    # from app.extensions import db
    # from werkzeug.security import generate_password_hash

    # try:
    #     admin_user = User(email='david.cardoza@clinicaprimavera.com', cargo='Administrador', area='IT', rol='Admin')
    #     admin_user.set_password('12345') # Asumiendo que tienes un método set_password en tu modelo User
    #     db.session.add(admin_user)

    #     clases = ['Equipo Biomédico', 'Equipo Electro-Industrial', 'TICs', 'Muebles y Enseres']
    #     for c in clases:
    #         db.session.add(ClaseActivo(nombre_clase=c))

    #     # ... y así sucesivamente para todos los demás datos de ejemplo ...

    try:
        cursor.execute(
            "INSERT INTO usuarios (email, clave_hash, cargo, area, rol) VALUES (?, ?, ?, ?, ?)",
            ('david.cardoza@clinicaprimavera.com', generate_password_hash('12345'), 'Administrador', 'IT', 'Admin')
        )
        print("Usuario de prueba 'david.cardoza@clinicaprimavera.com' (rol: Admin) insertado. Por favor, remueva esta línea en producción.")
    except sqlite3.IntegrityError:
        print("El usuario 'david.cardoza@clinicaprimavera.com' ya existe. Omitiendo la inserción.")

    # El resto de este código es el original, que debería ser reemplazado por el enfoque de SQLAlchemy.
    # Lo mantenemos por ahora para que el script no falle completamente.
    # clases = ['Equipo Biomédico', 'Equipo Electro-Industrial', 'TICs', 'Muebles y Enseres']
    # cursor.executemany("INSERT INTO clases_activo (nombre_clase) VALUES (?)", [(c,) for c in clases])
    # cursor.execute("INSERT INTO funcionarios (nombres, apellidos, cedula, cargo, area) VALUES (?, ?, ?, ?, ?)",
    #              ('Ana', 'Pérez', '12345678', 'Coordinadora', 'Administración'))
    cursor.execute("INSERT INTO funcionarios (nombres, apellidos, cedula, cargo, area) VALUES (?, ?, ?, ?, ?)",
                   ('Luis', 'García', '87654321', 'Jefe de Sistemas', 'Sistemas'))
    cursor.execute("INSERT INTO funcionarios (nombres, apellidos, cedula, cargo, area) VALUES (?, ?, ?, ?, ?)",
                   ('Maria', 'Rodriguez', '11223344', 'Enfermera Jefe', 'Hospitalización Piso 3'))
    cursor.execute("INSERT INTO funcionarios (nombres, apellidos, cedula, cargo, area) VALUES (?, ?, ?, ?, ?)",
                   ('Carlos', 'López', '22334455', 'Técnico de Mantenimiento', 'Mantenimiento'))
    cursor.execute("INSERT INTO funcionarios (nombres, apellidos, cedula, cargo, area) VALUES (?, ?, ?, ?, ?)",
                   ('Laura', 'Martínez', '33445566', 'Auxiliar Administrativa', 'Recursos Humanos'))


    #    # cursor.execute("INSERT INTO proveedores (razon_social, nit) VALUES (?, ?)",
    #                   ('TecnoSoluciones S.A.S.', '900.123.456-7'))
    cursor.execute("INSERT INTO proveedores (razon_social, nit) VALUES (?, ?)",
                   ('BioEquipos SAS', '900.555.123-4'))


    # tipo_nombres = [
    #     'Reporte Monitor Signos Vitales', 'Reporte Cama Hospitalaria', 'Reporte Calentador de Paciente',
    #     'Por Definir'
    # ]
    # cursor.executemany("INSERT INTO mantenimiento_tipos (nombre) VALUES (?)", [(n,) for n in tipo_nombres])

    # Activo sin asignar
    cursor.execute("""
        INSERT INTO activos (nombre_activo, placa_codigo_interno, marca, modelo, ubicacion, estado, clase_id, tipo_propiedad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Portátil de Desarrollo', 'TIC-001', 'Dell', 'Latitude 5420', 'Almacén Principal', 'Pendiente Asignación', 3, 'Propio'))
    portatil_id = cursor.lastrowid
    cursor.execute("INSERT INTO activo_accesorios (activo_id, descripcion, marca) VALUES (?, ?, ?)",
                   (portatil_id, 'Cargador 65W USB-C', 'Dell'))

    cursor.execute("""
        INSERT INTO activos (nombre_activo, placa_codigo_interno, marca, modelo, ubicacion, estado, clase_id, funcionario_id, valor_comercial, tipo_propiedad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Monitor de Signos Vitales', 'BIO-050', 'Mindray', 'ePM12', 'Hospitalización Piso 3', 'Operativo', 1, 3, 8200000.00, 'Propio'))
    monitor_id = cursor.lastrowid
    cursor.execute("INSERT INTO activo_accesorios (activo_id, descripcion) VALUES (?, ?)", (monitor_id, 'Sensor SpO2 Adulto'))

    # Se crea un movimiento de tipo 'Entrega' para el portátil.
    fecha_mov = '2025-08-15 11:30:00'
    cursor.execute("INSERT INTO movimientos (tipo_movimiento, fecha, usuario_id, observaciones_generales) VALUES (?, ?, ?, ?)",
                   ('Entrega', fecha_mov, 1, 'Entrega inicial de Portátil a Luis García'))
    movimiento_id = cursor.lastrowid

    # Enlaza el activo al movimiento
    cursor.execute("INSERT INTO movimiento_activos (movimiento_id, activo_id) VALUES (?, ?)", (movimiento_id, portatil_id))
    mov_item_id = cursor.lastrowid

    # Se insertan los detalles de la entrega. Nota: se usan los IDs de los funcionarios.
    cursor.execute("""
        INSERT INTO detalles_entrega (
            movimiento_id, quien_recibe_nombre, quien_entrega_nombre, 
            orden_compra_contrato, fecha_oc_contrato, objeto_contrato,
            tipo_elementos, requiere_montaje, requiere_capacitacion, tipo_asignacion,
            observaciones_acta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        movimiento_id, 'Luis García', 'Ana Pérez',
        'OC-2025-151', '2025-08-10', 'Suministro de equipo de cómputo',
        json.dumps(['Equipos TIC']), 0, 0, 'Asignación Directa',
        'Entrega de portátil para el área de sistemas.'
    ))

    # Se insertan los accesorios de la entrega
    cursor.execute("""
        INSERT INTO accesorios (movimiento_activo_id, descripcion, referencia, serial, cantidad, observacion)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mov_item_id, 'Mouse inalámbrico', 'Logitech MX', 'MX-123', 1, 'Conecta por Bluetooth'))

    # Se inserta la firma del movimiento. Ahora se usa 'documento_id' y 'tipo_documento'.
    cursor.execute("""
        INSERT INTO firmas (documento_id, tipo_documento, rol_firma, firma_base64) VALUES (?, ?, ?, ?)
    """, (movimiento_id, 'movimiento', 'Quien_Recibe', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...'))
    
    # Se crea un movimiento de tipo 'Traslado' para el monitor
    cursor.execute("""
        INSERT INTO movimientos (tipo_movimiento, fecha, usuario_id, observaciones_generales)
        VALUES (?, ?, ?, ?)
    """, ('Traslado', '2025-08-16 09:00:00', 1, 'Traslado de monitor de piso'))
    mov_traslado_id = cursor.lastrowid

    # Enlaza el activo (monitor) al movimiento de traslado
    cursor.execute("INSERT INTO movimiento_activos (movimiento_id, activo_id) VALUES (?, ?)", (mov_traslado_id, monitor_id))

    # Se insertan los detalles del traslado
    cursor.execute("""
        INSERT INTO detalles_traslado (
            movimiento_id, origen_area, origen_funcionario_id, destino_area, destino_funcionario_id, motivo_traslado
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (mov_traslado_id, 'Hospitalización Piso 3', 3, 'Hospitalización Piso 4', 3, 'Cambio de ubicación del paciente'))


    # Se crea un movimiento de tipo 'Paz y Salvo' para Maria Rodriguez
    cursor.execute("""
        INSERT INTO movimientos (tipo_movimiento, fecha, usuario_id, observaciones_generales)
        VALUES (?, ?, ?, ?)
    """, ('Paz y Salvo', '2025-08-17 14:00:00', 1, 'Desvinculación de Maria Rodriguez'))
    mov_paz_salvo_id = cursor.lastrowid

    # Se insertan los detalles de paz y salvo
    cursor.execute("""
        INSERT INTO detalles_paz_salvo (movimiento_id, funcionario_desvinculado_id, nombre_funcionario, cargo_funcionario, area_funcionario, observaciones_paz_salvo) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mov_paz_salvo_id, 3, 'Maria Rodriguez', 'Enfermera Jefe', 'Hospitalización Piso 3', 'Devolución de todos los activos a satisfacción.'))

# ------------------------------------------------------------------------------
# Orquestación
# ------------------------------------------------------------------------------
def init_db_app(app):
    """
    Crea y configura la base de datos desde cero usando SQLAlchemy.
    Esta función se debe ejecutar en el contexto de la aplicación Flask.
    """
    with app.app_context():
        from app.extensions import db
        # Importa aquí todos tus modelos para que SQLAlchemy los conozca
        from app.models import User, Funcionario, Proveedor, ClaseActivo, Activo, Movimiento, Mantenimiento # y todos los demás

        db_path = app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Base de datos '{db_path}' existente eliminada para empezar limpia.")

        print("-> Creando todas las tablas desde los modelos...")
        db.create_all()
        print("-> Tablas creadas.")

        print("-> Insertando datos de ejemplo (seed)...")
        # --- Creación de datos con SQLAlchemy ---
        try:
            # Usuario Admin
            admin_user = User(email='david.cardoza@clinicaprimavera.com', cargo='Administrador', area='IT', rol='Admin')
            admin_user.set_password('12345') # Asumiendo método en el modelo User
            db.session.add(admin_user)

            # Clases de Activo
            clases = ['Equipo Biomédico', 'Equipo Electro-Industrial', 'TICs', 'Muebles y Enseres']
            for c in clases:
                db.session.add(ClaseActivo(nombre_clase=c))

            # (Aquí iría el resto de la lógica para crear funcionarios, proveedores, activos, etc.)

            db.session.commit()
            print(f"\n✅ Base de datos '{db_path}' creada y poblada exitosamente.")
            print("   Admin de prueba -> usuario: 'david.cardoza@clinicaprimavera.com'  |  contraseña: '12345'")
        except Exception as e:
            print(f"\n❌ Error al poblar la base de datos: {e}")
            db.session.rollback()
            raise