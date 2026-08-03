# app/db.py
import click
from flask.cli import with_appcontext
from .extensions import db


@click.command("init-db")
@click.option('--si-estoy-seguro', is_flag=True,
              help='Omite la confirmación interactiva. Úsalo solo en scripts.')
@with_appcontext
def init_db_command(si_estoy_seguro):
    """
    Reinicia la base de datos: borra TODAS las tablas y las vuelve a crear.

    Operación destructiva e irreversible. Para cambios de esquema en una base
    con datos usa migraciones (`flask db migrate` / `flask db upgrade`), no
    este comando.
    """
    if not si_estoy_seguro:
        click.echo('ATENCION: esto BORRARA todas las tablas y los datos que contienen.')
        click.echo('Para cambios de esquema conservando los datos usa: flask db upgrade')
        click.confirm('Deseas continuar?', abort=True)

    db.drop_all()
    db.create_all()
    click.echo("Base de datos reinicializada.")
