"""Agregar datos de contrato a activos ajenos

Estas 8 columnas ya se escribían desde el formulario de edición de activos
(`app/activos/routes.py`), pero no existían en el modelo ni en la base de datos:
`setattr` sobre un atributo no mapeado no persiste nada, así que los datos de
contrato se perdían en silencio y las alertas de vencimiento del dashboard de
activos ajenos siempre salían vacías.

Revision ID: b58456050078
Revises: a1b2c3d4e5f6
Create Date: 2026-08-03 09:57:21.302745

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b58456050078'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nit_propietario', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('telefono_propietario', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('email_propietario', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('numero_contrato', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('fecha_inicio_contrato', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('fecha_fin_contrato', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('observaciones_contrato', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('costo_mensual', sa.Float(), nullable=True))
        # Índice para las consultas de alertas de vencimiento del dashboard
        batch_op.create_index(
            batch_op.f('ix_activos_fecha_fin_contrato'),
            ['fecha_fin_contrato'],
            unique=False
        )


def downgrade():
    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_activos_fecha_fin_contrato'))
        batch_op.drop_column('costo_mensual')
        batch_op.drop_column('observaciones_contrato')
        batch_op.drop_column('fecha_fin_contrato')
        batch_op.drop_column('fecha_inicio_contrato')
        batch_op.drop_column('numero_contrato')
        batch_op.drop_column('email_propietario')
        batch_op.drop_column('telefono_propietario')
        batch_op.drop_column('nit_propietario')
