"""
Script para verificar usuarios en la base de datos
"""
from dotenv import load_dotenv

# IMPORTANTE: Cargar variables de entorno ANTES de importar app
load_dotenv()

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    print("=" * 70)
    print("USUARIOS EN LA BASE DE DATOS")
    print("=" * 70)
    print()

    # Verificar qué base de datos estamos usando
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'mysql' in db_uri:
        print(f"✅ Usando MySQL: {app.config['DB_NAME']}")
    else:
        print(f"⚠️  Usando SQLite: {db_uri}")
    print()

    users = User.query.all()

    print("=" * 70)
    print("LISTADO DE USUARIOS")
    print("=" * 70)

    if not users:
        print("❌ NO HAY USUARIOS EN LA BASE DE DATOS")
        print("\nEjecuta: python init_db.py")
    else:
        for u in users:
            print(f"\nID:     {u.id}")
            print(f"Email:  {u.email}")
            print(f"Rol:    {u.rol}")
            print(f"Cargo:  {u.cargo}")
            print(f"Área:   {u.area}")
            print("-" * 70)

        print(f"\nTotal de usuarios: {len(users)}")

        # Probar contraseña del admin
        admin = User.query.filter_by(email='activosfijos@jerosmart.local').first()
        if admin:
            print("\n" + "=" * 70)
            print("PRUEBA DE CONTRASEÑA ADMIN")
            print("=" * 70)
            print(f"Email: {admin.email}")

            # Probar con diferentes contraseñas
            passwords_to_test = ['12345', 'admin', 'password', '123456']

            for pwd in passwords_to_test:
                if admin.check_password(pwd):
                    print(f"✅ La contraseña es: '{pwd}'")
                    break
            else:
                print("❌ Ninguna de las contraseñas comunes funcionó")
                print("\nPara resetear la contraseña, ejecuta:")
                print("python reset_password.py")
