import os
import click
from app import create_app
from init_db import init_db_app

# Crea la instancia de la aplicación usando la fábrica
app = create_app()

@app.cli.command("init-db")
def init_db_cli_command():
    """Limpia los datos existentes y crea nuevas tablas."""
    # Pasamos el objeto 'app' a la función de inicialización
    init_db_app(app)
    click.echo("Base de datos inicializada.")

if __name__ == '__main__':
    # Cuando se ejecuta con 'python run.py', se inicia el servidor de desarrollo.
    # Cuando se usa 'flask run', esta parte no se ejecuta.
    app.run(debug=True)