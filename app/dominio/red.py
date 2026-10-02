"""Red de cobertura: grafo dirigido y ponderado de ubicaciones (bases y zonas).

Representación: lista de adyacencia
    self._adyacencia = {"B1": {"Z1": 10.0, "Z2": 7.0}, "Z1": {"B1": 10.0}, ...}
Cada clave es un nodo, y su diccionario interno son las aristas que salen de él
con su costo en minutos.
"""
import math
import re

from app.dominio.errores import DatoInvalido, ElementoDuplicado, ElementoNoEncontrado
from app.dominio.modelos import Nodo, Tecnico, TipoNodo, Trayecto

PATRON_ID = re.compile(r"^[A-Z0-9_-]{1,30}$")


def normalizar_id(valor) -> str:
    """Quita espacios, pasa a mayúsculas y valida el formato del identificador."""
    if not isinstance(valor, str):
        raise DatoInvalido("El identificador debe ser texto.")
    id_limpio = valor.strip().upper()
    if not PATRON_ID.match(id_limpio):
        raise DatoInvalido(
            f"Identificador '{valor}' inválido: use de 1 a 30 letras, números, '-' o '_', sin espacios."
        )
    return id_limpio


def validar_peso(peso) -> float:
    """El peso debe ser un número finito y estrictamente positivo."""
    # bool es subclase de int en Python, por eso se excluye explícitamente.
    if isinstance(peso, bool) or not isinstance(peso, (int, float)):
        raise DatoInvalido(f"El tiempo del trayecto debe ser un número, se recibió '{peso}'.")
    if math.isnan(peso) or math.isinf(peso):
        raise DatoInvalido("El tiempo del trayecto debe ser un número finito.")
    if peso <= 0:
        raise DatoInvalido(f"El tiempo del trayecto debe ser mayor que 0, se recibió {peso}.")
    return float(peso)


class RedCobertura:
    def __init__(self):
        self.nodos: dict[str, Nodo] = {}
        self.tecnicos: dict[str, Tecnico] = {}
        self._adyacencia: dict[str, dict[str, float]] = {}

    # ---------- Nodos ----------

    def agregar_nodo(self, id_nodo, nombre, tipo) -> Nodo:
        id_nodo = normalizar_id(id_nodo)
        nombre = self._validar_nombre(nombre)
        try:
            tipo = TipoNodo(str(tipo).strip().upper())
        except ValueError:
            raise DatoInvalido(f"Tipo '{tipo}' inválido: debe ser BASE o ZONA.") from None

        if id_nodo in self.nodos:
            raise ElementoDuplicado(f"Ya existe un nodo con id '{id_nodo}'.")

        nodo = Nodo(id=id_nodo, nombre=nombre, tipo=tipo)
        self.nodos[id_nodo] = nodo
        self._adyacencia[id_nodo] = {}
        return nodo

    def obtener_nodo(self, id_nodo) -> Nodo:
        id_nodo = normalizar_id(id_nodo)
        if id_nodo not in self.nodos:
            raise ElementoNoEncontrado(f"No existe el nodo '{id_nodo}'.")
        return self.nodos[id_nodo]

    # ---------- Técnicos ----------

    def agregar_tecnico(self, id_tecnico, nombre, base_id, disponible: bool = True) -> Tecnico:
        id_tecnico = normalizar_id(id_tecnico)
        nombre = self._validar_nombre(nombre)
        base = self.obtener_nodo(base_id)
        if base.tipo != TipoNodo.BASE:
            raise DatoInvalido(f"'{base.id}' es una zona; un técnico solo puede pertenecer a una base.")
        if id_tecnico in self.tecnicos:
            raise ElementoDuplicado(f"Ya existe un técnico con id '{id_tecnico}'.")

        tecnico = Tecnico(id=id_tecnico, nombre=nombre, base_id=base.id, disponible=bool(disponible))
        self.tecnicos[id_tecnico] = tecnico
        return tecnico

    # ---------- Trayectos (aristas) ----------

    def agregar_trayecto(self, origen, destino, minutos, bidireccional: bool = True) -> list[Trayecto]:
        """Registra A -> B (y B -> A si es bidireccional). Devuelve las aristas creadas.

        Primero se valida todo y después se modifica la red. Así, si algo falla,
        la red no queda a medias (por ejemplo, con solo uno de los dos sentidos).
        """
        origen = self.obtener_nodo(origen).id
        destino = self.obtener_nodo(destino).id
        minutos = validar_peso(minutos)
        if origen == destino:
            raise DatoInvalido("Un trayecto no puede empezar y terminar en el mismo nodo.")

        sentidos = [(origen, destino)]
        if bidireccional:
            sentidos.append((destino, origen))

        for a, b in sentidos:
            if b in self._adyacencia[a]:
                raise ElementoDuplicado(f"Ya existe el trayecto {a} -> {b}.")

        for a, b in sentidos:
            self._adyacencia[a][b] = minutos
        return [Trayecto(a, b, minutos) for a, b in sentidos]

    def vecinos(self, id_nodo) -> dict[str, float]:
        """Nodos a los que se llega directamente desde id_nodo, con su costo."""
        id_nodo = self.obtener_nodo(id_nodo).id
        return dict(self._adyacencia[id_nodo])  # copia para que nadie modifique el grafo desde fuera

    def trayectos(self) -> list[Trayecto]:
        return [
            Trayecto(origen, destino, minutos)
            for origen, salidas in self._adyacencia.items()
            for destino, minutos in salidas.items()
        ]

    # ---------- Utilidades ----------

    @staticmethod
    def _validar_nombre(nombre) -> str:
        if not isinstance(nombre, str) or not nombre.strip():
            raise DatoInvalido("El nombre no puede estar vacío.")
        return nombre.strip()
