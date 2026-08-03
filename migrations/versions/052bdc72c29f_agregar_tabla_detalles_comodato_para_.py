"""Agregar tabla detalles_comodato para gestión de contratos de comodato

Revision ID: 052bdc72c29f
Revises: f1d2e3d4c5b6
Create Date: 2025-12-09 12:10:23.008415

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '052bdc72c29f'
down_revision = 'f1d2e3d4c5b6'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla detalles_comodato
    op.create_table('detalles_comodato',
    sa.Column('movimiento_id', sa.Integer(), nullable=False),
    sa.Column('proveedor_id', sa.Integer(), nullable=True),
    sa.Column('comodante_nombre', sa.String(length=200), nullable=False),
    sa.Column('comodante_nit', sa.String(length=50), nullable=False),
    sa.Column('comodante_direccion', sa.String(length=200), nullable=True),
    sa.Column('comodante_telefono', sa.String(length=50), nullable=True),
    sa.Column('comodante_email', sa.String(length=100), nullable=True),
    sa.Column('comodante_representante', sa.String(length=200), nullable=True),
    sa.Column('comodante_cedula_representante', sa.String(length=50), nullable=True),
    sa.Column('comodatario_nombre', sa.String(length=200), nullable=False),
    sa.Column('comodatario_nit', sa.String(length=50), nullable=False),
    sa.Column('comodatario_direccion', sa.String(length=200), nullable=True),
    sa.Column('comodatario_representante', sa.String(length=200), nullable=True),
    sa.Column('comodatario_cedula_representante', sa.String(length=50), nullable=True),
    sa.Column('numero_contrato', sa.String(length=100), nullable=False),
    sa.Column('fecha_inicio', sa.Date(), nullable=False),
    sa.Column('fecha_fin', sa.Date(), nullable=False),
    sa.Column('plazo_meses', sa.Integer(), nullable=True),
    sa.Column('renovacion_automatica', sa.Boolean(), nullable=True),
    sa.Column('objeto_comodato', sa.Text(), nullable=False),
    sa.Column('uso_permitido', sa.Text(), nullable=True),
    sa.Column('restricciones', sa.Text(), nullable=True),
    sa.Column('mantenimiento_cargo', sa.String(length=100), nullable=True),
    sa.Column('seguros_cargo', sa.String(length=100), nullable=True),
    sa.Column('condiciones_devolucion', sa.Text(), nullable=True),
    sa.Column('lugar_devolucion', sa.String(length=200), nullable=True),
    sa.Column('requiere_verificacion_tecnica', sa.Boolean(), nullable=True),
    sa.Column('valor_comercial_referencial', sa.Float(), nullable=True),
    sa.Column('ubicacion_bien', sa.String(length=200), nullable=False),
    sa.Column('responsable_interno_nombre', sa.String(length=150), nullable=False),
    sa.Column('responsable_interno_cedula', sa.String(length=50), nullable=False),
    sa.Column('responsable_interno_cargo', sa.String(length=100), nullable=True),
    sa.Column('responsable_interno_area', sa.String(length=100), nullable=True),
    sa.Column('responsable_interno_telefono', sa.String(length=50), nullable=True),
    sa.Column('responsable_interno_email', sa.String(length=100), nullable=True),
    sa.Column('incluye_capacitacion', sa.Boolean(), nullable=True),
    sa.Column('incluye_mantenimiento_preventivo', sa.Boolean(), nullable=True),
    sa.Column('incluye_soporte_tecnico', sa.Boolean(), nullable=True),
    sa.Column('observaciones_adicionales', sa.Text(), nullable=True),
    sa.Column('estado_comodato', sa.String(length=50), nullable=False),
    sa.Column('renovaciones_json', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['movimiento_id'], ['movimientos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['proveedor_id'], ['proveedores.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('movimiento_id')
    )

    # Crear índices
    with op.batch_alter_table('detalles_comodato', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_detalles_comodato_estado_comodato'), ['estado_comodato'], unique=False)
        batch_op.create_index(batch_op.f('ix_detalles_comodato_fecha_fin'), ['fecha_fin'], unique=False)
        batch_op.create_index(batch_op.f('ix_detalles_comodato_fecha_inicio'), ['fecha_inicio'], unique=False)
        batch_op.create_index(batch_op.f('ix_detalles_comodato_movimiento_id'), ['movimiento_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_detalles_comodato_numero_contrato'), ['numero_contrato'], unique=False)
        batch_op.create_index(batch_op.f('ix_detalles_comodato_proveedor_id'), ['proveedor_id'], unique=False)


def downgrade():
    # Eliminar tabla detalles_comodato
    with op.batch_alter_table('detalles_comodato', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_detalles_comodato_proveedor_id'))
        batch_op.drop_index(batch_op.f('ix_detalles_comodato_numero_contrato'))
        batch_op.drop_index(batch_op.f('ix_detalles_comodato_movimiento_id'))
        batch_op.drop_index(batch_op.f('ix_detalles_comodato_fecha_inicio'))
        batch_op.drop_index(batch_op.f('ix_detalles_comodato_fecha_fin'))
        batch_op.drop_index(batch_op.f('ix_detalles_comodato_estado_comodato'))

    op.drop_table('detalles_comodato')
