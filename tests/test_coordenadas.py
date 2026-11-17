"""Pruebas de la geolocalización de nodos (docs/mapa-medellin.md)."""
import math

import pytest

from app.dominio.carga import red_de_ejemplo
from app.dominio.errores import DatoInvalido
from app.dominio.red import RedCobertura
from tests.utilidades import cliente_como


# ---------- Dominio ----------

def test_un_nodo_puede_tener_ubicacion():
    nodo = RedCobertura().agregar_nodo("Z1", "Castilla", "ZONA", 6.2917, -75.5833)
    assert (nodo.latitud, nodo.longitud) == (6.2917, -75.5833)


def test_la_ubicacion_es_opcional():
    nodo = RedCobertura().agregar_nodo("Z1", "Castilla", "ZONA")
    assert nodo.latitud is None and nodo.longitud is None


def test_latitud_y_longitud_van_juntas():
    red = RedCobertura()
    for lat, lon in ((6.25, None), (None, -75.5)):
        with pytest.raises(DatoInvalido, match="juntas"):
            red.agregar_nodo("Z1", "X", "ZONA", lat, lon)
    assert not red.nodos


@pytest.mark.parametrize("lat, lon, texto", [
    (91, -75.5, "latitud"), (-90.5, -75.5, "latitud"), (6.2, 181, "longitud"), (6.2, -180.1, "longitud"),
])
def test_las_coordenadas_fuera_de_rango_se_rechazan(lat, lon, texto):
    with pytest.raises(DatoInvalido, match=texto):
        RedCobertura().agregar_nodo("Z1", "X", "ZONA", lat, lon)


@pytest.mark.parametrize("lat, lon", [
    (math.nan, -75.5), (6.2, math.inf), ("6.2", -75.5), (6.2, "abc"), (True, -75.5),
])
def test_las_coordenadas_deben_ser_numeros_finitos(lat, lon):
    with pytest.raises(DatoInvalido):
        RedCobertura().agregar_nodo("Z1", "X", "ZONA", lat, lon)


def test_los_limites_exactos_son_validos():
    red = RedCobertura()
    red.agregar_nodo("Z1", "Polo", "ZONA", 90, 180)
    red.agregar_nodo("Z2", "Polo sur", "ZONA", -90, -180)


def test_la_red_de_ejemplo_esta_ubicada_en_el_valle_de_medellin():
    red = red_de_ejemplo()
    assert len(red.nodos) == 11
    for nodo in red.nodos.values():
        assert nodo.latitud is not None and nodo.longitud is not None, nodo.id
        assert 6.15 <= nodo.latitud <= 6.40 and -75.70 <= nodo.longitud <= -75.50, nodo.id


# ---------- API ----------

def test_registrar_nodo_con_ubicacion_y_verla_en_la_red():
    cliente = cliente_como("admin")
    r = cliente.post("/api/nodos", json={"id": "Z1", "nombre": "Laureles", "tipo": "ZONA", "latitud": 6.2442, "longitud": -75.5900})
    assert r.status_code == 201 and r.json()["latitud"] == 6.2442
    nodo = cliente.get("/api/red").json()["nodos"][0]
    assert (nodo["latitud"], nodo["longitud"]) == (6.2442, -75.59)


def test_los_nodos_sin_ubicacion_devuelven_null():
    cliente = cliente_como("admin")
    cliente.post("/api/nodos", json={"id": "Z1", "nombre": "Laureles", "tipo": "ZONA"})
    nodo = cliente.get("/api/red").json()["nodos"][0]
    assert nodo["latitud"] is None and nodo["longitud"] is None


def test_la_api_rechaza_ubicaciones_incompletas_o_invalidas():
    cliente = cliente_como("admin")
    r = cliente.post("/api/nodos", json={"id": "Z1", "nombre": "X", "tipo": "ZONA", "latitud": 6.2})
    assert r.status_code == 400 and "juntas" in r.json()["error"]
    r = cliente.post("/api/nodos", json={"id": "Z1", "nombre": "X", "tipo": "ZONA", "latitud": 95, "longitud": 0})
    assert r.status_code == 400 and "latitud" in r.json()["error"]
    r = cliente.post("/api/nodos", json={"id": "Z1", "nombre": "X", "tipo": "ZONA", "latitud": "abc", "longitud": 0})
    assert r.status_code == 400
    assert cliente.get("/api/red").json()["nodos"] == []


def test_la_red_de_ejemplo_llega_con_ubicaciones_por_la_api():
    cliente = cliente_como("admin")
    cliente.post("/api/red/ejemplo")
    assert all(n["latitud"] is not None for n in cliente.get("/api/red").json()["nodos"])
