"""fase_2_2_terceros_para_entrada_salida

Revision ID: 3a3cc952d9ea
Revises: 99b868bb70c1
Create Date: 2025-11-24 14:49:15.478612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a3cc952d9ea'
down_revision = '99b868bb70c1'
branch_labels = None
depends_on = None


def upgrade():
    """
    FASE 2.2: Crear tabla terceros para gestión de terceros en movimientos Entrada/Salida
    """
    # 1. Crear tabla terceros
    op.create_table('terceros',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('nombre_completo', sa.String(length=200), nullable=False),
        sa.Column('tipo_documento', sa.String(length=20), nullable=False),
        sa.Column('numero_documento', sa.String(length=50), nullable=False),
        sa.Column('direccion', sa.String(length=200), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices para mejora de rendimiento
    op.create_index(op.f('ix_terceros_tipo'), 'terceros', ['tipo'], unique=False)
    op.create_index(op.f('ix_terceros_activo'), 'terceros', ['activo'], unique=False)

    # 2. Insertar tercero de ejemplo: PACIENTE HOSPITALIZADO
    op.execute("""
        INSERT INTO terceros
        (tipo, nombre_completo, tipo_documento, numero_documento, direccion, telefono, observaciones, activo)
        VALUES
        ('Paciente', 'PACIENTE HOSPITALIZADO', 'NIT', '123456789', 'Calle 123', '575555555',
         'Tercero genérico para registrar activos ajenos de alto costo que los pacientes ingresen cuando están hospitalizados', 1)
    """)

    # 3. Agregar columna tercero_id a detalles_entrada_salida
    op.add_column('detalles_entrada_salida',
        sa.Column('tercero_id', sa.Integer(), nullable=True)
    )

    # Crear índice en tercero_id
    op.create_index(op.f('ix_detalles_entrada_salida_tercero_id'), 'detalles_entrada_salida', ['tercero_id'], unique=False)

    # Crear FK constraint
    op.create_foreign_key(
        'fk_detalles_entrada_salida_tercero',
        'detalles_entrada_salida', 'terceros',
        ['tercero_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """
    Revertir cambios de FASE 2.2
    """
    # 1. Eliminar FK y columna tercero_id de detalles_entrada_salida
    op.drop_constraint('fk_detalles_entrada_salida_tercero', 'detalles_entrada_salida', type_='foreignkey')
    op.drop_index(op.f('ix_detalles_entrada_salida_tercero_id'), table_name='detalles_entrada_salida')
    op.drop_column('detalles_entrada_salida', 'tercero_id')

    # 2. Eliminar índices de terceros
    op.drop_index(op.f('ix_terceros_activo'), table_name='terceros')
    op.drop_index(op.f('ix_terceros_tipo'), table_name='terceros')

    # 3. Eliminar tabla terceros
    op.drop_table('terceros')
