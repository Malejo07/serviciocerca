"""Pruebas de la API de la F4: aceptación demostrable."""
import pytest
from tests.utilidades import cliente_como


@pytest.fixture
def cliente():
    return cliente_como("admin")


# ---------- Aceptación por API ----------

def test_aceptacion_devuelve_los_cuatro_escenarios(cliente):
    r = cliente.get("/api/aceptacion")
    assert r.status_code == 200
    datos = r.json()
    assert datos["todos_cumplidos"] is True and datos["cumplidos"] == 4
    assert [e["id"] for e in datos["escenarios"]] == ["exito", "zona_inexistente", "red_desconectada", "peso_invalido"]


def test_aceptacion_no_modifica_la_red_cargada(cliente):
    cliente.post("/api/red/ejemplo")
    antes = cliente.get("/api/red").json()
    cliente.get("/api/aceptacion")
    assert cliente.get("/api/red").json() == antes


def test_aceptacion_funciona_con_la_red_vacia(cliente):
    cliente.delete("/api/red")
    assert cliente.get("/api/aceptacion").json()["todos_cumplidos"] is True
    assert cliente.get("/api/red").json()["nodos"] == []


def test_evidencia_se_descarga_como_markdown(cliente):
    r = cliente.get("/api/aceptacion/evidencia")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert r.text.startswith("# Evidencia de aceptación")
