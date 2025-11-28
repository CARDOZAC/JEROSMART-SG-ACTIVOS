"""
Script para limpiar completamente la base de datos MySQL.
Borra todas las tablas y las recrea desde cero.
"""
import os
from run import app
from app.extensions import db
from app.models import (
    User, Funcionario, Proveedor, ClaseActivo, Activo, ActivoAccesorio, HojaVidaBiomedico,
    Movimiento, MovimientoActivo, Accesorio, Firma,
    DocumentoAdjunto, DetalleEntrega, DetalleTraslado,
    DetalleEntradaSalida, DetallePazSalvo, MantenimientoTipo,
    Mantenimiento, MantenimientoFoto
)

def limpiar_base_datos():
    """Borra todas las tablas y las recrea."""
    with app.app_context():
        try:
            print("Desactivando verificaciones de foreign keys...")
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
            db.session.commit()

            print("Borrando todas las tablas...")
            db.drop_all()
            print("Tablas borradas exitosamente.")

            print("\nReactivando verificaciones de foreign keys...")
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
            db.session.commit()

            print("\nCreando todas las tablas desde cero...")
            db.create_all()
            print("Tablas creadas exitosamente.")

            print("\n=== Base de datos limpia y lista para usar! ===")
            print("\nAhora puedes ejecutar: python init_db.py")

        except Exception as e:
            print(f"\nError al limpiar la base de datos: {e}")
            # Reactivar foreign keys aunque haya error
            try:
                db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
                db.session.commit()
            except:
                pass
            raise

if __name__ == '__main__':
    limpiar_base_datos()
