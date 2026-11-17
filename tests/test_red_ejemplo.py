"""La red de ejemplo es la base de las demostraciones: sus datos deben seguir contando la misma historia."""
import pytest

from app.dominio.asignacion import mejor_base
from app.dominio.carga import red_de_ejemplo
from app.dominio.cobertura import consultar_cobertura
from app.dominio.costo import menor_costo


@pytest.fixture
def red():
    return red_de_ejemplo()


def test_contenido_de_la_red(red):
    zonas = {n.nombre for n in red.nodos.values() if n.tipo == "ZONA"}
    assert {"La América", "Boston"} <= zonas
    assert len(red.nodos) == 11 and len([n for n in red.nodos.values() if n.tipo == "BASE"]) == 2


def test_hay_cuatro_tecnicos_dos_por_base_y_uno_disponible_en_cada_una(red):
    tecnicos = list(red.tecnicos.values())
    assert len(tecnicos) == 4
    for base in ("B1", "B2"):
        propios = [t for t in tecnicos if t.base_id == base]
        assert len(propios) == 2 and sum(t.disponible for t in propios) == 1


def test_los_minutos_son_razonables_para_una_ciudad(red):
    minutos = [t.minutos for t in red.trayectos()]
    assert all(5 <= m <= 30 for m in minutos), sorted(minutos)


def test_menos_tramos_no_es_menos_tiempo(red):
    """La demostración central: el camino directo tiene 1 tramo pero tarda más que el rodeo de 2 tramos."""
    por_tramos = consultar_cobertura(red, "B1", "Z3")
    por_tiempo = menor_costo(red, "B1", "Z3")
    assert por_tramos["camino"] == ["B1", "Z3"] and por_tramos["tramos"] == 1
    assert por_tiempo["camino"] == ["B1", "Z2", "Z3"] and por_tiempo["tramos"] == 2
    assert por_tiempo["costo"] < por_tiempo["comparacion_bfs"]["costo"]
    assert (por_tiempo["costo"], por_tiempo["comparacion_bfs"]["costo"]) == (15, 20)


def test_las_zonas_nuevas_se_atienden_desde_base_sur(red):
    assert mejor_base(red, "Z8")["mejor"]["base"] == "B2" and mejor_base(red, "Z8")["mejor"]["costo"] == 14
    assert mejor_base(red, "Z9")["mejor"]["base"] == "B2" and mejor_base(red, "Z9")["mejor"]["costo"] == 42


def test_siguen_los_casos_de_red_desconectada(red):
    assert consultar_cobertura(red, "B2", "Z4")["cubierta"] is False       # trayecto de un solo sentido
    assert "no tiene trayectos" in consultar_cobertura(red, "B1", "Z7")["mensaje"]   # Poblado sin conexión
    assert menor_costo(red, "B1", "Z8")["alcanzable"] is True              # La América sí llega desde el norte


def test_ninguna_zona_nueva_abre_camino_de_base_sur_al_norte(red):
    for zona in ("Z1", "Z2", "Z3", "Z4"):
        assert menor_costo(red, "B2", zona)["alcanzable"] is False, zona
