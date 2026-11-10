"""Pruebas de F3 (mejora): qué base con técnicos disponibles llega antes a una zona."""
import pytest

from app.dominio.asignacion import mejor_base
from app.dominio.carga import red_de_ejemplo
from app.dominio.errores import DatoInvalido, ElementoNoEncontrado
from app.dominio.red import RedCobertura


@pytest.fixture
def red():
    return red_de_ejemplo()


def test_gana_la_base_mas_rapida(red):
    # Robledo (Z5): desde B2 son 5 min; desde B1 son 21 min.
    r = mejor_base(red, "Z5")
    assert r["mejor"]["base"] == "B2"
    assert r["mejor"]["costo"] == 5
    assert r["mejor"]["camino"] == ["B2", "Z5"]
    assert [t["nombre"] for t in r["mejor"]["tecnicos_disponibles"]] == ["Marta"]
    assert "Marta" in r["mensaje"] and "5 min" in r["mensaje"]


def test_opciones_ordenadas_por_costo(red):
    r = mejor_base(red, "Z5")
    assert [(o["base"], o["costo"]) for o in r["opciones"]] == [("B2", 5), ("B1", 21)]


def test_base_que_no_llega_queda_al_final(red):
    # Aranjuez (Z3): B2 no llega porque Z4 -> Z5 es de solo ida.
    r = mejor_base(red, "Z3")
    assert r["mejor"]["base"] == "B1" and r["mejor"]["costo"] == 13
    assert r["mejor"]["camino"] == ["B1", "Z2", "Z3"]  # usa el menor costo, no el de menos tramos
    ultima = r["opciones"][-1]
    assert ultima["base"] == "B2" and ultima["alcanzable"] is False and ultima["costo"] is None


def test_solo_cuentan_tecnicos_disponibles(red):
    # Luis (T2) está en B1 pero no disponible: no aparece.
    r = mejor_base(red, "Z1")
    assert [t["id"] for t in r["mejor"]["tecnicos_disponibles"]] == ["T1"]


def test_base_cercana_sin_tecnicos_no_gana(red):
    red.agregar_nodo("B3", "Base Centro", "BASE")
    red.agregar_tecnico("T4", "Pedro", "B3", disponible=False)
    red.agregar_trayecto("B3", "Z3", 2)
    r = mejor_base(red, "Z3")
    assert r["mejor"]["base"] == "B1"  # B3 llega en 2 min, pero no tiene técnicos disponibles
    b3 = next(o for o in r["opciones"] if o["base"] == "B3")
    assert b3["costo"] == 2 and b3["tecnicos_disponibles"] == []
    assert "B3" in r["mensaje"]  # se le explica al operador por qué no se eligió la más cercana


def test_ninguna_base_con_tecnicos_llega():
    red = RedCobertura()
    red.agregar_nodo("B1", "Base", "BASE")
    red.agregar_nodo("Z1", "Zona", "ZONA")
    red.agregar_trayecto("B1", "Z1", 5)
    r = mejor_base(red, "Z1")
    assert r["mejor"] is None
    assert "ninguna" in r["mensaje"].lower()


def test_zona_sin_conexion(red):
    r = mejor_base(red, "Z7")
    assert r["mejor"] is None
    assert "no tiene trayectos" in r["mensaje"]
    assert all(o["alcanzable"] is False for o in r["opciones"])


def test_ninguna_base_llega_red_desconectada(red):
    # Z8 recibe un trayecto desde Poblado (Z7), pero ninguna base llega a Poblado.
    red.agregar_nodo("Z8", "Envigado", "ZONA")
    red.agregar_trayecto("Z7", "Z8", 6, bidireccional=False)
    r = mejor_base(red, "Z8")
    assert r["mejor"] is None
    assert "desconectada" in r["mensaje"]


def test_red_sin_bases():
    red = RedCobertura()
    red.agregar_nodo("Z1", "Zona", "ZONA")
    r = mejor_base(red, "Z1")
    assert r["mejor"] is None and r["opciones"] == []
    assert "no hay bases" in r["mensaje"].lower()


def test_empate_se_resuelve_por_id_de_base():
    red = RedCobertura()
    for i, tipo in (("B2", "BASE"), ("B1", "BASE"), ("Z1", "ZONA")):
        red.agregar_nodo(i, i, tipo)
    red.agregar_tecnico("T1", "Ana", "B1")
    red.agregar_tecnico("T2", "Luis", "B2")
    red.agregar_trayecto("B1", "Z1", 7)
    red.agregar_trayecto("B2", "Z1", 7)
    assert mejor_base(red, "Z1")["mejor"]["base"] == "B1"


def test_zona_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        mejor_base(red, "Z99")


def test_destino_debe_ser_zona(red):
    with pytest.raises(DatoInvalido):
        mejor_base(red, "B1")
