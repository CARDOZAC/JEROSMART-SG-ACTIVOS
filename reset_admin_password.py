"""
Script para resetear la contraseña del administrador.
Ejecutar con: python reset_admin_password.py
"""

def reset_admin_password():
    """Resetea la contraseña del usuario administrador."""
    from run import app

    with app.app_context():
        from app.extensions import db
        from app.models import User

        # Buscar el usuario admin
        admin = User.query.filter_by(email='activosfijos@jerosmart.local').first()

        if not admin:
            print("❌ No se encontró el usuario administrador.")
            print("   Email buscado: activosfijos@jerosmart.local")
            print("\n📋 Usuarios existentes en la base de datos:")
            users = User.query.all()
            if users:
                for user in users:
                    print(f"   - {user.email} (Rol: {user.rol})")
            else:
                print("   No hay usuarios en la base de datos.")
            return

        # Solicitar nueva contraseña
        print(f"✅ Usuario encontrado: {admin.email}")
        print(f"   Rol: {admin.rol}")
        print(f"   Área: {admin.area}")
        print()

        nueva_password = input("Ingrese la nueva contraseña (o presione Enter para usar '12345'): ").strip()

        if not nueva_password:
            nueva_password = '12345'

        # Cambiar la contraseña
        admin.set_password(nueva_password)
        db.session.commit()

        print()
        print("✅ ¡Contraseña actualizada exitosamente!")
        print()
        print("=" * 50)
        print("   NUEVAS CREDENCIALES")
        print("=" * 50)
        print(f"   Email:      {admin.email}")
        print(f"   Contraseña: {nueva_password}")
        print("=" * 50)

if __name__ == '__main__':
    reset_admin_password()
