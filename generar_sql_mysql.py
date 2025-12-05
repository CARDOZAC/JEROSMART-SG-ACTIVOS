"""
Script para generar SQL de creación de tablas MySQL desde modelos SQLAlchemy
Autor: Claude Code - Profesional en Activos Fijos Clínicos Colombianos
Fecha: 2025-11-28
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql

def generar_sql_mysql():
    """Genera SQL CREATE TABLE para todas las tablas definidas en los modelos"""

    # Crear la aplicación
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("GENERANDO SQL DE CREACIÓN DE TABLAS PARA MYSQL")
        print("=" * 80)
        print()
        print("-- Script generado automáticamente desde modelos SQLAlchemy")
        print("-- Base de datos: jerosmart_activos")
        print("-- Motor: MySQL 8.0+")
        print()
        print("SET FOREIGN_KEY_CHECKS = 0;")
        print()

        # Obtener todas las tablas de los metadatos
        for table in db.metadata.sorted_tables:
            print(f"-- Tabla: {table.name}")
            print(f"DROP TABLE IF EXISTS `{table.name}`;")

            # Generar el CREATE TABLE usando el dialecto de MySQL
            create_table = CreateTable(table).compile(dialect=mysql.dialect())
            sql = str(create_table).strip()

            # Ajustar para MySQL (cambiar tipos si es necesario)
            sql = sql.replace("DATETIME", "DATETIME")
            sql = sql.replace("VARCHAR", "VARCHAR")
            sql = sql.replace("TEXT", "TEXT")
            sql = sql.replace("INTEGER", "INT")
            sql = sql.replace("BOOLEAN", "TINYINT(1)")

            print(f"{sql};")
            print()

        print("SET FOREIGN_KEY_CHECKS = 1;")
        print()
        print("=" * 80)
        print(f"TOTAL DE TABLAS: {len(db.metadata.sorted_tables)}")
        print("=" * 80)

if __name__ == "__main__":
    generar_sql_mysql()
