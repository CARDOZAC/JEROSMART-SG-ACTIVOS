"""Script temporal para verificar la estructura de la tabla atributo_valor"""
from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)

    # Verificar si la tabla existe
    if 'atributo_valor' in inspector.get_table_names():
        print("✓ La tabla 'atributo_valor' existe")
        print("\nColumnas actuales:")
        columns = inspector.get_columns('atributo_valor')
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']:<30} {str(col['type']):<20} {nullable}")

        # Verificar si falta la columna updated_by
        col_names = [col['name'] for col in columns]
        if 'updated_by' not in col_names:
            print("\n⚠ PROBLEMA: La columna 'updated_by' NO existe en la tabla")
            print("✓ SOLUCIÓN: Necesitas agregar la columna a la base de datos MySQL")
        else:
            print("\n✓ La columna 'updated_by' existe")
    else:
        print("✗ La tabla 'atributo_valor' NO existe")
