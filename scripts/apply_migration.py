"""
Script para aplicar una migración SQL específica.

Uso:
    python apply_migration.py <ruta_del_archivo.sql>
"""
import sys
from pathlib import Path
from sqlalchemy import text
from app import create_app, db

def apply_migration(sql_file):
    """Ejecuta un archivo de migración SQL."""
    app = create_app()
    with app.app_context():
        print(f"Aplicando migración desde: {sql_file}")
        
        if not Path(sql_file).exists():
            print(f"Error: El archivo '{sql_file}' no se encuentra.")
            return

        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        try:
            with db.engine.connect() as connection:
                connection.execute(text(sql_content))
                connection.commit()
            print("Migración aplicada exitosamente.")
        except Exception as e:
            print(f"Error al aplicar la migración: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python apply_migration.py <ruta_del_archivo.sql>")
        sys.exit(1)
    
    sql_file_path = sys.argv[1]
    apply_migration(sql_file_path)