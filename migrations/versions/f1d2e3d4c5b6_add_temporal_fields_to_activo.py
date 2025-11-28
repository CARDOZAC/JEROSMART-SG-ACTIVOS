"""Add temporary income fields to Activo model

Revision ID: f1d2e3d4c5b6
Revises: c50a8b4aaa5e
Create Date: 2025-11-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1d2e3d4c5b6'
down_revision = 'c50a8b4aaa5e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('es_ingreso_temporal', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('fecha_inicio_temporal', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('fecha_fin_temporal', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.drop_column('fecha_fin_temporal')
        batch_op.drop_column('fecha_inicio_temporal')
        batch_op.drop_column('es_ingreso_temporal')

    # ### end Alembic commands ###
