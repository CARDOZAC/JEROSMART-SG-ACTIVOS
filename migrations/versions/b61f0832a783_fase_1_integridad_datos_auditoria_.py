"""fase_1_integridad_datos_auditoria_completa

FASE 1: Integridad de Datos (CRÍTICO)
- Sistema de Conciliación Física (Anti-Activo Fantasma)
- Auditoría Histórica Completa (Trazabilidad Legal)
- Robustez de DocumentoAdjunto (Integridad Criptográfica)

Revision ID: b61f0832a783
Revises: 8978b78c4852
Create Date: 2025-11-24 07:26:16.407555

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b61f0832a783'
down_revision = '8978b78c4852'
branch_labels = None
depends_on = None


def upgrade():
    # ===== FASE 1.1: Sistema de Conciliación Física en Activos =====
    print("Aplicando FASE 1.1: Sistema de Conciliación Física...")

    # Agregar campos de conciliación física
    op.add_column('activos', sa.Column('estado_conciliacion', sa.String(length=20),
                                       nullable=False, server_default='Pendiente'))
    op.add_column('activos', sa.Column('fecha_ultima_verificacion', sa.DateTime(), nullable=True))
    op.add_column('activos', sa.Column('usuario_ultima_verificacion_id', sa.Integer(), nullable=True))
    op.add_column('activos', sa.Column('notas_verificacion', sa.Text(), nullable=True))

    # Crear índice en estado_conciliacion para consultas rápidas
    op.create_index('ix_activos_estado_conciliacion', 'activos', ['estado_conciliacion'], unique=False)

    # Crear FK a usuarios para el verificador
    op.create_foreign_key(
        'fk_activos_usuario_verificador',
        'activos', 'usuarios',
        ['usuario_ultima_verificacion_id'], ['id'],
        ondelete='SET NULL'
    )

    # ===== FASE 1.2: Tabla de Auditoría Histórica Completa =====
    print("Aplicando FASE 1.2: Auditoría Histórica Completa...")

    op.create_table(
        'activo_historico',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activo_id', sa.Integer(), nullable=False),
        sa.Column('campo_modificado', sa.String(length=100), nullable=False),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_nuevo', sa.Text(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('tipo_operacion', sa.String(length=50), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices para consultas eficientes
    op.create_index('ix_activo_historico_activo_id', 'activo_historico', ['activo_id'], unique=False)
    op.create_index('ix_activo_historico_campo_modificado', 'activo_historico', ['campo_modificado'], unique=False)
    op.create_index('ix_activo_historico_timestamp', 'activo_historico', ['timestamp'], unique=False)
    op.create_index('idx_activo_timestamp', 'activo_historico', ['activo_id', 'timestamp'], unique=False)
    op.create_index('idx_campo_timestamp', 'activo_historico', ['campo_modificado', 'timestamp'], unique=False)

    # Crear FK a activos y usuarios
    op.create_foreign_key(
        'fk_activo_historico_activo',
        'activo_historico', 'activos',
        ['activo_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_activo_historico_usuario',
        'activo_historico', 'usuarios',
        ['usuario_id'], ['id'],
        ondelete='SET NULL'
    )

    # ===== FASE 1.3: Robustez de DocumentoAdjunto =====
    print("Aplicando FASE 1.3: Robustez de DocumentoAdjunto...")

    # Agregar nuevas columnas para integridad y relaciones ampliadas
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('activo_id', sa.Integer(), nullable=True))
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('movimiento_id', sa.Integer(), nullable=True))
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('nombre_archivo_original', sa.String(length=200), nullable=True))
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('checksum_sha256', sa.String(length=64), nullable=True))
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('usuario_carga_id', sa.Integer(), nullable=True))
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('tamano_bytes', sa.Integer(), nullable=True))
    op.add_column('documentos_adjuntos_biomedicos',
                  sa.Column('mime_type', sa.String(length=100), nullable=True))

    # Cambiar fecha_carga a DateTime (era Date)
    op.alter_column('documentos_adjuntos_biomedicos', 'fecha_carga',
                    existing_type=sa.Date(),
                    type_=sa.DateTime(),
                    existing_nullable=True)

    # Hacer hoja_vida_id nullable (antes era NOT NULL)
    op.alter_column('documentos_adjuntos_biomedicos', 'hoja_vida_id',
                    existing_type=sa.Integer(),
                    nullable=True)

    # Crear índices
    op.create_index('ix_documentos_adjuntos_biomedicos_activo_id',
                    'documentos_adjuntos_biomedicos', ['activo_id'], unique=False)
    op.create_index('ix_documentos_adjuntos_biomedicos_movimiento_id',
                    'documentos_adjuntos_biomedicos', ['movimiento_id'], unique=False)
    op.create_index('ix_documentos_adjuntos_biomedicos_tipo_documento',
                    'documentos_adjuntos_biomedicos', ['tipo_documento'], unique=False)
    op.create_index('ix_documentos_adjuntos_biomedicos_checksum_sha256',
                    'documentos_adjuntos_biomedicos', ['checksum_sha256'], unique=False)

    # Crear FKs a activos, movimientos y usuarios
    op.create_foreign_key(
        'fk_documentos_activo',
        'documentos_adjuntos_biomedicos', 'activos',
        ['activo_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_documentos_movimiento',
        'documentos_adjuntos_biomedicos', 'movimientos',
        ['movimiento_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_documentos_usuario_carga',
        'documentos_adjuntos_biomedicos', 'usuarios',
        ['usuario_carga_id'], ['id'],
        ondelete='SET NULL'
    )

    print("FASE 1 completada exitosamente!")
    print("   - Sistema de conciliacion fisica implementado")
    print("   - Auditoria historica completa activada")
    print("   - Integridad criptografica de documentos habilitada")


def downgrade():
    # ===== FASE 1.3: Revertir DocumentoAdjunto =====
    print("Revirtiendo FASE 1.3...")

    op.drop_constraint('fk_documentos_usuario_carga', 'documentos_adjuntos_biomedicos', type_='foreignkey')
    op.drop_constraint('fk_documentos_movimiento', 'documentos_adjuntos_biomedicos', type_='foreignkey')
    op.drop_constraint('fk_documentos_activo', 'documentos_adjuntos_biomedicos', type_='foreignkey')

    op.drop_index('ix_documentos_adjuntos_biomedicos_checksum_sha256',
                  table_name='documentos_adjuntos_biomedicos')
    op.drop_index('ix_documentos_adjuntos_biomedicos_tipo_documento',
                  table_name='documentos_adjuntos_biomedicos')
    op.drop_index('ix_documentos_adjuntos_biomedicos_movimiento_id',
                  table_name='documentos_adjuntos_biomedicos')
    op.drop_index('ix_documentos_adjuntos_biomedicos_activo_id',
                  table_name='documentos_adjuntos_biomedicos')

    op.alter_column('documentos_adjuntos_biomedicos', 'hoja_vida_id',
                    existing_type=sa.Integer(),
                    nullable=False)

    op.alter_column('documentos_adjuntos_biomedicos', 'fecha_carga',
                    existing_type=sa.DateTime(),
                    type_=sa.Date(),
                    existing_nullable=True)

    op.drop_column('documentos_adjuntos_biomedicos', 'mime_type')
    op.drop_column('documentos_adjuntos_biomedicos', 'tamano_bytes')
    op.drop_column('documentos_adjuntos_biomedicos', 'usuario_carga_id')
    op.drop_column('documentos_adjuntos_biomedicos', 'checksum_sha256')
    op.drop_column('documentos_adjuntos_biomedicos', 'nombre_archivo_original')
    op.drop_column('documentos_adjuntos_biomedicos', 'movimiento_id')
    op.drop_column('documentos_adjuntos_biomedicos', 'activo_id')

    # ===== FASE 1.2: Eliminar tabla de auditoría =====
    print("Revirtiendo FASE 1.2...")

    op.drop_constraint('fk_activo_historico_usuario', 'activo_historico', type_='foreignkey')
    op.drop_constraint('fk_activo_historico_activo', 'activo_historico', type_='foreignkey')

    op.drop_index('idx_campo_timestamp', table_name='activo_historico')
    op.drop_index('idx_activo_timestamp', table_name='activo_historico')
    op.drop_index('ix_activo_historico_timestamp', table_name='activo_historico')
    op.drop_index('ix_activo_historico_campo_modificado', table_name='activo_historico')
    op.drop_index('ix_activo_historico_activo_id', table_name='activo_historico')

    op.drop_table('activo_historico')

    # ===== FASE 1.1: Revertir conciliación física =====
    print("Revirtiendo FASE 1.1...")

    op.drop_constraint('fk_activos_usuario_verificador', 'activos', type_='foreignkey')
    op.drop_index('ix_activos_estado_conciliacion', table_name='activos')

    op.drop_column('activos', 'notas_verificacion')
    op.drop_column('activos', 'usuario_ultima_verificacion_id')
    op.drop_column('activos', 'fecha_ultima_verificacion')
    op.drop_column('activos', 'estado_conciliacion')

    print("FASE 1 revertida completamente")
