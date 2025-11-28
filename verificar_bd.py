"""
Script para verificar la configuración de la base de datos y las tablas existentes.
"""
import os
from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("=" * 70)
    print("  DIAGNÓSTICO DE BASE DE DATOS - JeroSmart Activos")
    print("=" * 70)

    # 1. Verificar tipo de BD configurado
    print("\n📊 CONFIGURACIÓN ACTUAL:")
    print(f"   DB_TYPE (variable de entorno): {os.environ.get('DB_TYPE', 'NO CONFIGURADA')}")
    print(f"   Base de datos en uso: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NO CONFIGURADA')}")

    # Detectar tipo de BD por URI
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'mysql' in uri:
        db_type = 'MySQL'
        print(f"   ✅ Tipo detectado: {db_type}")
    elif 'sqlite' in uri:
        db_type = 'SQLite'
        print(f"   ⚠️  Tipo detectado: {db_type} (deberías estar usando MySQL)")
    else:
        db_type = 'Desconocido'
        print(f"   ❌ Tipo detectado: {db_type}")

    print("\n" + "-" * 70)

    # 2. Intentar conectar
    try:
        inspector = inspect(db.engine)
        print("\n✅ CONEXIÓN EXITOSA a la base de datos")

        # 3. Listar todas las tablas
        tables = inspector.get_table_names()
        print(f"\n📋 TABLAS ENCONTRADAS ({len(tables)} en total):")

        for table in sorted(tables):
            print(f"   - {table}")

        # 4. Verificar tabla específica
        print("\n" + "-" * 70)
        print("\n🔍 VERIFICACIÓN DE TABLA 'atributo_valor':")

        if 'atributo_valor' in tables:
            print("   ✅ La tabla 'atributo_valor' EXISTE")

            columns = inspector.get_columns('atributo_valor')
            print(f"\n   Columnas ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"      - {col['name']:<25} {str(col['type']):<20} {nullable}")

            # Verificar columna específica
            col_names = [col['name'] for col in columns]
            if 'updated_by' in col_names:
                print("\n   ✅ La columna 'updated_by' EXISTE")
            else:
                print("\n   ❌ La columna 'updated_by' NO EXISTE")
                print("   → Necesitas ejecutar la migración para agregarla")
        else:
            print("   ❌ La tabla 'atributo_valor' NO EXISTE")
            print("\n   💡 POSIBLES CAUSAS:")
            print("      1. Migraste de SQLite a MySQL pero no creaste las tablas nuevas")
            print("      2. Estás conectado a la base de datos incorrecta")
            print("      3. Las variables de entorno no están configuradas")

        # 5. Verificar otras tablas importantes
        print("\n" + "-" * 70)
        print("\n🔍 VERIFICACIÓN DE TABLAS PRINCIPALES:")

        tablas_importantes = [
            'activos', 'usuarios', 'funcionarios', 'movimientos',
            'categoria_activo', 'atributo_definicion', 'atributo_valor'
        ]

        for tabla in tablas_importantes:
            if tabla in tables:
                # Contar registros
                try:
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
                    print(f"   ✅ {tabla:<25} → {count} registros")
                except Exception as e:
                    print(f"   ✅ {tabla:<25} → (error al contar: {str(e)[:30]})")
            else:
                print(f"   ❌ {tabla:<25} → NO EXISTE")

    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN: {e}")
        print("\n💡 Verifica:")
        print("   - Que MySQL esté corriendo")
        print("   - Que las credenciales sean correctas")
        print("   - Que la base de datos exista")

    print("\n" + "=" * 70)
    print("\n💡 RECOMENDACIONES:")

    if db_type == 'SQLite':
        print("\n   ⚠️  PROBLEMA DETECTADO: Estás usando SQLite pero deberías usar MySQL")
        print("\n   SOLUCIÓN:")
        print("   1. Configura las variables de entorno antes de ejecutar la app:")
        print("      set DB_TYPE=mysql")
        print("      set DB_USER=root")
        print("      set DB_PASSWORD=JeroNimoDaviLex9824.")
        print("      set DB_NAME=jerosmart_activos")
        print("\n   2. O modifica el archivo .env si lo tienes")
        print("\n   3. Reinicia la aplicación")

    elif 'atributo_valor' not in tables:
        print("\n   ⚠️  PROBLEMA DETECTADO: Faltan tablas en MySQL")
        print("\n   SOLUCIÓN:")
        print("   1. Ejecuta init_db.py para crear TODAS las tablas:")
        print("      python init_db.py")
        print("\n   2. O ejecuta la migración manualmente en MySQL:")
        print("      - Abre MySQL Workbench o phpMyAdmin")
        print("      - Ejecuta el script SQL que está en el archivo models.py")

    print("\n" + "=" * 70 + "\n")
