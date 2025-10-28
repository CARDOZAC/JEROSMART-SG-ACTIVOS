"""
Este archivo centraliza la inicialización de las extensiones de Flask
para evitar importaciones circulares y mantener el código organizado.

Siguiendo el patrón de "Application Factory", las extensiones se crean aquí
pero se inicializan en la factory `create_app`.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instancia de la base de datos (ORM)
db = SQLAlchemy()

# Instancia del gestor de sesiones de usuario
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirige a esta vista si un usuario no autenticado intenta acceder a una página protegida.
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"