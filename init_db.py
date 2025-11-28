"""
Este módulo define un comando de Flask CLI para inicializar la base de datos.
"""
import os
import json
import click
from flask.cli import with_appcontext
from .app.extensions import db
from .app.models import (User, Funcionario, Proveedor, ClaseActivo, Activo,
                         Movimiento, DetalleEntrega, MovimientoActivo, Accesorio,
                         Firma, DetalleTraslado, DetallePazSalvo)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Limpia los datos existentes y crea nuevas tablas."""
    db_path = db.get_app().config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    if os.path.exists(db_path):
        os.remove(db_path)
        click.echo(f"Base de datos '{db_path}' existente eliminada para empezar limpia.")

    click.echo("-> Creando todas las tablas desde los modelos...")
    db.create_all()
    click.echo("-> Tablas creadas.")

    click.echo("-> Insertando datos de ejemplo (seed)...")
    seed_data()
    
    click.echo(f"\n✅ Base de datos '{db_path}' creada y poblada exitosamente.")
    click.echo("   Admin de prueba -> usuario: 'david.cardoza@clinicaprimavera.com'  |  contraseña: '12345'")


def seed_data():
    """Inserta datos de ejemplo en la base de datos usando SQLAlchemy."""
    try:
        # --- Creación de datos con SQLAlchemy ---
        # Usuario Admin
        admin_user = User(email='david.cardoza@clinicaprimavera.com', cargo='Administrador', area='IT', rol='Admin')
        admin_user.set_password('12345')
        db.session.add(admin_user)

        # Clases de Activo
        clases = ['Equipo Biomédico', 'Equipo Electro-Industrial', 'TICs', 'Muebles y Enseres']
        clase_objects = {name: ClaseActivo(nombre_clase=name) for name in clases}
        for clase in clase_objects.values():
            db.session.add(clase)

        # Funcionarios
        funcionarios = [
            Funcionario(nombres='Ana', apellidos='Pérez', cedula='12345678', cargo='Coordinadora', area='Administración'),
            Funcionario(nombres='Luis', apellidos='García', cedula='87654321', cargo='Jefe de Sistemas', area='Sistemas'),
            Funcionario(nombres='Maria', apellidos='Rodriguez', cedula='11223344', cargo='Enfermera Jefe', area='Hospitalización Piso 3'),
            Funcionario(nombres='Carlos', apellidos='López', cedula='22334455', cargo='Técnico de Mantenimiento', area='Mantenimiento'),
            Funcionario(nombres='Laura', apellidos='Martínez', cedula='33445566', cargo='Auxiliar Administrativa', area='Recursos Humanos')
        ]
        db.session.add_all(funcionarios)

        # Proveedores
        proveedores = [
            Proveedor(razon_social='TecnoSoluciones S.A.S.', nit='900.123.456-7'),
            Proveedor(razon_social='BioEquipos SAS', nit='900.555.123-4')
        ]
        db.session.add_all(proveedores)

        db.session.commit() # Commit para que los objetos tengan ID

        # Activos
        portatil = Activo(
            nombre_activo='Portátil de Desarrollo',
            placa_codigo_interno='TIC-001',
            marca='Dell',
            modelo='Latitude 5420',
            ubicacion='Almacén Principal',
            estado='Pendiente Asignación',
            clase_id=clase_objects['TICs'].id,
            tipo_propiedad='Propio'
        )
        db.session.add(portatil)

        monitor = Activo(
            nombre_activo='Monitor de Signos Vitales',
            placa_codigo_interno='BIO-050',
            marca='Mindray',
            modelo='ePM12',
            ubicacion='Hospitalización Piso 3',
            estado='Operativo',
            clase_id=clase_objects['Equipo Biomédico'].id,
            funcionario_id=3,
            valor_comercial=8200000.00,
            tipo_propiedad='Propio'
        )
        db.session.add(monitor)

        db.session.commit() # Commit para que los activos tengan ID

        # Movimiento de Entrega
        movimiento_entrega = Movimiento(
            tipo_movimiento='Entrega',
            fecha='2025-08-15 11:30:00',
            usuario_id=1,
            observaciones_generales='Entrega inicial de Portátil a Luis García'
        )
        db.session.add(movimiento_entrega)

        detalle_entrega = DetalleEntrega(
            movimiento=movimiento_entrega,
            quien_recibe_nombre='Luis García',
            quien_entrega_nombre='Ana Pérez',
            orden_compra_contrato='OC-2025-151',
            fecha_oc_contrato='2025-08-10',
            objeto_contrato='Suministro de equipo de cómputo',
            tipo_elementos=json.dumps(['Equipos TIC']),
            requiere_montaje=False,
            requiere_capacitacion=False,
            tipo_asignacion='Asignación Directa',
            observaciones_acta='Entrega de portátil para el área de sistemas.'
        )
        db.session.add(detalle_entrega)

        movimiento_activo_entrega = MovimientoActivo(
            movimiento=movimiento_entrega,
            activo=portatil
        )
        db.session.add(movimiento_activo_entrega)

        accesorio_entrega = Accesorio(
            movimiento_activo=movimiento_activo_entrega,
            descripcion='Mouse inalámbrico',
            referencia='Logitech MX',
            serial='MX-123',
            cantidad=1,
            observacion='Conecta por Bluetooth'
        )
        db.session.add(accesorio_entrega)

        firma_entrega = Firma(
            documento_id=movimiento_entrega.id,
            tipo_documento='movimiento',
            rol_firma='Quien_Recibe',
            firma_base64='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...'
        )
        db.session.add(firma_entrega)
        db.session.commit() # Commit movimiento_entrega to get an ID

        db.session.commit()

    except Exception as e:
        click.echo(f"\n❌ Error al poblar la base de datos: {e}")
        db.session.rollback()
        raise

def register_commands(app):
    """Registra los comandos CLI con la aplicación Flask."""
    app.cli.add_command(init_db_command)
