"""F3 — Menor costo: camino de menor tiempo total entre un origen y una zona.

Se usa Dijkstra (con montículo) implementado a mano. Es correcto porque todos los pesos son
positivos (ver docs/F3-menor-costo.md). Cada trayecto recorrido se vuelve a validar.
"""
import heapq

from app.dominio.cobertura import bfs, reconstruir_camino, tiene_trayectos_de_llegada
from app.dominio.errores import DatoInvalido
from app.dominio.modelos import TipoNodo
from app.dominio.red import RedCobertura, validar_peso


def formatear_minutos(minutos: float) -> str:
    minutos = round(minutos, 6)
    return str(int(minutos)) if minutos == int(minutos) else str(minutos)


def peso_del_trayecto(red: RedCobertura, origen: str, destino: str) -> float:
    """Peso de origen -> destino, validado otra vez: Dijkstra exige pesos finitos y > 0."""
    try:
        return validar_peso(red.vecinos(origen)[destino])
    except DatoInvalido as error:
        raise DatoInvalido(f"Trayecto {origen} -> {destino} inválido para el cálculo de menor costo: "
                           f"{error.mensaje}") from None


def dijkstra(red: RedCobertura, origen: str, destino: str):
    """Devuelve (dist, padre, definitivos, traza). Se detiene cuando el destino queda definitivo."""
    dist = {origen: 0.0}      # mejor costo candidato conocido para cada nodo descubierto
    padre = {origen: None}    # desde quién se llegó con ese costo
    definitivos = set()       # nodos cuyo costo ya no puede mejorar
    monticulo = [(0.0, origen)]

    def cola():
        # Costos candidatos de los nodos aún no definitivos (no es el contenido literal del heap,
        # que puede guardar entradas viejas que se descartan al sacarlas).
        return [{"id": n, "costo": round(c, 6)} for c, n in sorted((c, n) for n, c in dist.items() if n not in definitivos)]

    traza = [{"paso": 0, "actual": None, "costo_actual": None, "relajaciones": [], "nuevos": [origen], "cola": cola()}]

    while monticulo:
        costo, actual = heapq.heappop(monticulo)
        if actual in definitivos or costo > dist[actual]:
            continue  # entrada vieja: el nodo ya salió con un costo menor
        definitivos.add(actual)

        relajaciones, nuevos = [], []
        if actual != destino:
            for vecino in sorted(red.vecinos(actual)):
                peso = peso_del_trayecto(red, actual, vecino)
                candidato = dist[actual] + peso
                anterior = dist.get(vecino)
                mejora = anterior is None or candidato < anterior  # mejora estricta: los empates no cambian el camino
                relajaciones.append({"vecino": vecino, "candidato": round(candidato, 6),
                                     "anterior": None if anterior is None else round(anterior, 6), "mejora": mejora})
                if mejora:
                    if anterior is None:
                        nuevos.append(vecino)
                    dist[vecino] = candidato
                    padre[vecino] = actual
                    heapq.heappush(monticulo, (candidato, vecino))

        traza.append({"paso": len(traza), "actual": actual, "costo_actual": round(costo, 6),
                      "relajaciones": relajaciones, "nuevos": nuevos, "cola": cola()})
        if actual == destino:
            break

    return dist, padre, definitivos, traza


def menor_costo(red: RedCobertura, origen, zona) -> dict:
    """Camino de menor tiempo desde el origen hasta la zona, comparado con el de menos tramos (BFS)."""
    nodo_origen = red.obtener_nodo(origen)
    nodo_zona = red.obtener_nodo(zona)
    if nodo_zona.tipo != TipoNodo.ZONA:
        raise DatoInvalido(f"'{nodo_zona.id}' es una base; la zona solicitada debe ser una ZONA.")

    dist, padre, definitivos, traza = dijkstra(red, nodo_origen.id, nodo_zona.id)
    alcanzable = nodo_zona.id in definitivos
    nombre = f"{nodo_zona.id} ({nodo_zona.nombre})"
    resultado = {"origen": nodo_origen.id, "zona": nodo_zona.id, "alcanzable": alcanzable, "camino": None,
                 "costo": None, "tramos": None, "comparacion_bfs": None, "menos_tramos_es_mas_caro": False,
                 "traza": traza}

    if not alcanzable:
        if not tiene_trayectos_de_llegada(red, nodo_zona.id):
            resultado["mensaje"] = f"{nombre} no tiene trayectos que lleguen a ella; no se puede atender desde ninguna base."
        else:
            resultado["mensaje"] = (f"{nombre} no es alcanzable desde {nodo_origen.id}: "
                                    f"no hay camino desde el origen; la red está desconectada entre ambos.")
        return resultado

    camino = reconstruir_camino(padre, nodo_zona.id)
    costo = round(dist[nodo_zona.id], 6)
    resultado.update(camino=camino, costo=costo, tramos=len(camino) - 1)
    mensaje = (f"Menor costo de {nodo_origen.id} a {nombre}: {formatear_minutos(costo)} min "
               f"por {' -> '.join(camino)} ({len(camino) - 1} tramo(s)).")

    # Comparación con la ruta de menos tramos (la que daría BFS).
    camino_bfs = reconstruir_camino(bfs(red, nodo_origen.id).padre, nodo_zona.id)
    # Se validan también estos pesos: Dijkstra se detiene al llegar al destino y puede no haber revisado
    # todos los tramos de la ruta de menos tramos.
    costo_bfs = round(sum(peso_del_trayecto(red, a, b) for a, b in zip(camino_bfs, camino_bfs[1:])), 6)
    diferencia = round(costo_bfs - costo, 6)
    resultado["comparacion_bfs"] = {"camino": camino_bfs, "tramos": len(camino_bfs) - 1,
                                    "costo": costo_bfs, "diferencia": diferencia}
    if diferencia > 0:
        resultado["menos_tramos_es_mas_caro"] = True
        mensaje += (f" La ruta con menos tramos ({' -> '.join(camino_bfs)}, {len(camino_bfs) - 1} tramo(s)) "
                    f"cuesta {formatear_minutos(costo_bfs)} min, {formatear_minutos(diferencia)} min más.")
    resultado["mensaje"] = mensaje
    return resultado
