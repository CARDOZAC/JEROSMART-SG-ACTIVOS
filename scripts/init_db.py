"""
Script de inicialización de la base de datos usando SQLAlchemy ORM.
Este script crea todas las tablas a partir de los modelos definidos en app/models.py
y carga datos de ejemplo para desarrollo.

Buenas prácticas aplicadas ("Petr-Level"):
- **Consistencia de Datos**: Los datos de ejemplo reflejan la lógica de negocio.
  (ej. una entrega actualiza el estado y responsable del activo).
- **Sin "Magic Strings"**: Se usan constantes para roles y tipos de movimiento.
- **Datos Completos**: Se incluyen atributos dinámicos para activos biomédicos.
- **Claridad**: El código es auto-documentado y fácil de seguir.
"""
import os
import json


# ------------------------------------------------------------------------------
# Datos de ejemplo
# ------------------------------------------------------------------------------

# --- Constantes para evitar "Magic Strings" ---
class ROLES:
    ADMIN = 'Admin'
    USER = 'User'

class MOVIMIENTO_TIPO:
    ENTREGA = 'Entrega'
    TRASLADO = 'Traslado'
    PAZ_Y_SALVO = 'Paz y Salvo'
    ENTRADA = 'Entrada'
    SALIDA = 'Salida'
# ------------------------------------------------------------------------------
def seed_data():
    """
    Inserta datos de ejemplo para el entorno de desarrollo usando SQLAlchemy ORM.
    """
    from app.extensions import db
    from app.models import (
        User, Funcionario, Proveedor, ClaseActivo, Activo, ActivoAccesorio,
        HojaVidaBiomedico, Movimiento, MovimientoActivo, Accesorio,
        DetalleEntrega, DetalleTraslado, DetallePazSalvo, MantenimientoTipo, Firma
    )

    print("-> Insertando datos de ejemplo...")

    try:
        # ========================
        # Usuario administrador
        # ========================
        admin_user = User(
            email='activosfijos@jerosmart.local',
            cargo='Administrador',
            area='IT',
            rol=ROLES.ADMIN
        )
        admin_user.set_password('12345')  # Usa el método del modelo
        db.session.add(admin_user)

        # ========================
        # Clases de Activo
        # ========================
        clases = [
            'Equipo Biomédico',
            'Equipo Electro-Industrial',
            'TICs',
            'Muebles y Enseres'
        ]
        clases_objetos = []
        for nombre_clase in clases:
            clase = ClaseActivo(nombre_clase=nombre_clase)
            db.session.add(clase)
            clases_objetos.append(clase)

        # Hacer flush para obtener IDs de las clases
        db.session.flush()
        print(f"   -> Clases de activo creadas: {[c.nombre_clase for c in clases_objetos]}")

        # ========================
        # Funcionarios
        # ========================
        funcionario_luis = Funcionario(
            nombres='Luis',
            apellidos='García',
            cedula='87654321',
            cargo='Jefe de Sistemas',
            area='Sistemas'
        )
        db.session.add(funcionario_luis)

        funcionario_maria = Funcionario(
            nombres='Maria',
            apellidos='Rodriguez',
            cedula='11223344',
            cargo='Enfermera Jefe',
            area='Hospitalización Piso 3'
        )
        db.session.add(funcionario_maria)

        funcionario_carlos = Funcionario(
            nombres='Carlos',
            apellidos='López',
            cedula='22334455',
            cargo='Técnico de Mantenimiento',
            area='Mantenimiento'
        )
        db.session.add(funcionario_carlos)

        funcionario_laura = Funcionario(
            nombres='Laura',
            apellidos='Martínez',
            cedula='33445566',
            cargo='Auxiliar Administrativa',
            area='Recursos Humanos'
        )
        db.session.add(funcionario_laura)

        # ========================
        # Proveedores
        # ========================
        proveedor_bio = Proveedor(
            razon_social='BioEquipos SAS',
            nit='900.555.123-4',
            direccion='Calle 45 #23-10, Bogotá',
            persona_contacto='Juan Pérez',
            numero_contacto='3001234567'
        )
        db.session.add(proveedor_bio)

        # Hacer flush para obtener IDs generados
        db.session.flush()

        # ========================
        # Activos
        # ========================
        # Activo sin asignar (clase TICs)
        portatil = Activo(
            nombre_activo='Portátil de Desarrollo',
            placa_codigo_interno='TIC-001',
            marca='Dell',
            modelo='Latitude 5420', # noqa
            ubicacion='Oficina de Sistemas', # Ubicación final post-entrega
            estado='Operativo', # Estado final post-entrega
            clase_id=clases_objetos[2].id,  # TICs (índice 2)
            funcionario_id=funcionario_luis.id, # Responsable final post-entrega
            tipo_propiedad='Propio'
        )
        db.session.add(portatil)
        db.session.flush()

        # Accesorio del portátil
        acc_portatil = ActivoAccesorio(
            activo_id=portatil.id,
            descripcion='Cargador 65W USB-C',
            marca='Dell'
        )
        db.session.add(acc_portatil)

        # Monitor de signos vitales (clase Biomédico)
        monitor = Activo(
            nombre_activo='Monitor de Signos Vitales',
            placa_codigo_interno='BIO-050',
            marca='Mindray',
            modelo='ePM12',
            ubicacion='Hospitalización Piso 3',
            estado='Operativo',
            clase_id=clases_objetos[0].id,  # Equipo Biomédico (índice 0)
            funcionario_id=funcionario_maria.id,
            valor_comercial=8200000.00,
            tipo_propiedad='Propio',
            # Atributos dinámicos cruciales para equipos biomédicos
            atributos_dinamicos_json=json.dumps({
                "registro_invima": "2022DM-0012345",
                "clasificacion_riesgo": "IIa",
                "clasificacion_biomedica": "Diagnóstico",
                "fabricante": "Mindray",
                "pais_origen": "China",
                "vida_util": "8",
                "frecuencia_mantenimiento": "Anual",
                "requiere_calibracion": "Sí",
                "voltaje_operacion": "100-240V AC",
                "potencia": "75",
                "ultimo_mantenimiento": None
            })
        )
        db.session.add(monitor)
        db.session.flush()

        # Accesorio del monitor
        acc_monitor = ActivoAccesorio(
            activo_id=monitor.id,
            descripcion='Sensor SpO2 Adulto'
        )
        db.session.add(acc_monitor)

        # ========================
        # Movimiento de Entrega
        # ========================
        fecha_mov = '2025-08-15 11:30:00'
        mov_entrega = Movimiento(
            tipo_movimiento=MOVIMIENTO_TIPO.ENTREGA,
            fecha=fecha_mov,
            usuario_id=admin_user.id,
            observaciones_generales='Entrega inicial de Portátil a Luis García'
        )
        db.session.add(mov_entrega)
        db.session.flush()

        # Enlazar el activo al movimiento
        mov_activo = MovimientoActivo(
            movimiento_id=mov_entrega.id,
            activo_id=portatil.id
        )
        db.session.add(mov_activo)
        db.session.flush()

        # Detalles de la entrega
        detalle_entrega = DetalleEntrega(
            movimiento_id=mov_entrega.id,
            quien_recibe_nombre='Luis García',
            quien_entrega_nombre='Ana Pérez',
            orden_compra_contrato='OC-2025-151',
            fecha_oc_contrato='2025-08-10',
            objeto_contrato='Suministro de equipo de cómputo',
            tipo_elementos=json.dumps(['Equipos TIC']),
            requiere_montaje=False,
            requiere_capacitacion=False,
            tipo_asignacion='Asignación Directa'
        )
        db.session.add(detalle_entrega)

        # Accesorios de la entrega
        accesorio_mov = Accesorio(
            movimiento_activo_id=mov_activo.id,
            descripcion='Mouse inalámbrico',
            referencia='Logitech MX',
            serial='MX-123',
            cantidad=1,
            observacion='Conecta por Bluetooth'
        )
        db.session.add(accesorio_mov)

        # Firma del movimiento
        firma_entrega = Firma(
            documento_id=mov_entrega.id,
            tipo_documento='movimiento',
            rol_firma='Quien_Recibe',
            firma_base64='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' # Pixel transparente
        )
        db.session.add(firma_entrega)

        # ========================
        # Movimiento de Traslado
        # ========================
        mov_traslado = Movimiento(
            tipo_movimiento=MOVIMIENTO_TIPO.TRASLADO,
            fecha='2025-08-16 09:00:00',
            usuario_id=admin_user.id,
            observaciones_generales='Traslado de monitor de piso'
        )
        db.session.add(mov_traslado)
        db.session.flush()

        # Enlazar el activo (monitor) al movimiento
        mov_activo_traslado = MovimientoActivo(
            movimiento_id=mov_traslado.id,
            activo_id=monitor.id
        )
        db.session.add(mov_activo_traslado)

        # Detalles del traslado
        detalle_traslado = DetalleTraslado(
            movimiento_id=mov_traslado.id,
            ubicacion_inicial='Hospitalización Piso 3',
            ubicacion_final='Hospitalización Piso 4',
            origen_responsable_nombre='Maria Rodriguez',
            origen_responsable_cc='11223344',
            origen_responsable_cargo='Enfermera Jefe',
            nuevo_responsable_nombre='Maria Rodriguez',
            nuevo_responsable_cc='11223344',
            nuevo_responsable_cargo='Enfermera Jefe'
        )
        db.session.add(detalle_traslado)

        # ========================
        # Movimiento de Paz y Salvo
        # ========================
        mov_paz_salvo = Movimiento(
            tipo_movimiento=MOVIMIENTO_TIPO.PAZ_Y_SALVO,
            fecha='2025-08-17 14:00:00',
            usuario_id=admin_user.id,
            observaciones_generales='Desvinculación de Maria Rodriguez'
        )
        db.session.add(mov_paz_salvo)
        db.session.flush()

        # Detalles de paz y salvo
        detalle_paz = DetallePazSalvo(
            movimiento_id=mov_paz_salvo.id,
            funcionario_desvinculado_id=funcionario_maria.id,
            observaciones_paz_salvo='Devolución de todos los activos a satisfacción.'
        )
        db.session.add(detalle_paz)

        # ========================
        # Tipos de Mantenimiento
        # ========================
        tipos_mantenimiento = [
            'Reporte Monitor Signos Vitales',
            'Reporte Cama Hospitalaria',
            'Reporte Calentador de Paciente',
            'Por Definir'
        ]
        for nombre_tipo in tipos_mantenimiento:
            tipo = MantenimientoTipo(nombre=nombre_tipo)
            db.session.add(tipo)

        # Confirmar toda la transacción
        db.session.commit()
        print("-> Datos de ejemplo insertados exitosamente.")

    except Exception as e:
        print(f"\nERROR: Error al insertar datos de ejemplo: {e}")
        db.session.rollback()
        raise


# ------------------------------------------------------------------------------
# Orquestación
# ------------------------------------------------------------------------------
def init_db_app(app):
    """
    Crea y configura la base de datos desde cero usando SQLAlchemy.
    Esta función se debe ejecutar en el contexto de la aplicación Flask.
    """
    with app.app_context():
        from app.extensions import db
        # Importar todos los modelos para que SQLAlchemy los conozca
        from app.models import (
            User, Funcionario, Proveedor, ClaseActivo, Activo, ActivoAccesorio, HojaVidaBiomedico,
            Movimiento, MovimientoActivo, Accesorio, Firma,
            DocumentoAdjunto, DetalleEntrega, DetalleTraslado,
            DetalleEntradaSalida, DetallePazSalvo, MantenimientoTipo,
            Mantenimiento, MantenimientoFoto
        )

        # Obtener la ruta de la base de datos
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///activos_fijos_v4.db')
        db_path = db_uri.replace('sqlite:///', '')

        # Eliminar base de datos existente si existe
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Base de datos '{db_path}' existente eliminada para empezar limpia.")

        print("-> Creando todas las tablas desde los modelos de SQLAlchemy...")
        db.create_all()
        print("-> Tablas creadas exitosamente.")

        # Insertar datos de ejemplo
        seed_data()

        print(f"\n=== Base de datos '{db_path}' creada y poblada exitosamente ===")
        print("   Admin de prueba -> usuario: 'activosfijos@jerosmart.local'  |  contrasena: '12345'")


# ------------------------------------------------------------------------------
# Ejecución directa del script
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Este bloque se ejecuta cuando se corre el script directamente
    from run import app
    init_db_app(app)
