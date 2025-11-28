"""Add DetalleReporteDanoPerdida table

Revision ID: c50a8b4aaa5e
Revises: 3a3cc952d9ea
Create Date: 2025-11-26 15:16:41.491488

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c50a8b4aaa5e'
down_revision = '3a3cc952d9ea'
branch_labels = None
depends_on = None


def upgrade():
    # Create detalles_reporte_dano_perdida table
    op.create_table('detalles_reporte_dano_perdida',
        sa.Column('movimiento_id', sa.Integer(), nullable=False),
        sa.Column('reporte_tipo', sa.String(length=50), nullable=False),
        sa.Column('fecha_incidente', sa.Date(), nullable=False),
        sa.Column('hora_incidente', sa.String(length=10), nullable=True),
        sa.Column('area_incidente', sa.String(length=200), nullable=False),
        sa.Column('ubicacion_especifica', sa.String(length=200), nullable=True),
        sa.Column('descripcion_incidente', sa.Text(), nullable=False),
        sa.Column('causas_incidente', sa.Text(), nullable=True),
        sa.Column('estado_activo', sa.String(length=50), nullable=False),
        sa.Column('requiere_reparacion', sa.String(length=10), nullable=True),
        sa.Column('costo_estimado', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('garantia_vigente', sa.String(length=10), nullable=True),
        sa.Column('responsable_reporte_nombre', sa.String(length=200), nullable=False),
        sa.Column('responsable_reporte_cc', sa.String(length=50), nullable=False),
        sa.Column('responsable_reporte_cargo', sa.String(length=100), nullable=False),
        sa.Column('responsable_reporte_area', sa.String(length=100), nullable=False),
        sa.Column('responsable_reporte_telefono', sa.String(length=50), nullable=True),
        sa.Column('responsable_reporte_email', sa.String(length=100), nullable=True),
        sa.Column('acciones_tomadas', sa.Text(), nullable=True),
        sa.Column('observaciones_adicionales', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['movimiento_id'], ['movimientos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('movimiento_id')
    )

    # Create index
    op.create_index('ix_detalles_reporte_dano_perdida_movimiento_id', 'detalles_reporte_dano_perdida', ['movimiento_id'], unique=False)


def downgrade():
    # Drop index and table
    op.drop_index('ix_detalles_reporte_dano_perdida_movimiento_id', table_name='detalles_reporte_dano_perdida')
    op.drop_table('detalles_reporte_dano_perdida')
