"""Pruebas de F2: cobertura con BFS sobre la red de ejemplo (ver docs/F2-cobertura.md)."""
import pytest

from app.dominio.carga import red_de_ejemplo
from app.dominio.cobertura import bfs, consultar_cobertura, listar_alcance, reconstruir_camino
from app.dominio.errores import DatoInvalido, ElementoNoEncontrado


@pytest.fixture
def red():
    return red_de_ejemplo()


# ---------- BFS (algoritmo) ----------

def test_traza_coincide_con_la_hecha_en_papel(red):
    resultado = bfs(red, "B1")
    pasos = [(p["actual"], p["nuevos"], p["cola"]) for p in resultado.traza]
    assert pasos == [
        (None, ["B1"], ["B1"]),                 # paso 0: inicio
        ("B1", ["Z1", "Z2", "Z3"], ["Z1", "Z2", "Z3"]),
        ("Z1", ["Z4"], ["Z2", "Z3", "Z4"]),
        ("Z2", [], ["Z3", "Z4"]),
        ("Z3", [], ["Z4"]),
        ("Z4", ["Z5"], ["Z5"]),
        ("Z5", ["B2", "Z6"], ["B2", "Z6"]),
        ("B2", [], ["Z6"]),
        ("Z6", [], []),
    ]


def test_bfs_calcula_tramos_por_nivel(red):
    tramos = bfs(red, "B1").tramos
    assert tramos == {"B1": 0, "Z1": 1, "Z2": 1, "Z3": 1, "Z4": 2, "Z5": 3, "B2": 4, "Z6": 4}


def test_reconstruir_camino_con_padres(red):
    padre = bfs(red, "B1").padre
    assert reconstruir_camino(padre, "Z5") == ["B1", "Z1", "Z4", "Z5"]
    assert reconstruir_camino(padre, "Z7") is None  # nunca se visitó


def test_bfs_origen_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        bfs(red, "NOPE")


# ---------- Cobertura de una zona ----------

def test_zona_cubierta(red):
    r = consultar_cobertura(red, "B1", "Z5")
    assert r["cubierta"] is True
    assert r["camino"] == ["B1", "Z1", "Z4", "Z5"]
    assert r["tramos"] == 3
    assert "alcanzable" in r["mensaje"]


def test_bfs_da_menos_tramos_no_menor_costo(red):
    # B1->Z3 directo (15 min) gana por tramos aunque B1->Z2->Z3 cuesta 13 min. Eso lo resuelve la F3.
    r = consultar_cobertura(red, "B1", "Z3")
    assert r["camino"] == ["B1", "Z3"]
    assert r["tramos"] == 1


def test_direccion_importa_red_desconectada(red):
    # Z4 -> Z5 es solo ida: desde B2 (sur) no se llega a Z1 (norte).
    r = consultar_cobertura(red, "B2", "Z1")
    assert r["cubierta"] is False
    assert r["camino"] is None
    assert "desconectada" in r["mensaje"]


def test_zona_sin_conexion(red):
    r = consultar_cobertura(red, "B1", "Z7")
    assert r["cubierta"] is False
    assert "no tiene trayectos" in r["mensaje"]


def test_origen_igual_a_zona(red):
    r = consultar_cobertura(red, "Z1", "Z1")
    assert r["cubierta"] is True
    assert r["tramos"] == 0
    assert r["camino"] == ["Z1"]


def test_ids_se_normalizan(red):
    assert consultar_cobertura(red, "b1", " z5 ")["cubierta"] is True


def test_zona_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        consultar_cobertura(red, "B1", "Z99")


def test_origen_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        consultar_cobertura(red, "B99", "Z1")


def test_zona_solicitada_no_puede_ser_base(red):
    with pytest.raises(DatoInvalido):
        consultar_cobertura(red, "B1", "B2")


# ---------- Alcance de una base ----------

def test_alcance_desde_base_norte(red):
    r = listar_alcance(red, "B1")
    assert [(z["id"], z["tramos"]) for z in r["zonas_alcanzables"]] == [
        ("Z1", 1), ("Z2", 1), ("Z3", 1), ("Z4", 2), ("Z5", 3), ("Z6", 4),
    ]
    assert r["zonas_no_alcanzables"] == ["Z7"]
    assert [t["id"] for t in r["tecnicos_disponibles"]] == ["T1"]  # Luis (T2) no está disponible


def test_alcance_desde_base_sur_respeta_direccion(red):
    r = listar_alcance(red, "B2")
    assert [z["id"] for z in r["zonas_alcanzables"]] == ["Z5", "Z6"]
    assert r["zonas_no_alcanzables"] == ["Z1", "Z2", "Z3", "Z4", "Z7"]


def test_alcance_requiere_base(red):
    with pytest.raises(DatoInvalido):
        listar_alcance(red, "Z1")


def test_alcance_base_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        listar_alcance(red, "B99")
