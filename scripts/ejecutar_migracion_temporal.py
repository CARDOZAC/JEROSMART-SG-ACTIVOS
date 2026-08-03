"""
Script para ejecutar la migración de columnas temporales
"""
import pymysql
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'jerosmart_activos'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4'
}

# Conectar a la base de datos
print("Conectando a la base de datos...")
connection = pymysql.connect(**db_config)

try:
    with connection.cursor() as cursor:
        print("Ejecutando migración...")

        # Agregar columnas
        sql = """
        ALTER TABLE activos
        ADD COLUMN es_ingreso_temporal TINYINT(1) DEFAULT 0 NULL COMMENT 'Indica si el activo es un ingreso temporal',
        ADD COLUMN fecha_inicio_temporal DATETIME NULL COMMENT 'Fecha de inicio del ingreso temporal',
        ADD COLUMN fecha_fin_temporal DATETIME NULL COMMENT 'Fecha de fin del ingreso temporal'
        """

        try:
            cursor.execute(sql)
            connection.commit()
            print("[OK] Columnas agregadas exitosamente")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("[WARN] Las columnas ya existen en la base de datos")
            else:
                raise

        # Verificar que las columnas existen
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'activos'
              AND COLUMN_NAME IN ('es_ingreso_temporal', 'fecha_inicio_temporal', 'fecha_fin_temporal')
        """, (db_config['database'],))

        results = cursor.fetchall()
        print(f"\n[OK] Verificacion de columnas:")
        for row in results:
            print(f"  - {row[0]}: {row[1]} | Nullable: {row[2]} | Default: {row[3]}")

        print("\n[OK] Migracion completada exitosamente!")

finally:
    connection.close()
    print("Conexión cerrada.")
