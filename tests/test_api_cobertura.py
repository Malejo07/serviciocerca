"""Pruebas de la API de cobertura (F2)."""
import pytest
from fastapi.testclient import TestClient
 
from app.main import crear_app
 
 
@pytest.fixture
def cliente():
    c = TestClient(crear_app())
    c.post("/api/red/ejemplo")
    return c
 
 
def test_zona_cubierta(cliente):
    r = cliente.get("/api/cobertura", params={"origen": "B1", "zona": "Z5"})
    assert r.status_code == 200
    datos = r.json()
    assert datos["cubierta"] is True
    assert datos["camino"] == ["B1", "Z1", "Z4", "Z5"]
    assert datos["traza"][0]["cola"] == ["B1"]
 
 
def test_zona_no_cubierta_red_desconectada(cliente):
    r = cliente.get("/api/cobertura", params={"origen": "B2", "zona": "Z1"})
    assert r.status_code == 200
    assert r.json()["cubierta"] is False
    assert "desconectada" in r.json()["mensaje"]
 
 
def test_zona_sin_conexion(cliente):
    r = cliente.get("/api/cobertura", params={"origen": "B1", "zona": "Z7"})
    assert r.status_code == 200
    assert "no tiene trayectos" in r.json()["mensaje"]
 
 
def test_origen_inexistente_404(cliente):
    r = cliente.get("/api/cobertura", params={"origen": "B99", "zona": "Z1"})
    assert r.status_code == 404
    assert "B99" in r.json()["error"]
 
 
def test_zona_es_base_400(cliente):
    r = cliente.get("/api/cobertura", params={"origen": "B1", "zona": "B2"})
    assert r.status_code == 400
 
 
def test_falta_parametro_400(cliente):
    r = cliente.get("/api/cobertura", params={"origen": "B1"})
    assert r.status_code == 400
 
 
def test_alcance_de_base(cliente):
    r = cliente.get("/api/cobertura/alcance/B2")
    assert r.status_code == 200
    assert [z["id"] for z in r.json()["zonas_alcanzables"]] == ["Z5", "Z6"]
 
 
def test_alcance_desde_zona_400(cliente):
    assert cliente.get("/api/cobertura/alcance/Z1").status_code == 400