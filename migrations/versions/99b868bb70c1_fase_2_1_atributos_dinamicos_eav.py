"""fase_2_1_atributos_dinamicos_eav

FASE 2.1: Sistema de Atributos Dinámicos (EAV Mejorado)
- Tabla categoria_activo: Categorías de activos (Biomédicos, TICs, etc.)
- Tabla atributo_definicion: Plantillas de atributos personalizados por categoría
- Tabla atributo_valor: Valores concretos de atributos (patrón EAV con columnas tipadas)
- Modificación tabla activos: Agregar categoria_id

Características:
✓ Validación de tipos de datos (texto, numero, fecha, booleano, lista, texto_largo)
✓ Columnas tipadas para búsquedas indexadas eficientes
✓ Atributos requeridos y valores por defecto
✓ Opciones predefinidas para campos tipo lista
✓ Validación con expresiones regulares
✓ Unidades de medida

Revision ID: 99b868bb70c1
Revises: cbe6127ebdff
Create Date: 2025-11-24 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '99b868bb70c1'
down_revision = 'cbe6127ebdff'
branch_labels = None
depends_on = None


def upgrade():
    print("=" * 80)
    print("INICIANDO FASE 2.1: Sistema de Atributos Dinámicos (EAV Mejorado)")
    print("=" * 80)

    # ===== 1. Crear tabla categoria_activo =====
    print("\n[1/4] Creando tabla 'categoria_activo'...")

    op.create_table(
        'categoria_activo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('icono', sa.String(length=50), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('orden_visualizacion', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre', name='uq_categoria_nombre'),
        sa.UniqueConstraint('codigo', name='uq_categoria_codigo'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Crear índices para categoria_activo
    op.create_index('ix_categoria_activo_codigo', 'categoria_activo', ['codigo'], unique=False)
    op.create_index('ix_categoria_activo_activa', 'categoria_activo', ['activa'], unique=False)
    op.create_index('ix_categoria_activo_orden', 'categoria_activo', ['orden_visualizacion'], unique=False)

    print("   [OK] Tabla 'categoria_activo' creada exitosamente")

    # ===== 2. Crear tabla atributo_definicion =====
    print("\n[2/4] Creando tabla 'atributo_definicion'...")

    op.create_table(
        'atributo_definicion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('etiqueta', sa.String(length=150), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('tipo_dato', sa.String(length=20), nullable=False),
        sa.Column('es_requerido', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('unidad_medida', sa.String(length=50), nullable=True),
        sa.Column('opciones_json', sa.Text(), nullable=True),
        sa.Column('valor_por_defecto', sa.String(length=255), nullable=True),
        sa.Column('orden_visualizacion', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('validacion_regex', sa.String(length=255), nullable=True),
        sa.Column('mensaje_ayuda', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('categoria_id', 'nombre', name='uq_atributo_categoria_nombre'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Crear índices para atributo_definicion
    op.create_index('ix_atributo_def_categoria', 'atributo_definicion', ['categoria_id'], unique=False)
    op.create_index('ix_atributo_def_activo', 'atributo_definicion', ['activo'], unique=False)
    op.create_index('ix_atributo_def_orden', 'atributo_definicion', ['orden_visualizacion'], unique=False)

    # Crear FK a categoria_activo
    op.create_foreign_key(
        'fk_atributo_def_categoria',
        'atributo_definicion', 'categoria_activo',
        ['categoria_id'], ['id'],
        ondelete='CASCADE'
    )

    print("   [OK] Tabla 'atributo_definicion' creada exitosamente")

    # ===== 3. Crear tabla atributo_valor =====
    print("\n[3/4] Creando tabla 'atributo_valor'...")

    op.create_table(
        'atributo_valor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activo_id', sa.Integer(), nullable=False),
        sa.Column('atributo_definicion_id', sa.Integer(), nullable=False),
        sa.Column('valor_texto', sa.String(length=500), nullable=True),
        sa.Column('valor_numerico', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('valor_fecha', sa.Date(), nullable=True),
        sa.Column('valor_booleano', sa.Boolean(), nullable=True),
        sa.Column('valor_texto_largo', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('activo_id', 'atributo_definicion_id', name='uq_valor_activo_atributo'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Crear índices para atributo_valor
    op.create_index('ix_atributo_valor_activo', 'atributo_valor', ['activo_id'], unique=False)
    op.create_index('ix_atributo_valor_def', 'atributo_valor', ['atributo_definicion_id'], unique=False)
    op.create_index('ix_atributo_valor_numerico', 'atributo_valor', ['valor_numerico'], unique=False)
    op.create_index('ix_atributo_valor_fecha', 'atributo_valor', ['valor_fecha'], unique=False)
    op.create_index('ix_atributo_valor_booleano', 'atributo_valor', ['valor_booleano'], unique=False)

    # Crear índice compuesto para búsquedas por activo y definición
    op.create_index('idx_valor_activo_def', 'atributo_valor', ['activo_id', 'atributo_definicion_id'], unique=False)

    # Crear FKs
    op.create_foreign_key(
        'fk_atributo_valor_activo',
        'atributo_valor', 'activos',
        ['activo_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_atributo_valor_definicion',
        'atributo_valor', 'atributo_definicion',
        ['atributo_definicion_id'], ['id'],
        ondelete='RESTRICT'
    )

    print("   [OK] Tabla 'atributo_valor' creada exitosamente")

    # ===== 4. Agregar categoria_id a tabla activos =====
    print("\n[4/4] Agregando campo 'categoria_id' a tabla 'activos'...")

    op.add_column('activos', sa.Column('categoria_id', sa.Integer(), nullable=True))
    op.create_index('ix_activos_categoria', 'activos', ['categoria_id'], unique=False)

    op.create_foreign_key(
        'fk_activos_categoria',
        'activos', 'categoria_activo',
        ['categoria_id'], ['id'],
        ondelete='SET NULL'
    )

    print("   [OK] Campo 'categoria_id' agregado a 'activos' exitosamente")

    # ===== 5. Poblar categorías iniciales =====
    print("\n[5/5] Poblando categorías iniciales...")

    connection = op.get_bind()

    categorias_iniciales = [
        {
            'nombre': 'Equipos Biomédicos',
            'codigo': 'BIOMEDICO',
            'descripcion': 'Equipos médicos y hospitalarios que requieren gestión de riesgo, voltaje, frecuencia y calibración',
            'icono': 'fa-heartbeat',
            'orden_visualizacion': 1
        },
        {
            'nombre': 'Equipos Informáticos',
            'codigo': 'INFORMATICO',
            'descripcion': 'Computadores, servidores, impresoras y equipos de TI',
            'icono': 'fa-desktop',
            'orden_visualizacion': 2
        },
        {
            'nombre': 'Mobiliario',
            'codigo': 'MOBILIARIO',
            'descripcion': 'Muebles de oficina, escritorios, sillas, estanterías',
            'icono': 'fa-couch',
            'orden_visualizacion': 3
        },
        {
            'nombre': 'Vehículos',
            'codigo': 'VEHICULO',
            'descripcion': 'Vehículos automotores de la institución',
            'icono': 'fa-car',
            'orden_visualizacion': 4
        },
        {
            'nombre': 'Otro',
            'codigo': 'OTRO',
            'descripcion': 'Activos que no se clasifican en las categorías anteriores',
            'icono': 'fa-box',
            'orden_visualizacion': 99
        }
    ]

    for cat in categorias_iniciales:
        connection.execute(
            sa.text("""
                INSERT INTO categoria_activo
                (nombre, codigo, descripcion, icono, activa, orden_visualizacion, created_at, updated_at)
                VALUES
                (:nombre, :codigo, :descripcion, :icono, 1, :orden, NOW(), NOW())
            """),
            {
                'nombre': cat['nombre'],
                'codigo': cat['codigo'],
                'descripcion': cat['descripcion'],
                'icono': cat['icono'],
                'orden': cat['orden_visualizacion']
            }
        )

    print(f"   [OK] {len(categorias_iniciales)} categorias iniciales creadas")

    # ===== 6. Crear atributos para Equipos Biomédicos =====
    print("\n[6/6] Creando atributos para categoría 'Equipos Biomédicos'...")

    # Obtener ID de la categoría Biomédicos
    result = connection.execute(
        sa.text("SELECT id FROM categoria_activo WHERE codigo = 'BIOMEDICO'")
    )
    categoria_biomedico_id = result.fetchone()[0]

    atributos_biomedicos = [
        {
            'nombre': 'voltaje',
            'etiqueta': 'Voltaje',
            'descripcion': 'Voltaje de operación del equipo',
            'tipo_dato': 'numero',
            'es_requerido': False,
            'unidad_medida': 'V',
            'orden': 1
        },
        {
            'nombre': 'frecuencia',
            'etiqueta': 'Frecuencia',
            'descripcion': 'Frecuencia de operación del equipo',
            'tipo_dato': 'numero',
            'es_requerido': False,
            'unidad_medida': 'Hz',
            'orden': 2
        },
        {
            'nombre': 'clasificacion_riesgo',
            'etiqueta': 'Clasificación de Riesgo',
            'descripcion': 'Clasificación de riesgo según normativa INVIMA',
            'tipo_dato': 'lista',
            'es_requerido': True,
            'opciones_json': '["I", "IIA", "IIB", "III"]',
            'orden': 3
        },
        {
            'nombre': 'tecnologia_predominante',
            'etiqueta': 'Tecnología Predominante',
            'descripcion': 'Tecnología principal del equipo',
            'tipo_dato': 'lista',
            'es_requerido': False,
            'opciones_json': '["Electromecánico", "Electrónico", "Mecánico", "Hidráulico", "Neumático", "Eléctrico"]',
            'orden': 4
        },
        {
            'nombre': 'requiere_calibracion',
            'etiqueta': '¿Requiere Calibración?',
            'descripcion': 'Indica si el equipo requiere calibración periódica',
            'tipo_dato': 'booleano',
            'es_requerido': False,
            'valor_por_defecto': '0',
            'orden': 5
        },
        {
            'nombre': 'periodicidad_mantenimiento',
            'etiqueta': 'Periodicidad de Mantenimiento',
            'descripcion': 'Frecuencia recomendada para mantenimiento preventivo',
            'tipo_dato': 'lista',
            'es_requerido': False,
            'opciones_json': '["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"]',
            'orden': 6
        },
        {
            'nombre': 'vida_util',
            'etiqueta': 'Vida Útil',
            'descripcion': 'Vida útil estimada del equipo en años',
            'tipo_dato': 'numero',
            'es_requerido': False,
            'unidad_medida': 'años',
            'valor_por_defecto': '10',
            'orden': 7
        },
        {
            'nombre': 'registro_invima',
            'etiqueta': 'Registro INVIMA',
            'descripcion': 'Número de registro INVIMA del equipo',
            'tipo_dato': 'texto',
            'es_requerido': False,
            'orden': 8
        },
        {
            'nombre': 'fabricante_autorizado',
            'etiqueta': 'Fabricante Autorizado',
            'descripcion': 'Nombre del fabricante autorizado',
            'tipo_dato': 'texto',
            'es_requerido': False,
            'orden': 9
        },
        {
            'nombre': 'fecha_ultima_calibracion',
            'etiqueta': 'Fecha Última Calibración',
            'descripcion': 'Fecha de la última calibración realizada',
            'tipo_dato': 'fecha',
            'es_requerido': False,
            'orden': 10
        }
    ]

    for attr in atributos_biomedicos:
        connection.execute(
            sa.text("""
                INSERT INTO atributo_definicion
                (categoria_id, nombre, etiqueta, descripcion, tipo_dato, es_requerido,
                 unidad_medida, opciones_json, valor_por_defecto, orden_visualizacion,
                 activo, created_at, updated_at)
                VALUES
                (:categoria_id, :nombre, :etiqueta, :descripcion, :tipo_dato, :es_requerido,
                 :unidad_medida, :opciones_json, :valor_por_defecto, :orden,
                 1, NOW(), NOW())
            """),
            {
                'categoria_id': categoria_biomedico_id,
                'nombre': attr['nombre'],
                'etiqueta': attr['etiqueta'],
                'descripcion': attr['descripcion'],
                'tipo_dato': attr['tipo_dato'],
                'es_requerido': attr['es_requerido'],
                'unidad_medida': attr.get('unidad_medida'),
                'opciones_json': attr.get('opciones_json'),
                'valor_por_defecto': attr.get('valor_por_defecto'),
                'orden': attr['orden']
            }
        )

    print(f"   [OK] {len(atributos_biomedicos)} atributos creados para 'Equipos Biomedicos'")

    print("\n" + "=" * 80)
    print("[OK] FASE 2.1 COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    print("\nResumen de cambios:")
    print("  - 3 nuevas tablas: categoria_activo, atributo_definicion, atributo_valor")
    print("  - 1 campo agregado: activos.categoria_id")
    print(f"  - {len(categorias_iniciales)} categorias iniciales pobladas")
    print(f"  - {len(atributos_biomedicos)} atributos para Equipos Biomedicos")
    print("  - Sistema EAV con columnas tipadas e indexadas")
    print("\nEl sistema ahora soporta atributos dinamicos personalizados por categoria.\n")


def downgrade():
    print("Revirtiendo FASE 2.1: Sistema de Atributos Dinamicos...")

    # Eliminar FK y columna de activos
    op.drop_constraint('fk_activos_categoria', 'activos', type_='foreignkey')
    op.drop_index('ix_activos_categoria', table_name='activos')
    op.drop_column('activos', 'categoria_id')

    # Eliminar tabla atributo_valor
    op.drop_index('idx_valor_activo_def', table_name='atributo_valor')
    op.drop_index('ix_atributo_valor_booleano', table_name='atributo_valor')
    op.drop_index('ix_atributo_valor_fecha', table_name='atributo_valor')
    op.drop_index('ix_atributo_valor_numerico', table_name='atributo_valor')
    op.drop_index('ix_atributo_valor_def', table_name='atributo_valor')
    op.drop_index('ix_atributo_valor_activo', table_name='atributo_valor')
    op.drop_table('atributo_valor')

    # Eliminar tabla atributo_definicion
    op.drop_index('ix_atributo_def_orden', table_name='atributo_definicion')
    op.drop_index('ix_atributo_def_activo', table_name='atributo_definicion')
    op.drop_index('ix_atributo_def_categoria', table_name='atributo_definicion')
    op.drop_table('atributo_definicion')

    # Eliminar tabla categoria_activo
    op.drop_index('ix_categoria_activo_orden', table_name='categoria_activo')
    op.drop_index('ix_categoria_activo_activa', table_name='categoria_activo')
    op.drop_index('ix_categoria_activo_codigo', table_name='categoria_activo')
    op.drop_table('categoria_activo')

    print("[OK] FASE 2.1 revertida exitosamente")
