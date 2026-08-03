"""Agregar tabla movimiento_historico para auditoría de movimientos

Revision ID: a1b2c3d4e5f6
Revises: 052bdc72c29f
Create Date: 2025-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '052bdc72c29f'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla movimiento_historico
    op.create_table('movimiento_historico',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('movimiento_id', sa.Integer(), nullable=False),
        sa.Column('campo_modificado', sa.String(length=100), nullable=False),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_nuevo', sa.Text(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('tipo_operacion', sa.String(length=50), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['movimiento_id'], ['movimientos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices para mejorar performance de consultas
    op.create_index('idx_movimiento_timestamp', 'movimiento_historico', ['movimiento_id', 'timestamp'], unique=False)
    op.create_index('idx_campo_timestamp', 'movimiento_historico', ['campo_modificado', 'timestamp'], unique=False)
    op.create_index(op.f('ix_movimiento_historico_campo_modificado'), 'movimiento_historico', ['campo_modificado'], unique=False)
    op.create_index(op.f('ix_movimiento_historico_movimiento_id'), 'movimiento_historico', ['movimiento_id'], unique=False)
    op.create_index(op.f('ix_movimiento_historico_timestamp'), 'movimiento_historico', ['timestamp'], unique=False)


def downgrade():
    # Eliminar índices
    op.drop_index(op.f('ix_movimiento_historico_timestamp'), table_name='movimiento_historico')
    op.drop_index(op.f('ix_movimiento_historico_movimiento_id'), table_name='movimiento_historico')
    op.drop_index(op.f('ix_movimiento_historico_campo_modificado'), table_name='movimiento_historico')
    op.drop_index('idx_campo_timestamp', table_name='movimiento_historico')
    op.drop_index('idx_movimiento_timestamp', table_name='movimiento_historico')

    # Eliminar tabla
    op.drop_table('movimiento_historico')
