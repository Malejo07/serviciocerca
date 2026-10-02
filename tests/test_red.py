"""Pruebas del dominio: registro y validación de la red de cobertura."""
import math

import pytest

from app.dominio.errores import DatoInvalido, ElementoDuplicado, ElementoNoEncontrado
from app.dominio.modelos import TipoNodo
from app.dominio.red import RedCobertura


@pytest.fixture
def red():
    r = RedCobertura()
    r.agregar_nodo("B1", "Base Norte", "BASE")
    r.agregar_nodo("Z1", "Chapinero", "ZONA")
    r.agregar_nodo("Z2", "Usaquén", "ZONA")
    return r


# ---------- Nodos ----------

def test_agregar_nodo_valido(red):
    nodo = red.agregar_nodo("Z3", "Suba", "ZONA")
    assert nodo.id == "Z3"
    assert nodo.tipo == TipoNodo.ZONA
    assert len(red.nodos) == 4


def test_id_se_normaliza_a_mayusculas(red):
    nodo = red.agregar_nodo("  z9 ", "Kennedy", "zona")
    assert nodo.id == "Z9"
    assert nodo.tipo == TipoNodo.ZONA


@pytest.mark.parametrize("id_malo", ["", "   ", "Z 1", "Z#1", "A" * 31])
def test_id_invalido(red, id_malo):
    with pytest.raises(DatoInvalido):
        red.agregar_nodo(id_malo, "X", "ZONA")


def test_nodo_duplicado(red):
    with pytest.raises(ElementoDuplicado):
        red.agregar_nodo("z1", "Otra", "ZONA")  # z1 == Z1


def test_tipo_invalido(red):
    with pytest.raises(DatoInvalido):
        red.agregar_nodo("X1", "X", "HOSPITAL")


def test_nombre_vacio(red):
    with pytest.raises(DatoInvalido):
        red.agregar_nodo("X1", "   ", "ZONA")


# ---------- Técnicos ----------

def test_agregar_tecnico(red):
    t = red.agregar_tecnico("T1", "Ana", "B1")
    assert t.base_id == "B1"
    assert t.disponible is True


def test_tecnico_duplicado(red):
    red.agregar_tecnico("T1", "Ana", "B1")
    with pytest.raises(ElementoDuplicado):
        red.agregar_tecnico("T1", "Luis", "B1")


def test_tecnico_en_base_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        red.agregar_tecnico("T1", "Ana", "B99")


def test_tecnico_asignado_a_zona_no_permitido(red):
    with pytest.raises(DatoInvalido):
        red.agregar_tecnico("T1", "Ana", "Z1")


# ---------- Trayectos ----------

def test_trayecto_bidireccional_crea_dos_aristas(red):
    red.agregar_trayecto("B1", "Z1", 10)
    assert red.vecinos("B1") == {"Z1": 10}
    assert red.vecinos("Z1") == {"B1": 10}


def test_trayecto_unidireccional_crea_una_arista(red):
    red.agregar_trayecto("B1", "Z1", 10, bidireccional=False)
    assert red.vecinos("B1") == {"Z1": 10}
    assert red.vecinos("Z1") == {}


def test_trayectos_distinto_tiempo_por_sentido(red):
    red.agregar_trayecto("Z1", "Z2", 5, bidireccional=False)
    red.agregar_trayecto("Z2", "Z1", 8, bidireccional=False)
    assert red.vecinos("Z1")["Z2"] == 5
    assert red.vecinos("Z2")["Z1"] == 8


@pytest.mark.parametrize("peso", [0, -3, math.inf, math.nan, "diez", None, True])
def test_peso_invalido(red, peso):
    with pytest.raises(DatoInvalido):
        red.agregar_trayecto("B1", "Z1", peso)


def test_trayecto_con_nodo_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        red.agregar_trayecto("B1", "Z99", 5)


def test_trayecto_lazo(red):
    with pytest.raises(DatoInvalido):
        red.agregar_trayecto("Z1", "Z1", 5)


def test_trayecto_duplicado(red):
    red.agregar_trayecto("B1", "Z1", 10)
    with pytest.raises(ElementoDuplicado):
        red.agregar_trayecto("Z1", "B1", 7)  # el sentido Z1->B1 ya existe


def test_trayecto_fallido_no_deja_red_a_medias(red):
    red.agregar_trayecto("Z1", "B1", 4, bidireccional=False)
    with pytest.raises(ElementoDuplicado):
        red.agregar_trayecto("B1", "Z1", 10)  # B1->Z1 es nuevo, pero Z1->B1 ya existe
    assert "Z1" not in red.vecinos("B1")


# ---------- Consulta ----------

def test_trayectos_lista_todas_las_aristas(red):
    red.agregar_trayecto("B1", "Z1", 10)
    red.agregar_trayecto("Z1", "Z2", 3, bidireccional=False)
    pares = {(t.origen, t.destino, t.minutos) for t in red.trayectos()}
    assert pares == {("B1", "Z1", 10), ("Z1", "B1", 10), ("Z1", "Z2", 3)}


def test_vecinos_de_nodo_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        red.vecinos("NOPE")
