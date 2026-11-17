"""Errores del dominio. Cada uno tiene un mensaje pensado para el usuario."""


class ErrorRed(Exception):
    """Error base de la red de cobertura."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class DatoInvalido(ErrorRed):
    """Un dato no cumple el formato o las reglas (ID, tipo, peso...)."""


class ElementoDuplicado(ErrorRed):
    """Ya existe un elemento con ese identificador o esa conexión."""


class ElementoNoEncontrado(ErrorRed):
    """Se hace referencia a un elemento que no está registrado."""


# Código HTTP que la API devuelve para cada tipo de error (lo usan main.py y la aceptación de la F4).
CODIGOS_HTTP = {
    DatoInvalido: 400,
    ElementoNoEncontrado: 404,
    ElementoDuplicado: 409,
}
