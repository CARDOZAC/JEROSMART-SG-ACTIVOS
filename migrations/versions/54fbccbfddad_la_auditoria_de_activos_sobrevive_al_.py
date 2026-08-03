"""La auditoria de activos sobrevive al borrado

Revision ID: 54fbccbfddad
Revises: a2d771e166af
Create Date: 2026-08-03 14:59:53.488802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54fbccbfddad'
down_revision = 'a2d771e166af'
branch_labels = None
depends_on = None


def upgrade():
    # Mismo defecto que se corrigió en movimiento_historico (revisión
    # a2d771e166af): la FK tenía ON DELETE CASCADE, así que al borrar un activo
    # desaparecía todo su historial de auditoría, incluido el registro que
    # documentaba esa misma eliminación. La columna se conserva como entero
    # simple y la integridad se gestiona desde la aplicación.
    op.drop_constraint('activo_historico_ibfk_1', 'activo_historico', type_='foreignkey')


def downgrade():
    op.create_foreign_key(
        'activo_historico_ibfk_1', 'activo_historico', 'activos',
        ['activo_id'], ['id'], ondelete='CASCADE'
    )
