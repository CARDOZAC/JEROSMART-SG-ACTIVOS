"""
Script para agregar la columna updated_by a la tabla atributo_valor en MySQL.
Ejecutar una sola vez para actualizar el esquema de la base de datos.

Este script es seguro de ejecutar múltiples veces - verifica si la columna existe antes de agregarla.
"""
import sys
from app import create_app, db
from sqlalchemy import text, inspect

def main():
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("  Migración: Agregar columna 'updated_by' a atributo_valor")
        print("=" * 60)

        inspector = inspect(db.engine)

        # Verificar si la tabla existe
        if 'atributo_valor' not in inspector.get_table_names():
            print("\n⚠  ERROR: La tabla 'atributo_valor' no existe.")
            print("   Ejecuta primero init_db.py para crear las tablas.")
            return 1

        # Verificar si la columna ya existe
        columns = [col['name'] for col in inspector.get_columns('atributo_valor')]

        print(f"\n📋 Columnas actuales en 'atributo_valor': {len(columns)}")
        for col_name in columns:
            print(f"   - {col_name}")

        if 'updated_by' in columns:
            print("\n✅ La columna 'updated_by' YA EXISTE en la tabla.")
            print("   No se requiere migración.")
            return 0

        print("\n⚠  La columna 'updated_by' NO existe.")
        print("⏳ Agregando columna 'updated_by' a la tabla 'atributo_valor'...\n")

        try:
            # Agregar la columna updated_by como NULLABLE con foreign key
            sql = text("""
                ALTER TABLE atributo_valor
                ADD COLUMN updated_by INT NULL
            """)

            db.session.execute(sql)
            db.session.commit()

            print("✅ Paso 1/2: Columna 'updated_by' agregada exitosamente.")

            # Ahora intentar agregar la foreign key
            try:
                sql_fk = text("""
                    ALTER TABLE atributo_valor
                    ADD CONSTRAINT fk_atributo_valor_updated_by
                    FOREIGN KEY (updated_by) REFERENCES usuarios(id) ON DELETE SET NULL
                """)

                db.session.execute(sql_fk)
                db.session.commit()
                print("✅ Paso 2/2: Foreign key a 'usuarios' creada exitosamente.")

            except Exception as e_fk:
                print(f"⚠  Paso 2/2: No se pudo crear la foreign key: {e_fk}")
                print("   La columna funciona sin FK, pero es recomendable agregarla manualmente.")

            print("\n" + "=" * 60)
            print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            print("\n   Ahora puedes eliminar activos sin errores.")
            print("   Reinicia la aplicación para aplicar los cambios.\n")
            return 0

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERROR al agregar la columna: {e}")
            print("\nPor favor, ejecuta manualmente esta consulta SQL en tu base de datos:")
            print("   ALTER TABLE atributo_valor ADD COLUMN updated_by INT NULL;")
            return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
