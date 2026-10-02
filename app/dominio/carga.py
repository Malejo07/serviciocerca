"""Construye una red a partir de un diccionario (por ejemplo, leído de JSON).

Usa los mismos métodos de RedCobertura, así los datos de ejemplo pasan por
las mismas validaciones que los registrados a mano.
"""
import json
from pathlib import Path

from app.dominio.red import RedCobertura

RUTA_EJEMPLO = Path(__file__).resolve().parent.parent / "datos" / "red_ejemplo.json"


def red_desde_dict(datos: dict) -> RedCobertura:
    red = RedCobertura()
    for n in datos.get("nodos", []):
        red.agregar_nodo(n["id"], n["nombre"], n["tipo"])
    for t in datos.get("tecnicos", []):
        red.agregar_tecnico(t["id"], t["nombre"], t["base_id"], t.get("disponible", True))
    for tr in datos.get("trayectos", []):
        red.agregar_trayecto(tr["origen"], tr["destino"], tr["minutos"], tr.get("bidireccional", True))
    return red


def red_de_ejemplo() -> RedCobertura:
    with open(RUTA_EJEMPLO, encoding="utf-8") as f:
        return red_desde_dict(json.load(f))
