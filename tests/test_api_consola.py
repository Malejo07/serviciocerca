"""Pruebas de la API y las páginas de la F4: landing, consola y aceptación."""
import pytest
from tests.utilidades import cliente_como


@pytest.fixture
def cliente():
    return cliente_como("admin")


# ---------- Páginas ----------

def test_la_raiz_es_la_landing_y_enlaza_a_la_consola(cliente):
    r = cliente.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "ServicioCerca" in r.text
    assert 'href="/consola"' in r.text


def test_la_consola_integra_configuracion_cobertura_costo_y_aceptacion(cliente):
    r = cliente.get("/consola")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "Consola de operación" in r.text
    for ancla in ("form-cobertura", "btn-costo", "btn-mejor", "form-nodo", "form-tecnico", "form-trayecto",
                  "btn-aceptacion", "btn-ampliar-mapa"):
        assert f'id="{ancla}"' in r.text


def test_las_paginas_no_dependen_de_fuentes_externas(cliente):
    for ruta in ("/", "/consola"):
        assert "fonts.googleapis.com" not in cliente.get(ruta).text


@pytest.mark.parametrize("archivo", [
    "space-grotesk-500.woff2", "space-grotesk-700.woff2",
    "ibm-plex-sans-400.woff2", "ibm-plex-sans-500.woff2", "ibm-plex-sans-600.woff2",
])
def test_las_tipografias_se_sirven_desde_el_proyecto(cliente, archivo):
    r = cliente.get(f"/static/fonts/{archivo}")
    assert r.status_code == 200 and len(r.content) > 5000


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
