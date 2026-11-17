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


# ======================================================================
# Asignación equitativa de servicios
# ======================================================================
#
# Regla (ver docs/asignacion-equitativa.md):
#  1. Se calcula el mejor tiempo posible a la zona entre las bases con técnicos disponibles.
#  2. Compiten los técnicos que lleguen a menos de `tolerancia` minutos de ese mejor tiempo.
#  3. Gana quien lleva MENOS servicios asignados; si hay empate, el que llega más rápido; luego el id.

from app.dominio.errores import ElementoNoEncontrado, ServicioAjeno, SinTecnicoDisponible
from app.dominio.modelos import (NOMBRES_NOVEDAD, EstadoServicio, Novedad, ReporteVisita, Revision, Servicio,
                                 TipoNovedad)

TOLERANCIA_POR_DEFECTO = 10   # minutos


def _servicios_de(red: RedCobertura, id_tecnico: str) -> int:
    return sum(1 for s in red.servicios.values() if s.tecnico_id == id_tecnico)


def _validar_tolerancia(tolerancia) -> float:
    if isinstance(tolerancia, bool) or not isinstance(tolerancia, (int, float)) or tolerancia != tolerancia \
            or tolerancia < 0 or tolerancia == float("inf"):
        raise DatoInvalido("La tolerancia debe ser un número de minutos mayor o igual a 0.")
    return tolerancia


def asignar_servicio(red: RedCobertura, zona, tolerancia=TOLERANCIA_POR_DEFECTO) -> dict:
    """Asigna la zona a un técnico por la ruta más rápida de su base y guarda el servicio."""
    tolerancia = _validar_tolerancia(tolerancia)
    analisis = mejor_base(red, zona)
    nodo_zona = red.obtener_nodo(zona)
    nombre_zona = f"{nodo_zona.id} ({nodo_zona.nombre})"

    candidatos = [{"tecnico": t, "opcion": o}
                  for o in analisis["opciones"] if o["alcanzable"]
                  for t in o["tecnicos_disponibles"]]
    if not candidatos:
        raise SinTecnicoDisponible(analisis["mensaje"])

    mejor_tiempo = min(c["opcion"]["costo"] for c in candidatos)
    for c in candidatos:
        c["servicios"] = _servicios_de(red, c["tecnico"]["id"])
        c["compite"] = c["opcion"]["costo"] <= mejor_tiempo + tolerancia
    elegido = min((c for c in candidatos if c["compite"]),
                  key=lambda c: (c["servicios"], c["opcion"]["costo"], c["tecnico"]["id"]))

    o = elegido["opcion"]
    id_servicio = f"S{len(red.servicios) + 1}"
    servicio = Servicio(id=id_servicio, zona_id=nodo_zona.id, tecnico_id=elegido["tecnico"]["id"],
                        base_id=o["base"], camino=list(o["camino"]), minutos=o["costo"], tramos=o["tramos"])
    red.servicios[id_servicio] = servicio

    detalle = []
    for c in sorted(candidatos, key=lambda c: (c["opcion"]["costo"], c["tecnico"]["id"])):
        if c is elegido:
            estado = "Asignado"
        elif not c["compite"]:
            estado = f"Fuera de tolerancia (+{formatear_minutos(c['opcion']['costo'] - mejor_tiempo)} min)"
        else:
            estado = "Tiene más servicios" if c["servicios"] > elegido["servicios"] else "Llega más tarde"
        detalle.append({"tecnico_id": c["tecnico"]["id"], "nombre": c["tecnico"]["nombre"], "base": c["opcion"]["base"],
                        "minutos": c["opcion"]["costo"], "servicios_previos": c["servicios"], "estado": estado})

    nombre = elegido["tecnico"]["nombre"]
    mensaje = (f"{id_servicio}: {nombre} atenderá {nombre_zona} desde {o['base']}, "
               f"{formatear_minutos(o['costo'])} min por {' -> '.join(o['camino'])}. "
               f"Llevaba {elegido['servicios']} servicio(s) asignado(s).")
    mas_rapido = [c for c in candidatos if c["opcion"]["costo"] < o["costo"] and c is not elegido]
    if mas_rapido:
        c = min(mas_rapido, key=lambda c: (c["opcion"]["costo"], c["tecnico"]["id"]))
        mensaje += (f" {c['tecnico']['nombre']} llegaba en {formatear_minutos(c['opcion']['costo'])} min, "
                    f"pero tiene {c['servicios']} servicio(s) y se prefirió repartir la carga.")
    return {"servicio": serializar_servicio(red, servicio), "candidatos": detalle,
            "tolerancia": tolerancia, "mensaje": mensaje}


MAX_REPORTE, MAX_NOVEDAD, MAX_NOTA = 1000, 500, 500


def serializar_servicio(red: RedCobertura, s: Servicio) -> dict:
    tecnico, zona = red.tecnicos.get(s.tecnico_id), red.nodos.get(s.zona_id)
    reporte = None
    if s.reporte:
        novedad = s.reporte.novedad
        reporte = {"texto": s.reporte.texto, "fecha": s.reporte.fecha,
                   "novedad": {"tipo": novedad.tipo.value, "tipo_nombre": NOMBRES_NOVEDAD[novedad.tipo],
                               "detalle": novedad.detalle} if novedad else None}
    revision = {"revisor": s.revision.revisor, "fecha": s.revision.fecha, "nota": s.revision.nota} if s.revision else None
    return {"id": s.id, "zona": s.zona_id, "zona_nombre": zona.nombre if zona else s.zona_id,
            "tecnico_id": s.tecnico_id, "tecnico_nombre": tecnico.nombre if tecnico else s.tecnico_id,
            "base": s.base_id, "camino": s.camino, "minutos": s.minutos, "tramos": s.tramos,
            "estado": s.estado.value, "reporte": reporte, "revision": revision}


def _servicio(red: RedCobertura, id_servicio) -> Servicio:
    clave = str(id_servicio).strip().upper()
    if clave not in red.servicios:
        raise ElementoNoEncontrado(f"No existe el servicio '{clave}'.")
    return red.servicios[clave]


def _texto(valor, campo: str, maximo: int, obligatorio: bool = True) -> str:
    if valor is None:
        valor = ""
    if not isinstance(valor, str):
        raise DatoInvalido(f"{campo} debe ser texto.")
    valor = " ".join(valor.split())
    if obligatorio and not valor:
        raise DatoInvalido(f"{campo} no puede estar vacío.")
    if len(valor) > maximo:
        raise DatoInvalido(f"{campo} no puede pasar de {maximo} caracteres.")
    return valor


def reportar_visita(red: RedCobertura, id_servicio, texto, novedad_tipo=None, novedad_detalle=None,
                    tecnico_id=None, fecha: str = "") -> dict:
    """El técnico informa cómo fue la visita (y la novedad, si la hubo). El servicio queda por revisar.

    `tecnico_id` es quien reporta: si se indica, el servicio debe ser suyo. Puede corregir su reporte
    mientras nadie lo haya revisado.
    """
    servicio = _servicio(red, id_servicio)
    if tecnico_id is not None and servicio.tecnico_id != str(tecnico_id).strip().upper():
        raise ServicioAjeno("Ese servicio no está asignado a usted.")
    if servicio.estado in (EstadoServicio.CUMPLIDO, EstadoServicio.NO_CUMPLIDO):
        raise DatoInvalido("Este servicio ya fue revisado. Pida a quien revisa que lo reabra para corregir el reporte.")

    texto = _texto(texto, "El reporte", MAX_REPORTE)
    novedad = None
    if novedad_tipo or (novedad_detalle and str(novedad_detalle).strip()):
        try:
            tipo = TipoNovedad(str(novedad_tipo or "").strip().upper())
        except ValueError:
            raise DatoInvalido("Tipo de novedad inválido: use " + ", ".join(t.value for t in TipoNovedad) + ".") from None
        novedad = Novedad(tipo, _texto(novedad_detalle, "El detalle de la novedad", MAX_NOVEDAD))

    servicio.reporte = ReporteVisita(texto=texto, fecha=fecha, novedad=novedad)
    servicio.estado = EstadoServicio.POR_REVISAR
    return serializar_servicio(red, servicio)


def marcar_servicio(red: RedCobertura, id_servicio, estado, nota=None, revisor: str = "", fecha: str = "") -> dict:
    """Quien revisa decide si el servicio se cumplió (con una nota opcional) o lo reabre.

    CUMPLIDO y NO_CUMPLIDO cierran el servicio. ASIGNADO lo reabre: queda «por revisar» si ya hay reporte.
    """
    servicio = _servicio(red, id_servicio)
    try:
        nuevo = EstadoServicio(str(estado).strip().upper())
    except ValueError:
        raise DatoInvalido("Estado inválido: use CUMPLIDO, NO_CUMPLIDO o ASIGNADO (reabrir).") from None
    if nuevo == EstadoServicio.POR_REVISAR:
        raise DatoInvalido("Estado inválido: «por revisar» lo pone el reporte del técnico. Use CUMPLIDO, NO_CUMPLIDO o ASIGNADO (reabrir).")
    if nuevo == EstadoServicio.ASIGNADO:
        servicio.revision = None
        servicio.estado = EstadoServicio.POR_REVISAR if servicio.reporte else EstadoServicio.ASIGNADO
    else:
        servicio.revision = Revision(revisor=revisor, fecha=fecha, nota=_texto(nota, "La nota", MAX_NOTA, obligatorio=False))
        servicio.estado = nuevo
    return serializar_servicio(red, servicio)


def resumen_servicios(red: RedCobertura, solo_tecnico: str | None = None) -> dict:
    """Un renglón por técnico: servicios asignados y cuántos se cumplieron.

    Con `solo_tecnico` se devuelve únicamente lo de ese técnico (lo que ve el perfil técnico).
    """
    visibles = sorted(red.tecnicos.values(), key=lambda t: t.id)
    if solo_tecnico is not None:
        visibles = [t for t in visibles if t.id == str(solo_tecnico).strip().upper()]
    tecnicos = []
    for t in visibles:
        propios = [s for s in red.servicios.values() if s.tecnico_id == t.id]
        cuenta = lambda e: sum(1 for s in propios if s.estado == e)   # noqa: E731
        cumplidos, fallidos = cuenta(EstadoServicio.CUMPLIDO), cuenta(EstadoServicio.NO_CUMPLIDO)
        cerrados = cumplidos + fallidos
        tecnicos.append({"id": t.id, "nombre": t.nombre, "base": t.base_id, "disponible": t.disponible,
                         "asignados": len(propios), "cumplidos": cumplidos, "no_cumplidos": fallidos,
                         "por_revisar": cuenta(EstadoServicio.POR_REVISAR), "en_ruta": cuenta(EstadoServicio.ASIGNADO),
                         "con_novedad": sum(1 for s in propios if s.reporte and s.reporte.novedad),
                         "cumplimiento": round(100 * cumplidos / cerrados) if cerrados else None})
    ids = {t["id"] for t in tecnicos}
    servicios = [serializar_servicio(red, s) for s in red.servicios.values() if s.tecnico_id in ids]
    suma = lambda clave: sum(t[clave] for t in tecnicos)   # noqa: E731
    return {"tecnicos": tecnicos,
            "total": {"asignados": suma("asignados"), "cumplidos": suma("cumplidos"), "no_cumplidos": suma("no_cumplidos"),
                      "por_revisar": suma("por_revisar"), "en_ruta": suma("en_ruta"), "con_novedad": suma("con_novedad")},
            "servicios": servicios}
