"""
Script para resetear la contraseña del admin
"""
from dotenv import load_dotenv

# IMPORTANTE: Cargar variables de entorno ANTES de importar app
load_dotenv()

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    print("=" * 70)
    print("RESET DE CONTRASEÑA - JEROSMART ACTIVOS")
    print("=" * 70)
    print()

    # Verificar qué base de datos estamos usando
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'mysql' in db_uri:
        print(f"✅ Usando MySQL: {app.config['DB_NAME']}")
    else:
        print(f"⚠️  Usando SQLite: {db_uri}")
    print()

    # Buscar admin
    admin = User.query.filter_by(email='activosfijos@clinicaprimavera.com').first()

    if not admin:
        print("❌ Usuario admin no encontrado")
        print("\nCreando usuario admin...")

        admin = User(
            email='activosfijos@clinicaprimavera.com',
            cargo='Administrador',
            area='IT',
            rol='Admin'
        )
        admin.set_password('12345')
        db.session.add(admin)
        db.session.commit()

        print("✅ Usuario admin creado")
    else:
        print(f"✅ Usuario encontrado: {admin.email}")
        print(f"   Rol: {admin.rol}")
        print(f"   Cargo: {admin.cargo}")
        print()

        # Resetear contraseña
        print("Reseteando contraseña a '12345'...")
        admin.set_password('12345')
        db.session.commit()
        print("✅ Contraseña actualizada")

    print()
    print("=" * 70)
    print("CREDENCIALES DE ACCESO")
    print("=" * 70)
    print(f"URL:        http://localhost:5000")
    print(f"Email:      activosfijos@clinicaprimavera.com")
    print(f"Contraseña: 12345")
    print("=" * 70)
    print()

    # Verificar contraseña
    print("Verificando contraseña...")
    if admin.check_password('12345'):
        print("✅ La contraseña '12345' funciona correctamente")
    else:
        print("❌ ERROR: La contraseña no funciona")

    print()
    print("=" * 70)
    print("LISTO PARA USAR")
    print("=" * 70)
