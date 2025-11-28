from app import create_app
from init_db import register_commands

# Crea la instancia de la aplicación usando la fábrica
app = create_app()

# Registra los comandos CLI (como 'init-db')
register_commands(app)

if __name__ == '__main__':
    # Cuando se ejecuta con 'python run.py', se inicia el servidor de desarrollo.
    # Cuando se usa 'flask run', esta parte no se ejecuta.
    app.run(debug=True)
