"""
Script para agregar la columna 'nombre_firmante' a la tabla 'firmas'.
Ejecutar este script una sola vez para actualizar la base de datos existente.

Fecha: 2025-11-22
Autor: David Cardoza + Claude
"""

from app import create_app
from app.extensions import db

def agregar_columna_nombre_firmante():
    """Agrega la columna nombre_firmante a la tabla firmas."""
    app = create_app()

    with app.app_context():
        try:
            # Verificar si estamos usando SQLite o MySQL
            db_type = db.engine.dialect.name
            print(f"[INFO] Base de datos detectada: {db_type}")

            if db_type == 'sqlite':
                # SQLite: Verificar si la columna ya existe
                result = db.session.execute(db.text("PRAGMA table_info(firmas)"))
                columns = [row[1] for row in result.fetchall()]

                if 'nombre_firmante' in columns:
                    print("[OK] La columna 'nombre_firmante' ya existe en la tabla 'firmas'.")
                    return

                # Agregar columna en SQLite
                print("[EJECUTANDO] Agregando columna 'nombre_firmante' a la tabla 'firmas'...")
                db.session.execute(db.text(
                    "ALTER TABLE firmas ADD COLUMN nombre_firmante VARCHAR(200)"
                ))
                db.session.commit()
                print("[OK] Columna 'nombre_firmante' agregada exitosamente (SQLite).")

            elif db_type == 'mysql':
                # MySQL: Verificar si la columna ya existe
                result = db.session.execute(db.text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "AND TABLE_NAME = 'firmas' "
                    "AND COLUMN_NAME = 'nombre_firmante'"
                ))

                if result.fetchone():
                    print("[OK] La columna 'nombre_firmante' ya existe en la tabla 'firmas'.")
                    return

                # Agregar columna en MySQL
                print("[EJECUTANDO] Agregando columna 'nombre_firmante' a la tabla 'firmas'...")
                db.session.execute(db.text(
                    "ALTER TABLE firmas ADD COLUMN nombre_firmante VARCHAR(200) AFTER firma_base64"
                ))
                db.session.commit()
                print("[OK] Columna 'nombre_firmante' agregada exitosamente (MySQL).")

            else:
                print(f"[WARNING] Base de datos '{db_type}' no soportada por este script.")
                return

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al agregar la columna: {str(e)}")
            raise

if __name__ == '__main__':
    print("=" * 70)
    print("MIGRACION: Agregar campo 'nombre_firmante' a tabla 'firmas'")
    print("=" * 70)
    agregar_columna_nombre_firmante()
    print("=" * 70)
    print("[OK] Migracion completada exitosamente!")
    print("=" * 70)
