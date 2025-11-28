"""
Script para limpiar la migracion fallida de FASE 2.1
"""
from app import create_app, db

app = create_app()

with app.app_context():
    try:
        print("Limpiando tablas parciales de FASE 2.1...")
        print("=" * 50)

        # Eliminar tablas en orden correcto (por dependencias FK)

        # 0. Primero eliminar columna categoria_id de activos (tiene FK a categoria_activo)
        print("\nVerificando columna categoria_id en activos...")
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'activos'
            AND COLUMN_NAME = 'categoria_id'
        """))
        if result.fetchone()[0] > 0:
            print("  Eliminando FK fk_activos_categoria...")
            try:
                db.session.execute(db.text("ALTER TABLE activos DROP FOREIGN KEY fk_activos_categoria"))
                db.session.commit()
                print("    [OK] FK eliminada")
            except:
                print("    [INFO] FK no existe")

            print("  Eliminando columna categoria_id...")
            db.session.execute(db.text("ALTER TABLE activos DROP COLUMN categoria_id"))
            db.session.commit()
            print("  [OK] Columna eliminada")
        else:
            print("  [INFO] Columna no existe")

        # 1. Primero atributo_valor (depende de activos y atributo_definicion)
        print("\nVerificando tabla atributo_valor...")
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'atributo_valor'
        """))
        if result.fetchone()[0] > 0:
            print("  Eliminando tabla atributo_valor...")
            db.session.execute(db.text("DROP TABLE atributo_valor"))
            db.session.commit()
            print("  [OK] Tabla eliminada")
        else:
            print("  [INFO] Tabla no existe")

        # 2. Luego atributo_definicion (depende de categoria_activo)
        print("\nVerificando tabla atributo_definicion...")
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'atributo_definicion'
        """))
        if result.fetchone()[0] > 0:
            print("  Eliminando tabla atributo_definicion...")
            db.session.execute(db.text("DROP TABLE atributo_definicion"))
            db.session.commit()
            print("  [OK] Tabla eliminada")
        else:
            print("  [INFO] Tabla no existe")

        # 3. Finalmente categoria_activo
        print("\nVerificando tabla categoria_activo...")
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'categoria_activo'
        """))
        if result.fetchone()[0] > 0:
            print("  Eliminando tabla categoria_activo...")
            db.session.execute(db.text("DROP TABLE categoria_activo"))
            db.session.commit()
            print("  [OK] Tabla eliminada")
        else:
            print("  [INFO] Tabla no existe")


        print("\n" + "=" * 50)
        print("[OK] Limpieza completada exitosamente")
        print("=" * 50)
        print("\nAhora puedes ejecutar apply_migration.py nuevamente")

    except Exception as e:
        db.session.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
