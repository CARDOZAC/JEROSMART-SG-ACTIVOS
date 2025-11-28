"""add_check_constraint_documentos_relaciones

MEJORA FASE 1.3: CHECK Constraint para Relaciones Polimórficas
Garantiza que cada documento esté relacionado con al menos una entidad:
- hoja_vida_id (Hojas de Vida Biomédicas)
- activo_id (Activos directamente)
- movimiento_id (Movimientos de activos)

Esta validación a nivel de MySQL complementa la validación de aplicación
en SQLAlchemy, protegiendo contra cambios directos en la base de datos.

Revision ID: cbe6127ebdff
Revises: b61f0832a783
Create Date: 2025-11-24 10:19:34.534330

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbe6127ebdff'
down_revision = 'b61f0832a783'
branch_labels = None
depends_on = None


def upgrade():
    """
    Añade CHECK constraint para garantizar relaciones polimórficas válidas.
    Solo se aplica en MySQL 8.0.16+, se omite en SQLite para desarrollo.
    """
    bind = op.get_bind()

    # Solo aplicar en MySQL (omitir en SQLite para desarrollo)
    if bind.dialect.name == 'mysql':
        print("Aplicando CHECK constraint en documentos_adjuntos_biomedicos...")

        op.execute("""
            ALTER TABLE documentos_adjuntos_biomedicos
            ADD CONSTRAINT chk_al_menos_una_relacion
            CHECK (
                (hoja_vida_id IS NOT NULL) OR
                (activo_id IS NOT NULL) OR
                (movimiento_id IS NOT NULL)
            )
        """)

        print("OK: CHECK constraint creado exitosamente")
        print("   - Proteccion contra documentos sin relacion")
        print("   - Valida inserciones/actualizaciones directas en MySQL")
    else:
        print(f"OMITIENDO: CHECK constraint no soportado en {bind.dialect.name}")
        print("   - La validacion se mantiene a nivel de aplicacion (SQLAlchemy)")


def downgrade():
    """
    Remueve el CHECK constraint si existe.
    """
    bind = op.get_bind()

    if bind.dialect.name == 'mysql':
        print("Revirtiendo CHECK constraint...")

        try:
            op.execute("""
                ALTER TABLE documentos_adjuntos_biomedicos
                DROP CHECK chk_al_menos_una_relacion
            """)
            print("OK: CHECK constraint eliminado")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo eliminar constraint (posiblemente no existe): {e}")
    else:
        print(f"OMITIENDO: No hay CHECK constraint en {bind.dialect.name}")
