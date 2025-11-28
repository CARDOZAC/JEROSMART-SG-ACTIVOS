import pytest
from app import create_app, db
from app.models import User

@pytest.fixture(scope='module')
def test_app():
    """Crea una instancia de la aplicación para pruebas."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """Crea un cliente de pruebas para interactuar con la aplicación."""
    return test_app.test_client()

@pytest.fixture(scope='module')
def new_user():
    """Crea un usuario de prueba."""
    user = User(email='test@example.com', rol='User')
    user.set_password('password123')
    return user
