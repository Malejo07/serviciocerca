"""Pruebas de la API: códigos HTTP y mensajes legibles."""
import pytest
from fastapi.testclient import TestClient

from app.main import crear_app


@pytest.fixture
def cliente():
    # Cada prueba usa una app nueva con la red vacía: las pruebas no se afectan entre sí.
    return TestClient(crear_app())


def registrar_basico(cliente):
    cliente.post("/api/nodos", json={"id": "B1", "nombre": "Base Norte", "tipo": "BASE"})
    cliente.post("/api/nodos", json={"id": "Z1", "nombre": "Chapinero", "tipo": "ZONA"})


def test_red_inicia_vacia(cliente):
    r = cliente.get("/api/red")
    assert r.status_code == 200
    assert r.json() == {"nodos": [], "tecnicos": [], "trayectos": []}


def test_registrar_y_consultar_red(cliente):
    registrar_basico(cliente)
    assert cliente.post("/api/tecnicos", json={"id": "T1", "nombre": "Ana", "base_id": "B1"}).status_code == 201
    r = cliente.post("/api/trayectos", json={"origen": "B1", "destino": "Z1", "minutos": 10})
    assert r.status_code == 201
    assert len(r.json()) == 2  # bidireccional por defecto

    red = cliente.get("/api/red").json()
    assert {n["id"] for n in red["nodos"]} == {"B1", "Z1"}
    assert red["tecnicos"][0]["base_id"] == "B1"
    assert len(red["trayectos"]) == 2


def test_nodo_duplicado_409(cliente):
    registrar_basico(cliente)
    r = cliente.post("/api/nodos", json={"id": "z1", "nombre": "Otra", "tipo": "ZONA"})
    assert r.status_code == 409
    assert "Z1" in r.json()["error"]


def test_tipo_invalido_400(cliente):
    r = cliente.post("/api/nodos", json={"id": "X1", "nombre": "X", "tipo": "HOSPITAL"})
    assert r.status_code == 400
    assert "BASE o ZONA" in r.json()["error"]


@pytest.mark.parametrize("minutos", [0, -5])
def test_peso_invalido_400(cliente, minutos):
    registrar_basico(cliente)
    r = cliente.post("/api/trayectos", json={"origen": "B1", "destino": "Z1", "minutos": minutos})
    assert r.status_code == 400
    assert "mayor que 0" in r.json()["error"]


def test_peso_no_numerico_400(cliente):
    registrar_basico(cliente)
    r = cliente.post("/api/trayectos", json={"origen": "B1", "destino": "Z1", "minutos": "diez"})
    assert r.status_code == 400
    assert "error" in r.json()


def test_trayecto_nodo_inexistente_404(cliente):
    registrar_basico(cliente)
    r = cliente.post("/api/trayectos", json={"origen": "B1", "destino": "Z99", "minutos": 5})
    assert r.status_code == 404
    assert "Z99" in r.json()["error"]


def test_campo_faltante_400(cliente):
    r = cliente.post("/api/nodos", json={"id": "Z1"})
    assert r.status_code == 400
    assert r.json()["detalles"]


def test_cargar_ejemplo_y_vaciar(cliente):
    assert cliente.post("/api/red/ejemplo").status_code == 200
    red = cliente.get("/api/red").json()
    assert len(red["nodos"]) == 9
    assert len(red["tecnicos"]) == 3

    cliente.delete("/api/red")
    assert cliente.get("/api/red").json()["nodos"] == []
