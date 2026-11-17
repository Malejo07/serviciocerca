"""Autenticación y permisos de ServicioCerca. Ver docs/acceso-por-roles.md.

El dominio (app/dominio/) no sabe nada de usuarios: toda la seguridad vive aquí y en las rutas de main.py.
"""
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, Request

NOMBRE_COOKIE = "sc_sesion"
DURACION_SESION = 8 * 3600      # segundos
MAX_FALLOS = 5                  # intentos fallidos antes del bloqueo
SEGUNDOS_BLOQUEO = 30
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."

# Cada rol es un conjunto de permisos con nombre.
ROLES = {
    "administrador": ("Administrador", frozenset({"consultar", "configurar", "revisar", "administrar"}), "Acceso completo"),
    "configurador": ("Configurador de red", frozenset({"consultar", "configurar", "revisar"}),
                     "Configura la red y revisa los reportes de visita"),
    "tecnico": ("Técnico", frozenset({"consultar", "reportar"}), "Consulta la red, ve sus rutas y reporta sus visitas"),
}
ACCIONES = {
    "consultar": "consultar la red",
    "configurar": "configurar la red",
    "reportar": "reportar visitas",
    "revisar": "revisar el cumplimiento de los servicios",
    "administrar": "realizar tareas de administración",
}

# Cuentas de demostración. Si se define alguna clave propia por entorno, la demostración se desactiva.
USUARIOS_DEMO = {
    "admin": ("administrador", "Admin2026!", "SERVICIOCERCA_CLAVE_ADMIN"),
    "configurador": ("configurador", "Config2026!", "SERVICIOCERCA_CLAVE_CONFIGURADOR"),
    "tecnico": ("tecnico", "Tecnico2026!", "SERVICIOCERCA_CLAVE_TECNICO"),
}
# Técnico de la red al que está ligado el usuario «tecnico» (solo ve y reporta sus rutas).
TECNICO_DEMO = ("T1", "SERVICIOCERCA_TECNICO_ID")


# ---------- Errores de acceso (se responden como {"error": ...}) ----------

class ErrorAcceso(Exception):
    codigo = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoAutenticado(ErrorAcceso):
    codigo = 401

    def __init__(self, mensaje: str = "Debe iniciar sesión."):
        super().__init__(mensaje)


class CredencialesInvalidas(NoAutenticado):
    def __init__(self):
        super().__init__(MENSAJE_CREDENCIALES)


class SinPermiso(ErrorAcceso):
    codigo = 403

    def __init__(self, rol_nombre: str, permiso: str):
        super().__init__(f"El rol {rol_nombre} no tiene permiso para {ACCIONES[permiso]}.")


class DemasiadosIntentos(ErrorAcceso):
    codigo = 429

    def __init__(self, segundos: int):
        super().__init__(f"Demasiados intentos. Espere {segundos} segundos e intente de nuevo.")


# ---------- Contraseñas ----------

def hashear_clave(clave: str) -> str:
    """scrypt con sal propia. Formato: scrypt$<sal>$<hash>, ambos en hexadecimal."""
    sal = secrets.token_bytes(16)
    derivada = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${sal.hex()}${derivada.hex()}"


def verificar_clave(clave: str, almacenado: str) -> bool:
    try:
        esquema, sal, esperado = almacenado.split("$")
        if esquema != "scrypt":
            return False
        derivada = hashlib.scrypt(clave.encode(), salt=bytes.fromhex(sal), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(derivada, bytes.fromhex(esperado))
    except ValueError:
        return False


@lru_cache(maxsize=8)
def _tabla_de_hashes(claves: tuple) -> dict:
    """Hashea una vez por proceso las claves configuradas (el hash es lento a propósito)."""
    return {usuario: hashear_clave(clave) for usuario, clave in claves}


@lru_cache(maxsize=1)
def _hash_falso() -> str:
    """Se compara contra él cuando el usuario no existe, para que tarde igual y no revele qué usuarios hay."""
    return hashear_clave(secrets.token_hex(8))


# ---------- Usuarios y sesiones ----------

@dataclass(frozen=True)
class Usuario:
    usuario: str
    rol: str
    clave_hash: str
    tecnico_id: str | None = None   # solo para el rol técnico: el técnico de la red que es esta persona


class Seguridad:
    def __init__(self, entorno=None, reloj=time.time, duracion: int = DURACION_SESION):
        entorno = os.environ if entorno is None else entorno
        claves = {u: entorno.get(variable) or demo for u, (_, demo, variable) in USUARIOS_DEMO.items()}
        self.modo_demo = not any(entorno.get(variable) for _, _, variable in USUARIOS_DEMO.values())
        self._claves_demo = {u: demo for u, (_, demo, _) in USUARIOS_DEMO.items()}
        hashes = _tabla_de_hashes(tuple(sorted(claves.items())))
        tecnico_id = (entorno.get(TECNICO_DEMO[1]) or TECNICO_DEMO[0]).strip().upper()
        self.usuarios = {u: Usuario(u, USUARIOS_DEMO[u][0], hashes[u], tecnico_id if USUARIOS_DEMO[u][0] == "tecnico" else None)
                         for u in USUARIOS_DEMO}
        self._reloj = reloj
        self.duracion = duracion
        self._sesiones: dict[str, tuple[str, float]] = {}
        self._fallos: dict[str, tuple[int, float]] = {}   # usuario -> (fallos seguidos, bloqueado hasta)

    # --- datos que se muestran ---

    def datos_sesion(self, usuario: str) -> dict:
        nombre_rol, permisos, _ = ROLES[self.usuarios[usuario].rol]
        return {"usuario": usuario, "rol": self.usuarios[usuario].rol, "rol_nombre": nombre_rol,
                "permisos": sorted(permisos), "tecnico_id": self.usuarios[usuario].tecnico_id}

    def cuentas_demostracion(self) -> dict:
        if not self.modo_demo:
            return {"activa": False, "cuentas": []}
        cuentas = [{"usuario": u, "clave": self._claves_demo[u], "rol_nombre": ROLES[rol][0], "descripcion": ROLES[rol][2]}
                   for u, (rol, _, _) in USUARIOS_DEMO.items()]
        return {"activa": True, "cuentas": cuentas}

    # --- sesiones ---

    def abrir_sesion(self, usuario: str) -> str:
        ahora = self._reloj()
        self._sesiones = {t: s for t, s in self._sesiones.items() if s[1] > ahora}   # limpia las vencidas
        token = secrets.token_urlsafe(32)
        self._sesiones[token] = (usuario, ahora + self.duracion)
        return token

    def sesion_de(self, token: str | None) -> dict | None:
        sesion = self._sesiones.get(token) if token else None
        if sesion is None:
            return None
        if sesion[1] <= self._reloj():
            del self._sesiones[token]
            return None
        return self.datos_sesion(sesion[0])

    def cerrar_sesion(self, token: str | None) -> None:
        self._sesiones.pop(token, None)

    # --- inicio de sesión ---

    def iniciar_sesion(self, usuario: str, clave: str) -> tuple[str, dict]:
        llave, ahora = usuario.strip().lower()[:64], self._reloj()
        _, bloqueado_hasta = self._fallos.get(llave, (0, 0.0))
        if bloqueado_hasta > ahora:
            raise DemasiadosIntentos(int(bloqueado_hasta - ahora) + 1)

        cuenta = self.usuarios.get(llave)
        valida = verificar_clave(clave, cuenta.clave_hash if cuenta else _hash_falso())
        if not (cuenta and valida):
            fallos = self._fallos.get(llave, (0, 0.0))[0] + 1
            if len(self._fallos) > 1000:      # tope de memoria ante nombres inventados
                self._fallos.clear()
            self._fallos[llave] = (0, ahora + SEGUNDOS_BLOQUEO) if fallos >= MAX_FALLOS else (fallos, 0.0)
            raise CredencialesInvalidas()

        self._fallos.pop(llave, None)
        return self.abrir_sesion(llave), self.datos_sesion(llave)


# ---------- Dependencias de FastAPI ----------

def sesion_actual(request: Request) -> dict:
    datos = request.app.state.seguridad.sesion_de(request.cookies.get(NOMBRE_COOKIE))
    if datos is None:
        raise NoAutenticado()
    return datos


def requiere(permiso: str):
    """Dependencia que exige sesión y un permiso concreto."""
    def comprobar(sesion: dict = Depends(sesion_actual)) -> dict:
        if permiso not in sesion["permisos"]:
            raise SinPermiso(sesion["rol_nombre"], permiso)
        return sesion
    return comprobar
