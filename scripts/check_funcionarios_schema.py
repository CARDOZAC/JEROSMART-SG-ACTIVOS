"""Script temporal para verificar esquema de la tabla funcionarios en MySQL"""
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(db.text('DESCRIBE funcionarios'))
    print("=" * 60)
    print("ESTRUCTURA DE LA TABLA 'funcionarios' EN MySQL")
    print("=" * 60)
    print(f"{'Campo':<25} | {'Tipo':<20} | {'Null':<5} | {'Key':<5} | {'Default'}")
    print("-" * 60)
    for row in result:
        print(f"{row[0]:<25} | {row[1]:<20} | {row[2]:<5} | {row[3]:<5} | {row[4] if row[4] else 'None'}")
    print("=" * 60)
