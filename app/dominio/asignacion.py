"""F3 (mejora): ¿desde qué base, con técnicos disponibles, se llega antes a una zona?

Responde la pregunta del cliente: "cuál técnico podría llegar con menor costo estimado".
Se ejecuta el Dijkstra de la F3 (menor_costo) una vez por cada base y se comparan los costos.
No asigna técnicos automáticamente (fuera de alcance): solo recomienda la mejor alternativa.
"""
from app.dominio.cobertura import tiene_trayectos_de_llegada
from app.dominio.costo import formatear_minutos, menor_costo
from app.dominio.errores import DatoInvalido
from app.dominio.modelos import TipoNodo
from app.dominio.red import RedCobertura


def mejor_base(red: RedCobertura, zona) -> dict:
    nodo_zona = red.obtener_nodo(zona)
    if nodo_zona.tipo != TipoNodo.ZONA:
        raise DatoInvalido(f"'{nodo_zona.id}' es una base; la zona solicitada debe ser una ZONA.")
    nombre_zona = f"{nodo_zona.id} ({nodo_zona.nombre})"

    bases = sorted((n for n in red.nodos.values() if n.tipo == TipoNodo.BASE), key=lambda n: n.id)
    if not bases:
        return {"zona": nodo_zona.id, "mejor": None, "opciones": [],
                "mensaje": "No hay bases registradas en la red."}

    opciones = []
    trazas = {}
    for base in bases:
        r = menor_costo(red, base.id, nodo_zona.id)  # Dijkstra de la F3
        tecnicos = [{"id": t.id, "nombre": t.nombre}
                    for t in red.tecnicos.values() if t.base_id == base.id and t.disponible]
        opciones.append({"base": base.id, "nombre": base.nombre, "tecnicos_disponibles": tecnicos,
                         "alcanzable": r["alcanzable"], "costo": r["costo"],
                         "camino": r["camino"], "tramos": r["tramos"]})
        trazas[base.id] = r["traza"]

    # Primero las que llegan, de menor a mayor costo; al final las que no llegan. Empates: por id de base.
    opciones.sort(key=lambda o: (not o["alcanzable"], o["costo"] if o["alcanzable"] else 0, o["base"]))

    candidatas = [o for o in opciones if o["alcanzable"] and o["tecnicos_disponibles"]]
    mejor = dict(candidatas[0], traza=trazas[candidatas[0]["base"]]) if candidatas else None

    return {"zona": nodo_zona.id, "mejor": mejor, "opciones": opciones,
            "mensaje": _mensaje(red, nodo_zona.id, nombre_zona, mejor, opciones)}


def _mensaje(red, id_zona, nombre_zona, mejor, opciones) -> str:
    llegan_sin_tecnicos = [o for o in opciones if o["alcanzable"] and not o["tecnicos_disponibles"]]

    if mejor:
        tecnicos = ", ".join(t["nombre"] for t in mejor["tecnicos_disponibles"])
        texto = (f"Llega primero a {nombre_zona}: {tecnicos} desde {mejor['base']} ({mejor['nombre']}), "
                 f"{formatear_minutos(mejor['costo'])} min por {' -> '.join(mejor['camino'])}.")
        mas_cercanas = [o for o in llegan_sin_tecnicos if o["costo"] < mejor["costo"]]
        for o in mas_cercanas:
            texto += (f" {o['base']} llega en {formatear_minutos(o['costo'])} min, "
                      f"pero no tiene técnicos disponibles.")
        return texto

    if not tiene_trayectos_de_llegada(red, id_zona):
        return f"{nombre_zona} no tiene trayectos que lleguen a ella; no se puede atender desde ninguna base."
    if llegan_sin_tecnicos:
        bases = ", ".join(o["base"] for o in llegan_sin_tecnicos)
        return (f"Ninguna base con técnicos disponibles llega a {nombre_zona}. "
                f"Llegan, pero sin técnicos disponibles: {bases}.")
    return f"Ninguna base llega a {nombre_zona}: la red está desconectada entre las bases y la zona."
