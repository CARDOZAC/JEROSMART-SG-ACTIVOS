"""
Script temporal para aplicar la migracion FASE 2.1
"""
from app import create_app, db
from flask_migrate import upgrade

app = create_app()

with app.app_context():
    try:
        print("Iniciando aplicacion de migracion...")
        upgrade()
        print("[OK] Migracion aplicada exitosamente")
    except Exception as e:
        print(f"[ERROR] Error al aplicar migracion: {e}")
        import traceback
        traceback.print_exc()
