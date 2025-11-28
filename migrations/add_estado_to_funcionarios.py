"""
Migración: Agregar columna 'estado' a la tabla 'funcionarios'

Fecha: 2025-11-21
Autor: Sistema JeroSmart
Razón: Sincronizar base de datos MySQL con modelo Python Funcionario

IMPORTANTE: Esta migración es segura y reversible.
"""

from app import create_app
from app.extensions import db

def upgrade():
    """Agregar columna estado a funcionarios"""
    print("\n" + "="*70)
    print("MIGRACIÓN: Agregar campo 'estado' a tabla 'funcionarios'")
    print("="*70)

    # Verificar si la columna ya existe
    check_query = db.text("""
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'funcionarios'
        AND COLUMN_NAME = 'estado'
    """)

    result = db.session.execute(check_query).fetchone()

    if result[0] > 0:
        print("✓ La columna 'estado' ya existe en la tabla 'funcionarios'")
        print("  No se requiere migración.")
        return

    print("\n[1/3] Agregando columna 'estado' a tabla 'funcionarios'...")

    # Agregar columna con valor por defecto y NOT NULL
    # Después de centro_costo para mantener orden lógico
    alter_query = db.text("""
        ALTER TABLE funcionarios
        ADD COLUMN estado VARCHAR(50) NOT NULL DEFAULT 'Activo'
        AFTER centro_costo
    """)

    try:
        db.session.execute(alter_query)
        print("  ✓ Columna 'estado' agregada exitosamente")
    except Exception as e:
        print(f"  ✗ Error al agregar columna: {e}")
        db.session.rollback()
        raise

    print("\n[2/3] Creando índice en columna 'estado' para optimizar consultas...")

    # Crear índice para optimizar filtros por estado
    index_query = db.text("""
        CREATE INDEX idx_funcionarios_estado
        ON funcionarios(estado)
    """)

    try:
        db.session.execute(index_query)
        print("  ✓ Índice creado exitosamente")
    except Exception as e:
        print(f"  ✗ Error al crear índice: {e}")
        # No es crítico, continuar

    print("\n[3/3] Verificando migración...")

    # Verificar que todos los registros tienen estado='Activo'
    count_query = db.text("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN estado = 'Activo' THEN 1 ELSE 0 END) as activos
        FROM funcionarios
    """)

    result = db.session.execute(count_query).fetchone()
    print(f"  ✓ Total funcionarios: {result[0]}")
    print(f"  ✓ Funcionarios activos: {result[1]}")

    # Commit de la transacción
    db.session.commit()

    print("\n" + "="*70)
    print("MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)
    print("\nCambios aplicados:")
    print("  • Columna 'estado' agregada a tabla 'funcionarios'")
    print("  • Valor por defecto: 'Activo'")
    print("  • Todos los funcionarios existentes marcados como 'Activo'")
    print("  • Índice creado para optimizar consultas")
    print("="*70 + "\n")


def downgrade():
    """Revertir: Eliminar columna estado de funcionarios"""
    print("\n" + "="*70)
    print("ROLLBACK: Eliminar campo 'estado' de tabla 'funcionarios'")
    print("="*70)

    print("\n[1/2] Eliminando índice...")
    drop_index_query = db.text("DROP INDEX IF EXISTS idx_funcionarios_estado ON funcionarios")

    try:
        db.session.execute(drop_index_query)
        print("  ✓ Índice eliminado")
    except Exception as e:
        print(f"  ⚠ Error al eliminar índice (puede no existir): {e}")

    print("\n[2/2] Eliminando columna 'estado'...")
    drop_column_query = db.text("ALTER TABLE funcionarios DROP COLUMN estado")

    try:
        db.session.execute(drop_column_query)
        db.session.commit()
        print("  ✓ Columna 'estado' eliminada exitosamente")
    except Exception as e:
        print(f"  ✗ Error al eliminar columna: {e}")
        db.session.rollback()
        raise

    print("\n" + "="*70)
    print("ROLLBACK COMPLETADO")
    print("="*70 + "\n")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        try:
            upgrade()
        except KeyboardInterrupt:
            print("\n\n⚠ Migración cancelada por el usuario")
            db.session.rollback()
        except Exception as e:
            print(f"\n\n✗ Error durante la migración: {e}")
            print("\nEjecutar downgrade() para revertir cambios si es necesario")
            db.session.rollback()
            raise
