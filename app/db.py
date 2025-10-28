# app/db.py
import click
from flask.cli import with_appcontext
from .extensions import db


def init_db():
    """Función interna para inicializar la base de datos."""
    db.drop_all()
    db.create_all()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Inicializa la base de datos (drop + create_all)."""
    init_db()
    click.echo("✅ Base de datos inicializada correctamente.")
