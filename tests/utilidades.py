"""Ayudas para las pruebas de la API: clientes que ya iniciaron sesión con un rol."""
from fastapi.testclient import TestClient

from app.main import crear_app
from app.seguridad import NOMBRE_COOKIE


def cliente_como(usuario: str = "admin", app=None) -> TestClient:
    """Cliente con sesión abierta directamente en el servidor (sin pasar por el hash de la clave)."""
    app = app or crear_app()
    cliente = TestClient(app)
    cliente.cookies.set(NOMBRE_COOKIE, app.state.seguridad.abrir_sesion(usuario))
    return cliente
