def test_app_exists(test_app):
    """Prueba que la aplicación de Flask se crea correctamente."""
    assert test_app is not None

def test_app_is_testing(test_app):
    """Prueba que la aplicación está en modo de prueba."""
    assert test_app.config['TESTING']

def test_home_page_redirects(test_client):
    """Prueba que la página de inicio redirige a la página de login."""
    response = test_client.get('/')
    assert response.status_code == 302
