from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(UserMixin):
    """
    Modelo de usuario para Flask-Login que funciona con consultas directas a la BD,
    sin depender de un ORM como SQLAlchemy.
    """
    def __init__(self, id, email, clave_hash, rol, cargo=None, area=None):
        self.id = id
        self.email = email
        self.clave_hash = clave_hash
        self.rol = rol
        self.cargo = cargo
        self.area = area

    @staticmethod
    def set_password(password):
        """Genera un hash de la contraseña."""
        return generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña contra el hash almacenado."""
        return check_password_hash(self.clave_hash, password)

    def __repr__(self):
        return f'<Usuario {self.email}>'