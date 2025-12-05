"""
Script para verificar tablas existentes en MySQL y comparar con modelos SQLAlchemy
Autor: Claude Code - Profesional en Activos Fijos Clínicos
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from sqlalchemy import inspect, text

def verificar_tablas():
    """Verifica qué tablas existen en MySQL vs las definidas en modelos"""

    app = create_app()

    with app.app_context():
        # Obtener inspector de la base de datos
        inspector = inspect(db.engine)

        # Tablas existentes en MySQL
        tablas_existentes = set(inspector.get_table_names())

        # Tablas definidas en modelos SQLAlchemy
        tablas_modelos = set([table.name for table in db.metadata.sorted_tables])

        print("=" * 80)
        print("VERIFICACIÓN DE TABLAS EN MYSQL")
        print("=" * 80)
        print()

        print(f"📊 Total de tablas definidas en modelos: {len(tablas_modelos)}")
        print(f"📊 Total de tablas existentes en MySQL: {len(tablas_existentes)}")
        print()

        # Tablas que existen en MySQL
        if tablas_existentes:
            print("✅ TABLAS QUE YA EXISTEN EN MYSQL:")
            print("-" * 80)
            for tabla in sorted(tablas_existentes):
                print(f"  ✓ {tabla}")
            print()

        # Tablas que faltan crear
        tablas_faltantes = tablas_modelos - tablas_existentes
        if tablas_faltantes:
            print("❌ TABLAS QUE FALTAN POR CREAR:")
            print("-" * 80)
            for tabla in sorted(tablas_faltantes):
                print(f"  ✗ {tabla}")
            print()

        # Tablas que existen pero no están en modelos (obsoletas)
        tablas_obsoletas = tablas_existentes - tablas_modelos
        if tablas_obsoletas:
            print("⚠️  TABLAS EN MYSQL NO DEFINIDAS EN MODELOS (posiblemente obsoletas):")
            print("-" * 80)
            for tabla in sorted(tablas_obsoletas):
                print(f"  ? {tabla}")
            print()

        print("=" * 80)

        # Guardar resultado en archivo
        with open("reporte_tablas_mysql.txt", "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE DE TABLAS EN MYSQL\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Total tablas en modelos: {len(tablas_modelos)}\n")
            f.write(f"Total tablas en MySQL: {len(tablas_existentes)}\n\n")

            if tablas_existentes:
                f.write("TABLAS EXISTENTES EN MYSQL:\n")
                f.write("-" * 80 + "\n")
                for tabla in sorted(tablas_existentes):
                    f.write(f"  {tabla}\n")
                f.write("\n")

            if tablas_faltantes:
                f.write("TABLAS QUE FALTAN POR CREAR:\n")
                f.write("-" * 80 + "\n")
                for tabla in sorted(tablas_faltantes):
                    f.write(f"  {tabla}\n")
                f.write("\n")

        print("\n💾 Reporte guardado en: reporte_tablas_mysql.txt")

if __name__ == "__main__":
    verificar_tablas()
