"""Esquemas de entrada/salida de la API (Pydantic).

Aquí solo se valida la forma del JSON (que lleguen los campos y el tipo).
Las reglas del negocio (pesos > 0, duplicados, etc.) las valida el dominio.
"""
from pydantic import BaseModel, Field


class NodoEntrada(BaseModel):
    id: str = Field(examples=["Z1"])
    nombre: str = Field(examples=["Chapinero"])
    tipo: str = Field(examples=["ZONA"], description="BASE o ZONA")


class TecnicoEntrada(BaseModel):
    id: str = Field(examples=["T1"])
    nombre: str = Field(examples=["Ana"])
    base_id: str = Field(examples=["B1"])
    disponible: bool = True


class TrayectoEntrada(BaseModel):
    origen: str = Field(examples=["B1"])
    destino: str = Field(examples=["Z1"])
    minutos: float = Field(examples=[10], description="Tiempo estimado, debe ser > 0")
    bidireccional: bool = True


class NodoSalida(BaseModel):
    id: str
    nombre: str
    tipo: str


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
