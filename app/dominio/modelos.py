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
    latitud: float | None = None     # ubicación geográfica opcional (grados)
    longitud: float | None = None


@dataclass
class Tecnico:
    """Técnico asociado a una base. NO es un nodo del grafo (ver docs/F1-modelado.md)."""
    id: str
    nombre: str
    base_id: str
    disponible: bool = True


class EstadoServicio(str, Enum):
    ASIGNADO = "ASIGNADO"          # el técnico va en camino
    POR_REVISAR = "POR_REVISAR"    # el técnico envió su reporte; falta que alguien decida
    CUMPLIDO = "CUMPLIDO"          # el revisor confirmó que se atendió la zona
    NO_CUMPLIDO = "NO_CUMPLIDO"    # el revisor decidió que no se cumplió


class TipoNovedad(str, Enum):
    TRAFICO = "TRAFICO"
    CLIENTE_AUSENTE = "CLIENTE_AUSENTE"
    ACCESO = "ACCESO"
    EQUIPO = "EQUIPO"
    OTRO = "OTRO"


NOMBRES_NOVEDAD = {
    TipoNovedad.TRAFICO: "Tráfico o vía cerrada",
    TipoNovedad.CLIENTE_AUSENTE: "Cliente ausente",
    TipoNovedad.ACCESO: "Sin acceso al lugar",
    TipoNovedad.EQUIPO: "Falla de equipo o herramienta",
    TipoNovedad.OTRO: "Otra novedad",
}


@dataclass
class Novedad:
    tipo: TipoNovedad
    detalle: str


@dataclass
class ReporteVisita:
    texto: str
    fecha: str
    novedad: Novedad | None = None


@dataclass
class Revision:
    """Decisión de quien revisa el servicio (administrador o configurador)."""
    revisor: str
    fecha: str
    nota: str = ""


@dataclass
class Servicio:
    """Atención de una zona asignada a un técnico, con la ruta planificada."""
    id: str
    zona_id: str
    tecnico_id: str
    base_id: str
    camino: list[str]
    minutos: float
    tramos: int
    estado: EstadoServicio = EstadoServicio.ASIGNADO
    reporte: ReporteVisita | None = None
    revision: Revision | None = None


@dataclass
class Trayecto:
    """Arista dirigida origen -> destino con su costo en minutos."""
    origen: str
    destino: str
    minutos: float
