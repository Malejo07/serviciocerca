"""Pruebas de la API de menor costo (F3)."""
import pytest
from fastapi.testclient import TestClient

from app.main import crear_app


@pytest.fixture
def cliente():
    c = TestClient(crear_app())
    c.post("/api/red/ejemplo")
    return c


def test_menor_costo(cliente):
    r = cliente.get("/api/menor-costo", params={"origen": "B1", "zona": "Z3"})
    assert r.status_code == 200
    datos = r.json()
    assert datos["alcanzable"] is True
    assert datos["camino"] == ["B1", "Z2", "Z3"] and datos["costo"] == 13
    assert datos["comparacion_bfs"]["costo"] == 15
    assert datos["traza"][0]["cola"] == [{"id": "B1", "costo": 0}]


def test_ruta_imposible_no_es_un_error(cliente):
    r = cliente.get("/api/menor-costo", params={"origen": "B2", "zona": "Z4"})
    assert r.status_code == 200
    assert r.json()["alcanzable"] is False and r.json()["costo"] is None


def test_nodo_inexistente_404(cliente):
    r = cliente.get("/api/menor-costo", params={"origen": "B99", "zona": "Z1"})
    assert r.status_code == 404 and "B99" in r.json()["error"]


def test_zona_es_base_400(cliente):
    assert cliente.get("/api/menor-costo", params={"origen": "B1", "zona": "B2"}).status_code == 400


def test_falta_parametro_400(cliente):
    assert cliente.get("/api/menor-costo", params={"origen": "B1"}).status_code == 400


# ---------- Mejora: qué técnico llega primero ----------

def test_mejor_base(cliente):
    r = cliente.get("/api/menor-costo/mejor-base", params={"zona": "Z5"})
    assert r.status_code == 200
    datos = r.json()
    assert datos["mejor"]["base"] == "B2" and datos["mejor"]["costo"] == 5
    assert datos["mejor"]["traza"][0]["cola"] == [{"id": "B2", "costo": 0}]
    assert [o["base"] for o in datos["opciones"]] == ["B2", "B1"]


def test_mejor_base_sin_alternativa_no_es_error(cliente):
    r = cliente.get("/api/menor-costo/mejor-base", params={"zona": "Z7"})
    assert r.status_code == 200 and r.json()["mejor"] is None


def test_mejor_base_zona_inexistente_404(cliente):
    assert cliente.get("/api/menor-costo/mejor-base", params={"zona": "Z99"}).status_code == 404


def test_mejor_base_destino_es_base_400(cliente):
    assert cliente.get("/api/menor-costo/mejor-base", params={"zona": "B1"}).status_code == 400


def test_mejor_base_falta_zona_400(cliente):
    assert cliente.get("/api/menor-costo/mejor-base").status_code == 400
