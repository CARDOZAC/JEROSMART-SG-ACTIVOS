# Gestión de Activos Fijos

Esta es una aplicación web Flask para la gestión de activos fijos, diseñada para llevar un control detallado del ciclo de vida de los activos dentro de una organización.

## Características

- **Gestión de Activos:** Creación, edición y visualización de activos.
- **Movimientos:** Registro de entregas, traslados, entradas/salidas y paz y salvos.
- **Gestión de Funcionarios y Proveedores:** Catálogos para funcionarios y proveedores.
- **Autenticación de Usuarios:** Sistema de login para usuarios registrados.
- **Base de Datos:** Utiliza SQLite con SQLAlchemy ORM y Flask-Migrate para el manejo de la base de datos.

## Requisitos

- Python 3.8+
- `pip` para la gestión de paquetes

## Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd <NOMBRE-DEL-REPOSITORIO>
    ```

2.  **Crear y activar un entorno virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar las dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuración de la Base de Datos

1.  **Inicializar la base de datos:**

    La primera vez que ejecute la aplicación, necesitará crear la base de datos y las tablas.

    ```bash
    flask init-db
    ```

    Este comando creará el archivo de la base de datos `activos_fijos_v4.db` y lo llenará con algunos datos de ejemplo.

2.  **Aplicar migraciones:**

    Si realiza cambios en los modelos de `app/models.py`, necesitará generar y aplicar una migración.

    ```bash
    flask db migrate -m "Descripción de los cambios"
    flask db upgrade
    ```

## Ejecución de la Aplicación

Para iniciar el servidor de desarrollo, ejecute:

```bash
flask run
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

## Estructura del Proyecto

```
.
├── app/                  # Directorio principal de la aplicación
│   ├── __init__.py       # Factory de la aplicación
│   ├── models.py         # Modelos de la base de datos
│   ├── extensions.py     # Extensiones de Flask
│   ├── config.py         # Configuración
│   ├── auth/             # Blueprint de autenticación
│   ├── activos/          # Blueprint de activos
│   ├── movimientos/      # Blueprint de movimientos
│   └── ...
├── migrations/           # Directorio de migraciones de la base de datos
├── tests/                # Directorio de pruebas
├── venv/                 # Entorno virtual
├── .flaskenv             # Variables de entorno para Flask
├── requirements.txt      # Dependencias de Python
├── run.py                # Punto de entrada para ejecutar la aplicación
└── init_db.py            # Script para inicializar la base de datos
```
