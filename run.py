from dotenv import load_dotenv
from app import create_app

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Crea la instancia de la aplicación usando la fábrica
app = create_app()

if __name__ == "__main__":
    # Cuando se ejecuta con 'python run.py', se inicia el servidor de desarrollo.
    # Cuando se usa 'flask run', esta parte no se ejecuta.
    app.run(debug=True, host="0.0.0.0", port=5000)
