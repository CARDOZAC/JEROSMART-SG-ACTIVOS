"""Proveedor en activos y auditoria de borrado persistente

Dos cambios:

1. `activos.proveedor_id`: el formulario de edición de activos ya pedía el
   proveedor, pero la columna no existía en el modelo y la asignación se perdía
   en silencio (mismo patrón que los datos de contrato de la revisión
   b58456050078).

2. Se elimina la FK `movimiento_historico.movimiento_id -> movimientos.id`.
   Tenía ON DELETE CASCADE, de modo que al borrar un movimiento se borraba
   también el registro de auditoría que documentaba esa misma eliminación: los
   borrados no dejaban ningún rastro. La columna se conserva como entero simple
   y la integridad se gestiona desde la aplicación.

Revision ID: a2d771e166af
Revises: b58456050078
Create Date: 2026-08-03 14:41:30.630881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2d771e166af'
down_revision = 'b58456050078'
branch_labels = None
depends_on = None


def upgrade():
    # --- 1. Proveedor del activo ---
    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('proveedor_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_activos_proveedor_id'), ['proveedor_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_activos_proveedor', 'proveedores', ['proveedor_id'], ['id'], ondelete='SET NULL'
        )

    # --- 2. La auditoría de borrado debe sobrevivir al movimiento ---
    op.drop_constraint('movimiento_historico_ibfk_1', 'movimiento_historico', type_='foreignkey')


def downgrade():
    op.create_foreign_key(
        'movimiento_historico_ibfk_1', 'movimiento_historico', 'movimientos',
        ['movimiento_id'], ['id'], ondelete='CASCADE'
    )

    with op.batch_alter_table('activos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_activos_proveedor', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_activos_proveedor_id'))
        batch_op.drop_column('proveedor_id')
