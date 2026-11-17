"""Esquemas de entrada/salida de la API (Pydantic).

Aquí solo se valida la forma del JSON (que lleguen los campos y el tipo).
Las reglas del negocio (pesos > 0, duplicados, etc.) las valida el dominio.
"""
from pydantic import BaseModel, Field


class NodoEntrada(BaseModel):
    id: str = Field(examples=["Z1"])
    nombre: str = Field(examples=["Chapinero"])
    tipo: str = Field(examples=["ZONA"], description="BASE o ZONA")
    latitud: float | None = Field(default=None, examples=[6.2442], description="Opcional; va junto con la longitud")
    longitud: float | None = Field(default=None, examples=[-75.5812])


class TecnicoEntrada(BaseModel):
    id: str = Field(examples=["T1"])
    nombre: str = Field(examples=["Ana"])
    base_id: str = Field(examples=["B1"])
    disponible: bool = True


class DisponibilidadEntrada(BaseModel):
    disponible: bool = Field(strict=True, description="true: puede recibir servicios; false: no")


class ServicioEntrada(BaseModel):
    zona: str = Field(examples=["Z3"])
    tolerancia: float = Field(default=10, description="Minutos extra sobre el mejor tiempo que aún compiten por equidad")


class EstadoServicioEntrada(BaseModel):
    estado: str = Field(examples=["CUMPLIDO"], description="CUMPLIDO, NO_CUMPLIDO o ASIGNADO (reabrir)")
    nota: str | None = Field(default=None, description="Comentario opcional de quien revisa")


class NovedadEntrada(BaseModel):
    tipo: str = Field(examples=["TRAFICO"], description="TRAFICO, CLIENTE_AUSENTE, ACCESO, EQUIPO u OTRO")
    detalle: str = Field(examples=["Vía cerrada por obras en la carrera 50"])


class ReporteEntrada(BaseModel):
    texto: str = Field(examples=["Visita realizada, se atendió la zona sin problemas."])
    novedad: NovedadEntrada | None = None


class TrayectoEntrada(BaseModel):
    origen: str = Field(examples=["B1"])
    destino: str = Field(examples=["Z1"])
    minutos: float = Field(examples=[10], description="Tiempo estimado, debe ser > 0")
    bidireccional: bool = True


class NodoSalida(BaseModel):
    id: str
    nombre: str
    tipo: str
    latitud: float | None = None
    longitud: float | None = None


class TecnicoSalida(BaseModel):
    id: str
    nombre: str
    base_id: str
    disponible: bool


class TrayectoSalida(BaseModel):
    origen: str
    destino: str
    minutos: float


class RedSalida(BaseModel):
    nodos: list[NodoSalida]
    tecnicos: list[TecnicoSalida]
    trayectos: list[TrayectoSalida]


class SesionEntrada(BaseModel):
    usuario: str = Field(min_length=1, max_length=64)
    clave: str = Field(min_length=1, max_length=128)   # el tope evita gastar el hash en claves enormes
