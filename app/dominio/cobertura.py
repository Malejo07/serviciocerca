"""F2 — Cobertura: ¿se puede llegar de un origen a una zona? (alcance, no costo).

Se usa BFS (búsqueda en anchura) implementado a mano. La justificación está en docs/F2-cobertura.md.
"""
from collections import deque
from dataclasses import dataclass

from app.dominio.errores import DatoInvalido
from app.dominio.modelos import TipoNodo
from app.dominio.red import RedCobertura


@dataclass
class ResultadoBFS:
    origen: str
    padre: dict[str, str | None]   # de quién se descubrió cada nodo (para reconstruir caminos)
    tramos: dict[str, int]         # cuántos tramos hay desde el origen hasta cada nodo visitado
    traza: list[dict]              # el estado de la cola en cada paso


def bfs(red: RedCobertura, origen) -> ResultadoBFS:
    origen = red.obtener_nodo(origen).id  # valida que exista y normaliza el id

    padre = {origen: None}
    tramos = {origen: 0}
    cola = deque([origen])
    traza = [{"paso": 0, "actual": None, "vecinos": [], "nuevos": [origen], "cola": [origen]}]

    while cola:
        actual = cola.popleft()  # FIFO: el primero que entró es el primero que sale
        vecinos = sorted(red.vecinos(actual))  # orden alfabético para que la traza sea reproducible
        nuevos = []
        for vecino in vecinos:
            if vecino not in padre:  # 'padre' también funciona como conjunto de visitados
                padre[vecino] = actual
                tramos[vecino] = tramos[actual] + 1
                cola.append(vecino)
                nuevos.append(vecino)
        traza.append({
            "paso": len(traza),
            "actual": actual,
            "vecinos": vecinos,
            "nuevos": nuevos,
            "cola": list(cola),
        })

    return ResultadoBFS(origen=origen, padre=padre, tramos=tramos, traza=traza)


def reconstruir_camino(padre: dict[str, str | None], destino: str) -> list[str] | None:
    """Sigue los padres desde el destino hasta el origen y voltea la lista."""
    if destino not in padre:
        return None
    camino = []
    nodo = destino
    while nodo is not None:
        camino.append(nodo)
        nodo = padre[nodo]
    camino.reverse()
    return camino


def consultar_cobertura(red: RedCobertura, origen, zona) -> dict:
    """¿La zona solicitada está dentro de la cobertura posible desde el origen?"""
    nodo_origen = red.obtener_nodo(origen)
    nodo_zona = red.obtener_nodo(zona)
    if nodo_zona.tipo != TipoNodo.ZONA:
        raise DatoInvalido(f"'{nodo_zona.id}' es una base; la zona solicitada debe ser una ZONA.")

    resultado = bfs(red, nodo_origen.id)
    camino = reconstruir_camino(resultado.padre, nodo_zona.id)
    cubierta = camino is not None

    if cubierta:
        tramos = resultado.tramos[nodo_zona.id]
        mensaje = (f"{nodo_zona.id} ({nodo_zona.nombre}) es alcanzable desde {nodo_origen.id} "
                   f"en {tramos} tramo(s): {' -> '.join(camino)}.")
    else:
        tramos = None
        if not _tiene_trayectos_de_llegada(red, nodo_zona.id):
            mensaje = (f"{nodo_zona.id} ({nodo_zona.nombre}) no tiene trayectos que lleguen a ella; "
                       f"no se puede atender desde ninguna base.")
        else:
            mensaje = (f"{nodo_zona.id} ({nodo_zona.nombre}) no es alcanzable desde {nodo_origen.id}: "
                       f"no hay camino desde el origen; la red está desconectada entre ambos.")

    return {
        "origen": nodo_origen.id,
        "zona": nodo_zona.id,
        "cubierta": cubierta,
        "camino": camino,
        "tramos": tramos,
        "mensaje": mensaje,
        "traza": resultado.traza,
    }


def listar_alcance(red: RedCobertura, base_id) -> dict:
    """Lista las zonas que se pueden alcanzar desde una base y las que no."""
    base = red.obtener_nodo(base_id)
    if base.tipo != TipoNodo.BASE:
        raise DatoInvalido(f"'{base.id}' es una zona; el alcance se consulta desde una BASE.")

    resultado = bfs(red, base.id)
    zonas = sorted((n for n in red.nodos.values() if n.tipo == TipoNodo.ZONA), key=lambda n: n.id)
    alcanzables = [
        {"id": z.id, "nombre": z.nombre, "tramos": resultado.tramos[z.id]}
        for z in zonas if z.id in resultado.tramos
    ]
    alcanzables.sort(key=lambda z: (z["tramos"], z["id"]))  # primero las más cercanas en tramos
    no_alcanzables = [z.id for z in zonas if z.id not in resultado.tramos]
    tecnicos = [
        {"id": t.id, "nombre": t.nombre}
        for t in red.tecnicos.values() if t.base_id == base.id and t.disponible
    ]

    return {
        "base": base.id,
        "zonas_alcanzables": alcanzables,
        "zonas_no_alcanzables": no_alcanzables,
        "tecnicos_disponibles": tecnicos,
        "mensaje": f"Desde {base.id} ({base.nombre}) se alcanzan {len(alcanzables)} de {len(zonas)} zonas.",
        "traza": resultado.traza,
    }


def _tiene_trayectos_de_llegada(red: RedCobertura, id_nodo: str) -> bool:
    return any(id_nodo in red.vecinos(otro) for otro in red.nodos if otro != id_nodo)
