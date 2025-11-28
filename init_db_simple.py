"""
Script simplificado para inicializar la base de datos.
Solo crea las tablas y las 4 clases de activos necesarias para migración.
"""
from run import app
from app.extensions import db
from app.models import User, ClaseActivo

def init_db_simple():
    """Crea tablas y datos mínimos necesarios."""
    with app.app_context():
        try:
            print("-> Creando todas las tablas desde los modelos...")
            db.create_all()
            print("   Tablas creadas exitosamente.")

            print("\n-> Insertando clases de activos...")

            # Las 4 clases de activos principales
            clases = [
                'Equipo Biomédico',
                'Equipo Electro-Industrial',
                'TICs',
                'Muebles y Enseres'
            ]

            for nombre_clase in clases:
                clase = ClaseActivo(nombre_clase=nombre_clase)
                db.session.add(clase)

            db.session.commit()
            print(f"   Clases de activo creadas: {clases}")

            print("\n-> Creando usuario administrador...")
            admin_user = User(
                email='activosfijos@clinicaprimavera.com',
                cargo='Administrador',
                area='IT',
                rol='Admin'
            )
            admin_user.set_password('12345')
            db.session.add(admin_user)
            db.session.commit()
            print("   Usuario administrador creado exitosamente.")

            print("\n" + "="*70)
            print("BASE DE DATOS CREADA Y LISTA PARA MIGRACION")
            print("="*70)
            print("\nClases de Activos configuradas:")
            print("  1. Equipo Biomédico       -> Módulo Biomédico")
            print("  2. Equipo Electro-Industrial -> Módulo de Mantenimientos")
            print("  3. TICs                   -> Módulo de Mantenimientos")
            print("  4. Muebles y Enseres      -> Módulo de Mantenimientos")
            print("\nCredenciales de acceso:")
            print("  Usuario: activosfijos@clinicaprimavera.com")
            print("  Contrasena: 12345")
            print("\nAhora puedes importar tus activos usando:")
            print("  - Wizard de importacion CSV")
            print("  - Asegurate de usar el 'clase_id' correcto (1-4)")
            print("="*70)

        except Exception as e:
            print(f"\nERROR: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    init_db_simple()
