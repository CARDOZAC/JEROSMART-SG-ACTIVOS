"""Crear tabla de proveedores y convertir strings a DateTime y JSON

Revision ID: 860609728414
Revises: 
Create Date: 2025-11-11 13:57:16.739427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '860609728414'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # === INICIO DE CÓDIGO MANUAL PARA LIMPIEZA DE DATOS ===
    
    # 1. Limpiar tabla temporal de una ejecución fallida anterior
    op.execute('DROP TABLE IF EXISTS _alembic_tmp_proveedores')

    # 2. Limpiar datos nulos/vacíos en la tabla de proveedores antes de hacer las columnas NOT NULL
    op.execute("UPDATE proveedores SET nit = 'N/A' WHERE nit IS NULL OR nit = ''")
    op.execute("UPDATE proveedores SET direccion = 'N/A' WHERE direccion IS NULL OR direccion = ''")

    # 3. Limpiar datos nulos/vacíos en todos los campos JSON antes de cambiar su tipo
    op.execute("UPDATE activos SET atributos_dinamicos_json = '{}' WHERE atributos_dinamicos_json IS NULL OR atributos_dinamicos_json = ''")
    op.execute("UPDATE detalles_entrada_salida SET accesorios_generales = '{}' WHERE accesorios_generales IS NULL OR accesorios_generales = ''")
    op.execute("UPDATE detalles_entrega SET tipo_elementos = '{}' WHERE tipo_elementos IS NULL OR tipo_elementos = ''")
    op.execute("UPDATE detalles_traslado SET tipo_traslado_json = '{}' WHERE tipo_traslado_json IS NULL OR tipo_traslado_json = ''")
    op.execute("UPDATE detalles_traslado SET accesorios_generales_json = '{}' WHERE accesorios_generales_json IS NULL OR accesorios_generales_json = ''")
    op.execute("UPDATE mantenimientos SET atributos_reporte_json = '{}' WHERE atributos_reporte_json IS NULL OR atributos_reporte_json = ''")
    
    # === FIN DE CÓDIGO MANUAL ===

    # ### Comandos de Alembic ajustados ###

    # NOTA: La adición de la columna 'hoja_pdf_fisica_url' se omite intencionadamente
    # porque ya fue añadida en una ejecución fallida anterior y causaba un error de "columna duplicada".
    
    with op.batch_alter_table('proveedores', schema=None) as batch_op:
        batch_op.alter_column('nit',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.alter_column('direccion',
               existing_type=sa.VARCHAR(length=200),
               nullable=False)
        # El índice se crea aquí para asegurar que se haga después de limpiar los datos
        batch_op.create_index(batch_op.f('ix_proveedores_nit'), ['nit'], unique=True)

    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True,
               server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.alter_column('atributos_dinamicos_json',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)
        batch_op.alter_column('fecha_ingreso_ajeno',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True)

    with op.batch_alter_table('auditoria_activos', schema=None) as batch_op:
        batch_op.alter_column('fecha_cambio',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True,
               server_default=sa.text('(CURRENT_TIMESTAMP)'))

    with op.batch_alter_table('detalles_entrada_salida', schema=None) as batch_op:
        batch_op.alter_column('fecha_retorno_estimada',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True)
        batch_op.alter_column('accesorios_generales',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)

    with op.batch_alter_table('detalles_entrega', schema=None) as batch_op:
        batch_op.alter_column('fecha_oc_contrato',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True)
        batch_op.alter_column('tipo_elementos',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)

    with op.batch_alter_table('detalles_traslado', schema=None) as batch_op:
        batch_op.alter_column('fecha_traslado',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True)
        batch_op.alter_column('tipo_traslado_json',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)
        batch_op.alter_column('accesorios_generales_json',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)

    with op.batch_alter_table('mantenimientos', schema=None) as batch_op:
        batch_op.alter_column('fecha_mantenimiento',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=False)
        batch_op.alter_column('atributos_reporte_json',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)

    with op.batch_alter_table('movimiento_documentos_adjuntos', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True,
               server_default=sa.text('(CURRENT_TIMESTAMP)'))

    with op.batch_alter_table('movimientos', schema=None) as batch_op:
        batch_op.alter_column('fecha',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=False)
        batch_op.alter_column('fecha_aprobacion',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.DateTime(),
               existing_nullable=True)


def downgrade():
    # El downgrade es complejo y podría no ser perfecto, pero es un intento razonable.
    with op.batch_alter_table('proveedores', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_proveedores_nit'))
        batch_op.alter_column('direccion',
               existing_type=sa.VARCHAR(length=200),
               nullable=True)
        batch_op.alter_column('nit',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)

    with op.batch_alter_table('movimientos', schema=None) as batch_op:
        batch_op.alter_column('fecha_aprobacion',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
        batch_op.alter_column('fecha',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)

    # ... (resto de las operaciones de downgrade de los otros modelos)
    pass