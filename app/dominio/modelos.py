"""Entidades de la red de cobertura."""
from dataclasses import dataclass
from enum import Enum


class TipoNodo(str, Enum):
    BASE = "BASE"
    ZONA = "ZONA"


@dataclass
class Nodo:
    """Ubicación física de la ciudad: una base o una zona (barrio)."""
    id: str
    nombre: str
    tipo: TipoNodo


@dataclass
class Tecnico:
    """Técnico asociado a una base. NO es un nodo del grafo (ver docs/F1-modelado.md)."""
    id: str
    nombre: str
    base_id: str
    disponible: bool = True


@dataclass
class Trayecto:
    """Arista dirigida origen -> destino con su costo en minutos."""
    origen: str
    destino: str
    minutos: float
