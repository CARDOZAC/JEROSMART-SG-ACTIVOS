# -*- coding: utf-8 -*-
"""
Script de Migración de Datos para Atributos Dinámicos.

Este script lee los datos del campo obsoleto `atributos_dinamicos_json` 
en el modelo `Activo` y los migra al nuevo sistema EAV (Entity-Attribute-Value)
compuesto por las tablas `CategoriaActivo`, `AtributoDefinicion` y `AtributoValor`.

ADVERTENCIA:
- Realice una copia de seguridad de la base de datos antes de ejecutar.
- Se recomienda ejecutar este script en un entorno de desarrollo o staging primero.
- El script asume que las definiciones de atributos (`AtributoDefinicion`) ya
  existen en la base de datos para las categorías correspondientes.
"""
import os
import sys
import json
from datetime import datetime

# Añadir el directorio raíz del proyecto al path para permitir importaciones de la app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Activo, CategoriaActivo, AtributoDefinicion, AtributoValor

def migrar_atributos_dinamicos():
    """
    Función principal que ejecuta el proceso de migración.
    """
    app = create_app()
    with app.app_context():
        print("--- Iniciando migración de atributos dinámicos de JSON a EAV ---")

        # Buscar activos que tengan datos en el campo JSON
        activos_a_migrar = db.session.scalars(
            db.select(Activo).filter(Activo.atributos_dinamicos_json.is_not(None))
        ).all()

        if not activos_a_migrar:
            print("No se encontraron activos con datos en `atributos_dinamicos_json`. No hay nada que migrar.")
            return

        print(f"Se encontraron {len(activos_a_migrar)} activos para procesar.\n")

        # Contadores para el reporte final
        activos_migrados_count = 0
        activos_fallidos = []
        atributos_migrados_count = 0
        atributos_omitidos_count = 0

        # ID de usuario para auditoría (asumimos ID 1 como usuario del sistema/admin)
        # En un sistema real, esto podría ser un ID de usuario específico para migraciones.
        SYSTEM_USER_ID = 1

        for activo in activos_a_migrar:
            print(f"Procesando Activo ID: {activo.id} (Placa: {activo.placa_codigo_interno})...")
            
            json_data = activo.atributos_dinamicos_json
            if not isinstance(json_data, dict) or not json_data:
                print("  -> Omitido: `atributos_dinamicos_json` está vacío o no es un diccionario.")
                continue

            if not activo.categoria_id:
                print("  -> ERROR: El activo no tiene una categoría asignada. No se pueden migrar sus atributos.")
                activos_fallidos.append({'id': activo.id, 'placa': activo.placa_codigo_interno, 'razon': 'Sin categoría asignada'})
                continue
            
            try:
                for nombre_atributo, valor in json_data.items():
                    if valor is None or valor == '':
                        print(f"  - Atributo '{nombre_atributo}': Omitido (valor vacío).")
                        continue

                    # Buscar la definición del atributo para la categoría del activo
                    definicion = db.session.scalar(
                        db.select(AtributoDefinicion).filter_by(
                            categoria_id=activo.categoria_id,
                            nombre=nombre_atributo
                        )
                    )

                    if not definicion:
                        print(f"  - Atributo '{nombre_atributo}': Omitido (No existe definición para esta categoría).")
                        atributos_omitidos_count += 1
                        continue

                    # Validar el valor antes de insertarlo
                    es_valido, msg_error = definicion.validar_valor(valor)
                    if not es_valido:
                        print(f"  - Atributo '{nombre_atributo}': ERROR de validación - {msg_error} (Valor: {valor}).")
                        atributos_omitidos_count += 1
                        continue

                    # Buscar si ya existe un valor para este atributo
                    valor_obj = db.session.scalar(
                        db.select(AtributoValor).filter_by(
                            activo_id=activo.id,
                            atributo_definicion_id=definicion.id
                        )
                    )

                    if valor_obj:
                        print(f"  - Atributo '{nombre_atributo}': Actualizando valor existente.")
                    else:
                        print(f"  - Atributo '{nombre_atributo}': Creando nuevo valor.")
                        valor_obj = AtributoValor(
                            activo_id=activo.id,
                            atributo_definicion_id=definicion.id,
                            updated_by=SYSTEM_USER_ID
                        )
                        db.session.add(valor_obj)
                    
                    # El setter de la propiedad 'valor' se encarga de la conversión de tipos
                    valor_obj.valor = valor
                    valor_obj.updated_at = datetime.utcnow()
                    
                    atributos_migrados_count += 1

                activos_migrados_count += 1
                # Hacemos commit por cada activo para aislar los errores
                db.session.commit()
                print(f"  -> Activo ID: {activo.id} migrado exitosamente.")

            except Exception as e:
                db.session.rollback()
                print(f"  -> ERROR: Ocurrió un error inesperado al migrar el activo ID {activo.id}. Detalles: {e}")
                activos_fallidos.append({'id': activo.id, 'placa': activo.placa_codigo_interno, 'razon': str(e)})

        print("\n--- Reporte Final de Migración ---")
        print(f"Total de activos procesados: {len(activos_a_migrar)}")
        print(f"Activos migrados exitosamente: {activos_migrados_count}")
        print(f"Activos con errores: {len(activos_fallidos)}")
        if activos_fallidos:
            print("Detalle de activos fallidos:")
            for item in activos_fallidos:
                print(f"  - ID: {item['id']}, Placa: {item['placa']}, Razón: {item['razon']}")
        
        print(f"\nTotal de atributos migrados: {atributos_migrados_count}")
        print(f"Total de atributos omitidos (sin definición o valor inválido): {atributos_omitidos_count}")
        print("--- Migración completada. ---")

if __name__ == '__main__':
    migrar_atributos_dinamicos()
