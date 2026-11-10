"""Pruebas de F3: menor costo con Dijkstra (ver docs/F3-menor-costo.md)."""
import random

import pytest

from app.dominio.carga import red_de_ejemplo
from app.dominio.cobertura import consultar_cobertura
from app.dominio.costo import menor_costo
from app.dominio.errores import DatoInvalido, ElementoDuplicado, ElementoNoEncontrado
from app.dominio.red import RedCobertura


@pytest.fixture
def red():
    return red_de_ejemplo()


# ---------- Algoritmo ----------

def test_traza_coincide_con_la_hecha_en_papel(red):
    r = menor_costo(red, "B1", "Z3")
    pasos = [(p["actual"], p["costo_actual"], [(x["vecino"], x["candidato"], x["mejora"]) for x in p["relajaciones"]],
              [(c["id"], c["costo"]) for c in p["cola"]]) for p in r["traza"]]
    assert pasos == [
        (None, None, [], [("B1", 0)]),
        ("B1", 0, [("Z1", 4, True), ("Z2", 6, True), ("Z3", 15, True)], [("Z1", 4), ("Z2", 6), ("Z3", 15)]),
        ("Z1", 4, [("B1", 8, False), ("Z4", 9, True)], [("Z2", 6), ("Z4", 9), ("Z3", 15)]),
        ("Z2", 6, [("B1", 12, False), ("Z3", 13, True)], [("Z4", 9), ("Z3", 13)]),
        ("Z4", 9, [("Z1", 14, False), ("Z5", 21, True)], [("Z3", 13), ("Z5", 21)]),
        ("Z3", 13, [], [("Z5", 21)]),
    ]


def test_menos_tramos_no_es_menor_costo(red):
    r = menor_costo(red, "B1", "Z3")
    assert r["alcanzable"] is True
    assert r["camino"] == ["B1", "Z2", "Z3"] and r["costo"] == 13 and r["tramos"] == 2
    bfs = r["comparacion_bfs"]
    assert bfs["camino"] == ["B1", "Z3"] and bfs["tramos"] == 1 and bfs["costo"] == 15
    assert bfs["diferencia"] == 2 and r["menos_tramos_es_mas_caro"] is True
    assert consultar_cobertura(red, "B1", "Z3")["camino"] == bfs["camino"]  # es justo el camino que elige BFS
    assert "2 min" in r["mensaje"] and "13" in r["mensaje"]


def test_cuando_coinciden_no_hay_advertencia(red):
    r = menor_costo(red, "B1", "Z1")
    assert r["camino"] == ["B1", "Z1"] and r["costo"] == 4
    assert r["menos_tramos_es_mas_caro"] is False


def test_ruta_de_varios_tramos(red):
    assert menor_costo(red, "B1", "Z5")["camino"] == ["B1", "Z1", "Z4", "Z5"]
    assert menor_costo(red, "B1", "Z5")["costo"] == 21
    r = menor_costo(red, "B2", "Z6")
    assert r["camino"] == ["B2", "Z5", "Z6"] and r["costo"] == 9


def test_origen_igual_al_destino(red):
    r = menor_costo(red, "Z1", "Z1")
    assert r["alcanzable"] is True and r["camino"] == ["Z1"] and r["costo"] == 0 and r["tramos"] == 0


# ---------- Rutas imposibles ----------

def test_respeta_la_direccion_de_los_trayectos(red):
    for origen, zona in (("B2", "Z4"), ("Z5", "Z4")):
        r = menor_costo(red, origen, zona)
        assert r["alcanzable"] is False and r["camino"] is None and r["costo"] is None
        assert "desconectada" in r["mensaje"]


def test_zona_sin_conexion(red):
    r = menor_costo(red, "B1", "Z7")
    assert r["alcanzable"] is False and "no tiene trayectos" in r["mensaje"]


def test_nodos_invalidos(red):
    with pytest.raises(ElementoNoEncontrado):
        menor_costo(red, "B99", "Z1")
    with pytest.raises(ElementoNoEncontrado):
        menor_costo(red, "B1", "Z99")
    with pytest.raises(DatoInvalido):
        menor_costo(red, "B1", "B2")


# ---------- Pesos que invalidan el algoritmo ----------

@pytest.mark.parametrize("peso", [-4, 0, float("nan"), float("inf"), "10", True])
def test_peso_invalido_se_rechaza_de_forma_explicita(red, peso):
    red._adyacencia["B1"]["Z1"] = peso  # alteración fuera de la API: la red ya no es de confianza
    with pytest.raises(DatoInvalido) as error:
        menor_costo(red, "B1", "Z3")
    assert "B1 -> Z1" in error.value.mensaje


# ---------- Otros casos ----------

def test_pesos_decimales():
    red = RedCobertura()
    red.agregar_nodo("B1", "Base", "BASE")
    red.agregar_nodo("Z1", "Uno", "ZONA")
    red.agregar_nodo("Z2", "Dos", "ZONA")
    red.agregar_trayecto("B1", "Z1", 0.1)
    red.agregar_trayecto("Z1", "Z2", 0.2)
    red.agregar_trayecto("B1", "Z2", 0.4)
    r = menor_costo(red, "B1", "Z2")
    assert r["camino"] == ["B1", "Z1", "Z2"] and r["costo"] == pytest.approx(0.3)
    assert "0.3 min" in r["mensaje"]


def test_empate_es_reproducible():
    red = RedCobertura()
    for i, tipo in (("B1", "BASE"), ("Z1", "ZONA"), ("Z2", "ZONA"), ("Z3", "ZONA")):
        red.agregar_nodo(i, i, tipo)
    for a, b in (("B1", "Z1"), ("B1", "Z2"), ("Z1", "Z3"), ("Z2", "Z3")):
        red.agregar_trayecto(a, b, 5)
    resultados = [menor_costo(red, "B1", "Z3") for _ in range(5)]
    assert all(r["costo"] == 10 for r in resultados)
    assert all(r["camino"] == resultados[0]["camino"] for r in resultados)


def test_no_modifica_la_red(red):
    antes = red.trayectos()
    menor_costo(red, "B1", "Z5")
    assert red.trayectos() == antes


def _fuerza_bruta(red, origen, destino):
    mejor = [None]

    def explorar(actual, visitados, costo):
        if actual == destino:
            mejor[0] = costo if mejor[0] is None else min(mejor[0], costo)
            return
        for vecino, peso in red.vecinos(actual).items():
            if vecino not in visitados:
                explorar(vecino, visitados | {vecino}, costo + peso)

    explorar(origen, {origen}, 0)
    return mejor[0]


def test_coincide_con_fuerza_bruta_en_redes_aleatorias():
    azar = random.Random(7)
    ids = ["B1", "Z1", "Z2", "Z3", "Z4", "Z5"]
    for _ in range(200):
        red = RedCobertura()
        for i in ids:
            red.agregar_nodo(i, i, "BASE" if i == "B1" else "ZONA")
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if azar.random() < .5:
                    a, b = (ids[i], ids[j]) if azar.random() < .5 else (ids[j], ids[i])
                    try:
                        red.agregar_trayecto(a, b, azar.randint(1, 20), azar.random() < .5)
                    except ElementoDuplicado:
                        pass
        for destino in ids[1:]:
            esperado = _fuerza_bruta(red, "B1", destino)
            r = menor_costo(red, "B1", destino)
            if esperado is None:
                assert r["alcanzable"] is False
            else:
                assert r["costo"] == pytest.approx(esperado)


def test_peso_invalido_en_ruta_de_menos_tramos_se_rechaza():
    # Dijkstra llega a Z por B1->X->Y->Z (3 min) y se detiene sin revisar W->Z.
    # La comparación con BFS (B1->W->Z) también debe validar ese tramo.
    red = RedCobertura()
    for i, tipo in (("B1", "BASE"), ("X", "ZONA"), ("Y", "ZONA"), ("W", "ZONA"), ("Z", "ZONA")):
        red.agregar_nodo(i, i, tipo)
    for a, b, m in (("B1", "X", 1), ("X", "Y", 1), ("Y", "Z", 1), ("B1", "W", 50), ("W", "Z", 1)):
        red.agregar_trayecto(a, b, m, bidireccional=False)
    red._adyacencia["W"]["Z"] = "10"  # alteración fuera de la API
    with pytest.raises(DatoInvalido) as error:
        menor_costo(red, "B1", "Z")
    assert "W -> Z" in error.value.mensaje
