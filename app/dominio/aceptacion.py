"""F4 — Aceptación demostrable: éxito, zona inexistente, red desconectada y peso inválido.

Cada escenario se ejecuta sobre una COPIA de la red de ejemplo, así que la red que el operador
tiene cargada no se modifica. Cada paso informa qué se hizo, qué se esperaba, qué se obtuvo y el
código HTTP que la API devolvería. Ver docs/F4-consola.md.

Uso desde la terminal:  python -m app.dominio.aceptacion
"""
from app.dominio.asignacion import mejor_base
from app.dominio.carga import red_de_ejemplo
from app.dominio.cobertura import consultar_cobertura
from app.dominio.costo import menor_costo
from app.dominio.errores import CODIGOS_HTTP, ErrorRed


def _llamar(funcion, *args):
    """Ejecuta una operación del dominio. Devuelve (código HTTP, resultado) o (código de error, mensaje)."""
    try:
        return 200, funcion(*args)
    except ErrorRed as error:
        return CODIGOS_HTTP.get(type(error), 400), error.mensaje


def _mensaje(codigo, resultado) -> str:
    return resultado["mensaje"] if codigo == 200 else resultado


def _paso(accion, esperado, codigo, resultado, cumple) -> dict:
    return {"accion": accion, "esperado": esperado, "obtenido": _mensaje(codigo, resultado),
            "codigo_http": codigo, "cumple": bool(cumple)}


def _escenario(id_escenario, nombre, descripcion, pasos) -> dict:
    return {"id": id_escenario, "nombre": nombre, "descripcion": descripcion,
            "cumple": all(p["cumple"] for p in pasos), "pasos": pasos}


# ---------- Escenarios ----------

def _exito() -> dict:
    red = red_de_ejemplo()
    pasos = []

    codigo, r = _llamar(consultar_cobertura, red, "B1", "Z3")
    pasos.append(_paso("Consultar cobertura de B1 a Z3 (Aranjuez)",
                       "Zona cubierta por el camino directo B1 -> Z3, de 1 tramo",
                       codigo, r, codigo == 200 and r["cubierta"] and r["camino"] == ["B1", "Z3"]))

    codigo, r = _llamar(menor_costo, red, "B1", "Z3")
    pasos.append(_paso("Calcular el menor costo de B1 a Z3",
                       "B1 -> Z2 -> Z3 en 15 min; la ruta con menos tramos (B1 -> Z3) cuesta 20 min",
                       codigo, r, codigo == 200 and r["camino"] == ["B1", "Z2", "Z3"] and r["costo"] == 15
                       and r["comparacion_bfs"]["costo"] == 20))

    codigo, r = _llamar(mejor_base, red, "Z5")
    mejor = r["mejor"] if codigo == 200 else None
    pasos.append(_paso("¿Qué técnico llega primero a Z5 (Robledo)?",
                       "Marta, desde B2, en 18 min",
                       codigo, r, mejor and mejor["base"] == "B2" and mejor["costo"] == 18
                       and [t["nombre"] for t in mejor["tecnicos_disponibles"]] == ["Marta"]))

    return _escenario("exito", "Consulta normal",
                      "La zona se puede atender y el sistema propone la mejor ruta y el técnico que llega primero.", pasos)


def _zona_inexistente() -> dict:
    red = red_de_ejemplo()
    pasos = []
    for accion, funcion in (("Consultar cobertura de B1 a Z99", consultar_cobertura),
                            ("Calcular el menor costo de B1 a Z99", menor_costo)):
        codigo, r = _llamar(funcion, red, "B1", "Z99")
        pasos.append(_paso(accion, "Error claro: No existe el nodo 'Z99'. (404)",
                           codigo, r, codigo == 404 and "Z99" in r))
    return _escenario("zona_inexistente", "Zona que no existe",
                      "Se pide una zona que no está registrada y el sistema responde con un mensaje claro.", pasos)


def _red_desconectada() -> dict:
    red = red_de_ejemplo()
    pasos = []

    codigo, r = _llamar(consultar_cobertura, red, "B2", "Z4")
    pasos.append(_paso("Consultar cobertura de B2 a Z4 (Manrique)",
                       "No cubierta; el mensaje explica que la red está desconectada",
                       codigo, r, codigo == 200 and not r["cubierta"] and "desconectada" in r["mensaje"]))

    codigo, r = _llamar(menor_costo, red, "B2", "Z4")
    pasos.append(_paso("Calcular el menor costo de B2 a Z4",
                       "No alcanzable, con el mismo motivo",
                       codigo, r, codigo == 200 and not r["alcanzable"] and "desconectada" in r["mensaje"]))

    codigo, r = _llamar(mejor_base, red, "Z7")
    pasos.append(_paso("¿Qué técnico llega primero a Z7 (Poblado)?",
                       "Z7 no tiene trayectos de llegada; no se puede atender desde ninguna base",
                       codigo, r, codigo == 200 and r["mejor"] is None and "no tiene trayectos" in r["mensaje"]))

    return _escenario("red_desconectada", "Zona sin conexión",
                      "No hay camino hasta la zona: el sistema lo explica en lugar de fallar.", pasos)


def _peso_invalido() -> dict:
    red = red_de_ejemplo()
    pasos = []

    for minutos in (-5, 0):
        antes = red.trayectos()
        codigo, r = _llamar(red.agregar_trayecto, "B1", "Z7", minutos)
        pasos.append(_paso(f"Registrar el trayecto B1 -> Z7 con {minutos} min",
                           "Rechazado: el tiempo debe ser mayor que 0; la red queda sin cambios (400)",
                           codigo, r, codigo == 400 and "mayor que 0" in r and red.trayectos() == antes))

    # Un peso inválido que llegara al grafo por fuera de la API no debe producir una ruta equivocada.
    red._adyacencia["B1"]["Z1"] = 0
    codigo, r = _llamar(menor_costo, red, "B1", "Z3")
    pasos.append(_paso("Calcular el menor costo con el peso de B1 -> Z1 alterado a 0 fuera de la API",
                       "El cálculo se detiene y el error nombra el trayecto B1 -> Z1 (400)",
                       codigo, r, codigo == 400 and "B1 -> Z1" in r))

    return _escenario("peso_invalido", "Tiempo inválido",
                      "Los tiempos en cero o negativos se rechazan al registrar y también al calcular.", pasos)


# ---------- API del módulo ----------

def ejecutar_aceptacion() -> dict:
    escenarios = [_exito(), _zona_inexistente(), _red_desconectada(), _peso_invalido()]
    cumplidos = sum(1 for e in escenarios if e["cumple"])
    return {"red_usada": "Copia de la red de ejemplo (la red cargada en la consola no se modifica)",
            "total": len(escenarios), "cumplidos": cumplidos, "todos_cumplidos": cumplidos == len(escenarios),
            "escenarios": escenarios}


def _celda(texto) -> str:
    """Deja el texto en una sola línea y sin barras verticales para no romper la tabla Markdown."""
    return " ".join(str(texto).split()).replace("|", "\\|")


def generar_reporte_markdown(resultado: dict) -> str:
    lineas = ["# Evidencia de aceptación — ServicioCerca (F4)", "",
              f"**Resultado:** {resultado['cumplidos']} de {resultado['total']} escenarios cumplidos.", "",
              f"Red usada: {resultado['red_usada']}.", ""]
    for numero, e in enumerate(resultado["escenarios"], start=1):
        estado = "Cumplido ✔" if e["cumple"] else "No cumplido ✖"
        lineas += [f"## {numero}. {e['nombre']} — {estado}", "", e["descripcion"], "",
                   "| Paso | Esperado | Obtenido | HTTP | Resultado |", "| --- | --- | --- | --- | --- |"]
        for p in e["pasos"]:
            lineas.append(f"| {_celda(p['accion'])} | {_celda(p['esperado'])} | {_celda(p['obtenido'])} | "
                          f"{p['codigo_http']} | {'✔' if p['cumple'] else '✖'} |")
        lineas.append("")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(generar_reporte_markdown(ejecutar_aceptacion()))
