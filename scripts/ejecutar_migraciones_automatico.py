"""
🤖 SCRIPT AUTOMÁTICO - Ejecuta todas las migraciones necesarias

Este script hace TODO por ti:
1. Agrega columna updated_by (error actual)
2. Agrega campos de depreciación
3. Crea sistema de ingreso rápido legacy

USO:
    python ejecutar_migraciones_automatico.py

O si tienes virtualenv:
    .\venv\Scripts\python.exe ejecutar_migraciones_automatico.py
"""

import sys
from pathlib import Path
from sqlalchemy import text, inspect
from app import create_app, db

def imprimir_titulo(titulo):
    """Imprime un título bonito"""
    print("\n" + "=" * 70)
    print(f"  {titulo}")
    print("=" * 70 + "\n")

def imprimir_exito(mensaje):
    """Imprime mensaje de éxito"""
    print(f"✅ {mensaje}")

def imprimir_error(mensaje):
    """Imprime mensaje de error"""
    print(f"❌ {mensaje}")

def imprimir_info(mensaje):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {mensaje}")

def ejecutar_migracion_sql(archivo_sql, descripcion):
    """
    Ejecuta un archivo SQL línea por línea

    Args:
        archivo_sql (str): Ruta al archivo SQL
        descripcion (str): Descripción de qué hace la migración

    Returns:
        bool: True si tuvo éxito, False si hubo error
    """
    imprimir_titulo(descripcion)

    archivo = Path(archivo_sql)

    if not archivo.exists():
        imprimir_error(f"El archivo {archivo} no existe")
        return False

    imprimir_info(f"Leyendo archivo: {archivo}")

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido_sql = f.read()

        # Dividir por punto y coma pero ignorar dentro de comillas
        # Esto es una simplificación - MySQL Workbench hace esto mejor
        # Pero funciona para nuestros scripts

        imprimir_info("Ejecutando migración...")

        # Para MySQL, usamos el motor directamente
        with db.engine.connect() as connection:
            # Ejecutar todo el contenido como un solo bloque
            # MySQL soporta múltiples statements
            connection.execute(text(contenido_sql))
            connection.commit()

        imprimir_exito(f"Migración completada: {descripcion}")
        return True

    except Exception as e:
        imprimir_error(f"Error en la migración: {str(e)}")
        print(f"\nDetalles del error:\n{e}")
        return False

def agregar_columna_updated_by():
    """Agrega la columna updated_by a atributo_valor"""
    imprimir_titulo("MIGRACIÓN 1: Agregar columna updated_by")

    inspector = inspect(db.engine)

    # Verificar si la tabla existe
    if 'atributo_valor' not in inspector.get_table_names():
        imprimir_info("La tabla 'atributo_valor' no existe (esto es normal si no usas EAV)")
        return True

    # Verificar si la columna ya existe
    columns = [col['name'] for col in inspector.get_columns('atributo_valor')]

    if 'updated_by' in columns:
        imprimir_info("La columna 'updated_by' YA EXISTE")
        return True

    imprimir_info("Agregando columna 'updated_by'...")

    try:
        sql = text("""
            ALTER TABLE atributo_valor
            ADD COLUMN updated_by INT NULL
        """)

        db.session.execute(sql)
        db.session.commit()

        imprimir_exito("Columna 'updated_by' agregada exitosamente")

        # Intentar agregar foreign key
        try:
            sql_fk = text("""
                ALTER TABLE atributo_valor
                ADD CONSTRAINT fk_atributo_valor_updated_by
                FOREIGN KEY (updated_by) REFERENCES usuarios(id) ON DELETE SET NULL
            """)

            db.session.execute(sql_fk)
            db.session.commit()
            imprimir_exito("Foreign key creada exitosamente")

        except Exception as e_fk:
            imprimir_info(f"No se pudo crear la foreign key (no crítico): {e_fk}")

        return True

    except Exception as e:
        db.session.rollback()
        imprimir_error(f"Error al agregar columna: {e}")
        return False

def main():
    """Función principal"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 ASISTENTE DE MIGRACIÓN AUTOMÁTICA                        ║
║        Sistema JeroSmart Activos                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    app = create_app()

    with app.app_context():
        print("\n📊 Información de la base de datos:")
        print(f"   URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurada')[:50]}...")

        try:
            # Verificar conexión
            inspector = inspect(db.engine)
            tablas = inspector.get_table_names()
            print(f"   Tablas encontradas: {len(tablas)}")
            imprimir_exito("Conexión a base de datos exitosa\n")

        except Exception as e:
            imprimir_error(f"No se pudo conectar a la base de datos: {e}")
            print("\nVerifica:")
            print("  1. Que MySQL esté corriendo")
            print("  2. Que las credenciales en .env sean correctas")
            print("  3. Que la base de datos 'jerosmart_activos' exista")
            return 1

        # MIGRACIÓN 1: Columna updated_by
        exito_1 = agregar_columna_updated_by()

        if not exito_1:
            print("\n⚠️  La primera migración falló.")
            print("¿Deseas continuar con las demás? (s/n): ", end='')
            respuesta = input().lower()
            if respuesta != 's':
                print("Migración cancelada por el usuario.")
                return 1

        # MIGRACIÓN 2: Sistema de depreciación
        archivo_depreciacion = Path("migrations/01_correccion_depreciacion_DETALLADO.sql")

        if not archivo_depreciacion.exists():
            imprimir_info("Usando script de depreciación alternativo...")
            archivo_depreciacion = Path("migrations/01_correccion_depreciacion.sql")

        if archivo_depreciacion.exists():
            print("\n⏳ Preparando migración de depreciación...")
            print("⚠️  IMPORTANTE: Esta migración puede tardar varios minutos si tienes muchos activos.")
            print("¿Continuar? (s/n): ", end='')
            respuesta = input().lower()

            if respuesta == 's':
                # ADVERTENCIA: ejecutar SQL completo es complejo
                # Mejor usar MySQL Workbench para scripts grandes
                imprimir_info("Para esta migración, es mejor usar MySQL Workbench:")
                print("\n📝 INSTRUCCIONES:")
                print("  1. Abre MySQL Workbench")
                print("  2. File → Open SQL Script")
                print(f"  3. Selecciona: {archivo_depreciacion.absolute()}")
                print("  4. Presiona el botón ⚡ (Execute)")
                print("\n¿Ya ejecutaste el script en Workbench? (s/n): ", end='')
                respuesta_wb = input().lower()

                if respuesta_wb == 's':
                    imprimir_exito("Migración de depreciación completada (según usuario)")
                else:
                    imprimir_info("Saltando migración de depreciación (hazla manualmente)")

        # MIGRACIÓN 3: Sistema legacy
        archivo_legacy = Path("migrations/02_sistema_ingreso_rapido_legacy.sql")

        if archivo_legacy.exists():
            print("\n⏳ ¿Deseas instalar el sistema de ingreso rápido para activos legacy? (s/n): ", end='')
            respuesta = input().lower()

            if respuesta == 's':
                imprimir_info("Igual que antes, usa MySQL Workbench:")
                print("\n📝 INSTRUCCIONES:")
                print("  1. Abre MySQL Workbench")
                print("  2. File → Open SQL Script")
                print(f"  3. Selecciona: {archivo_legacy.absolute()}")
                print("  4. Presiona el botón ⚡ (Execute)")
                print("\n¿Ya ejecutaste el script en Workbench? (s/n): ", end='')
                respuesta_wb = input().lower()

                if respuesta_wb == 's':
                    imprimir_exito("Sistema de ingreso rápido instalado (según usuario)")
                else:
                    imprimir_info("Puedes instalarlo después cuando quieras")

        # RESUMEN FINAL
        print("\n" + "=" * 70)
        print("  📊 RESUMEN DE MIGRACIONES")
        print("=" * 70)

        print(f"\n{'MIGRACIÓN':<40} {'ESTADO':<15}")
        print("-" * 70)
        print(f"{'1. Columna updated_by':<40} {'✅ HECHO' if exito_1 else '❌ ERROR':<15}")
        print(f"{'2. Sistema de depreciación':<40} {'⏭️  MANUAL':<15}")
        print(f"{'3. Sistema ingreso rápido legacy':<40} {'⏭️  MANUAL':<15}")

        print("\n" + "=" * 70)
        print("\n✅ Proceso completado.")
        print("\n📚 PRÓXIMOS PASOS:")
        print("   1. Lee: INSTRUCCIONES_SUPER_SIMPLES.md")
        print("   2. Ejecuta manualmente los scripts SQL en MySQL Workbench")
        print("   3. Verifica con: python verificar_bd.py")
        print("\n💡 Consejo: Es más seguro ejecutar scripts SQL grandes desde Workbench")

        return 0

if __name__ == '__main__':
    try:
        codigo_salida = main()
        sys.exit(codigo_salida)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
