
import sqlite3
import os

# Obtener la ruta absoluta del directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'activos_fijos_v4.db')

def crear_proveedor_generico():
    """
    Asegura que el proveedor 'No Aplica' exista en la base de datos.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar si el proveedor 'No Aplica' ya existe
        cursor.execute("SELECT id FROM proveedores WHERE nombre = ?", ('No Aplica',))
        proveedor = cursor.fetchone()

        if proveedor is None:
            print("Creando proveedor genérico 'No Aplica'...")
            # Insertar el proveedor genérico
            cursor.execute("""
                INSERT INTO proveedores (nombre, nit, direccion, telefono, email, tipo_proveedor)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('No Aplica', '00000000-0', 'N/A', '000', 'noaplica@local.host', 'N/A'))
            conn.commit()
            print("Proveedor 'No Aplica' creado exitosamente.")
        else:
            print("El proveedor 'No Aplica' ya existe.")

        conn.close()

    except sqlite3.Error as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == '__main__':
    crear_proveedor_generico()
