"""Aplicación FastAPI de ServicioCerca."""
from dataclasses import asdict
from pathlib import Path

import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.dominio.aceptacion import ejecutar_aceptacion, generar_reporte_markdown
from app.dominio.asignacion import (asignar_servicio, marcar_servicio, mejor_base, reportar_visita,
                                    resumen_servicios)
from app.dominio.carga import red_de_ejemplo
from app.dominio.cobertura import consultar_cobertura, listar_alcance
from app.dominio.costo import menor_costo
from app.dominio.errores import CODIGOS_HTTP, ErrorRed
from app.dominio.red import RedCobertura
from app.esquemas import (DisponibilidadEntrada, EstadoServicioEntrada, NodoEntrada, RedSalida, ReporteEntrada,
                          ServicioEntrada, SesionEntrada, TecnicoEntrada, TrayectoEntrada)
from app.seguridad import (DURACION_SESION, NOMBRE_COOKIE, ErrorAcceso, Seguridad, requiere, sesion_actual)

CARPETA_STATIC = Path(__file__).resolve().parent / "static"
SIN_CACHE = {"Cache-Control": "no-store"}   # al cerrar sesión, "Atrás" no debe mostrar la consola


def crear_app(reloj=time.time, duracion_sesion: int = DURACION_SESION) -> FastAPI:
    app = FastAPI(title="ServicioCerca", description="Red de cobertura de técnicos")
    app.state.red = RedCobertura()  # la red vive en memoria (datos sintéticos)
    app.state.seguridad = Seguridad(reloj=reloj, duracion=duracion_sesion)

    def ahora() -> str:
        return datetime.fromtimestamp(reloj(), timezone.utc).isoformat(timespec="seconds")

    # ---------- Manejo de errores legible ----------

    @app.exception_handler(ErrorRed)
    async def manejar_error_red(_: Request, exc: ErrorRed):
        return JSONResponse(status_code=CODIGOS_HTTP.get(type(exc), 400), content={"error": exc.mensaje})

    @app.exception_handler(ErrorAcceso)
    async def manejar_error_acceso(_: Request, exc: ErrorAcceso):
        return JSONResponse(status_code=exc.codigo, content={"error": exc.mensaje})

    @app.exception_handler(RequestValidationError)
    async def manejar_json_invalido(_: Request, exc: RequestValidationError):
        detalles = []
        for e in exc.errors():
            campo = ".".join(str(parte) for parte in e["loc"][1:])
            detalles.append(f"{campo}: {e['msg']}")
        return JSONResponse(status_code=400, content={"error": "Datos con formato incorrecto.", "detalles": detalles})

    def obtener_red(request: Request) -> RedCobertura:
        return request.app.state.red

    # ---------- Endpoints de la red ----------

    @app.get("/api/red", response_model=RedSalida, dependencies=[Depends(requiere("consultar"))])
    def consultar_red(red: RedCobertura = Depends(obtener_red)):
        return {
            "nodos": [asdict(n) for n in red.nodos.values()],
            "tecnicos": [asdict(t) for t in red.tecnicos.values()],
            "trayectos": [asdict(t) for t in red.trayectos()],
        }

    @app.post("/api/nodos", status_code=201, dependencies=[Depends(requiere("configurar"))])
    def registrar_nodo(datos: NodoEntrada, red: RedCobertura = Depends(obtener_red)):
        return asdict(red.agregar_nodo(datos.id, datos.nombre, datos.tipo, datos.latitud, datos.longitud))

    @app.post("/api/tecnicos", status_code=201, dependencies=[Depends(requiere("configurar"))])
    def registrar_tecnico(datos: TecnicoEntrada, red: RedCobertura = Depends(obtener_red)):
        return asdict(red.agregar_tecnico(datos.id, datos.nombre, datos.base_id, datos.disponible))

    @app.patch("/api/tecnicos/{id_tecnico}", dependencies=[Depends(requiere("configurar"))])
    def cambiar_disponibilidad(id_tecnico: str, datos: DisponibilidadEntrada, red: RedCobertura = Depends(obtener_red)):
        """Activa o desactiva a un técnico sin borrarlo."""
        return asdict(red.cambiar_disponibilidad(id_tecnico, datos.disponible))

    @app.post("/api/trayectos", status_code=201, dependencies=[Depends(requiere("configurar"))])
    def registrar_trayecto(datos: TrayectoEntrada, red: RedCobertura = Depends(obtener_red)):
        creados = red.agregar_trayecto(datos.origen, datos.destino, datos.minutos, datos.bidireccional)
        return [asdict(t) for t in creados]

    @app.post("/api/red/ejemplo", dependencies=[Depends(requiere("configurar"))])
    def cargar_ejemplo(request: Request):
        request.app.state.red = red_de_ejemplo()
        return {"mensaje": "Red de ejemplo cargada."}

    @app.delete("/api/red", dependencies=[Depends(requiere("administrar"))])
    def vaciar_red(request: Request):
        request.app.state.red = RedCobertura()
        return {"mensaje": "Red vaciada."}

    # ---------- F2: cobertura ----------
 
    @app.get("/api/cobertura", dependencies=[Depends(requiere("consultar"))])
    def cobertura_de_zona(origen: str, zona: str, red: RedCobertura = Depends(obtener_red)):
        """¿La zona está dentro de la cobertura posible desde el origen? (BFS)"""
        return consultar_cobertura(red, origen, zona)
 
    @app.get("/api/cobertura/alcance/{base_id}", dependencies=[Depends(requiere("consultar"))])
    def alcance_de_base(base_id: str, red: RedCobertura = Depends(obtener_red)):
        """Zonas que se pueden alcanzar desde una base (BFS)."""
        return listar_alcance(red, base_id)
    
    # ---------- F3: menor costo ----------

    @app.get("/api/menor-costo", dependencies=[Depends(requiere("consultar"))])
    def menor_costo_de_zona(origen: str, zona: str, red: RedCobertura = Depends(obtener_red)):
        """Camino de menor tiempo total desde el origen hasta la zona (Dijkstra)."""
        return menor_costo(red, origen, zona)

    @app.get("/api/menor-costo/mejor-base", dependencies=[Depends(requiere("consultar"))])
    def mejor_base_para_zona(zona: str, red: RedCobertura = Depends(obtener_red)):
        """Base con técnicos disponibles que llega antes a la zona (Dijkstra desde cada base)."""
        return mejor_base(red, zona)

    # ---------- Servicios: asignación equitativa y seguimiento ----------

    @app.post("/api/servicios", status_code=201, dependencies=[Depends(requiere("configurar"))])
    def asignar(datos: ServicioEntrada, red: RedCobertura = Depends(obtener_red)):
        """Asigna la zona al técnico que llega por la ruta más rápida, repartiendo la carga."""
        return asignar_servicio(red, datos.zona, datos.tolerancia)

    @app.get("/api/servicios")
    def servicios(sesion: dict = Depends(requiere("consultar")), red: RedCobertura = Depends(obtener_red)):
        """Resumen por técnico. Quien revisa ve todo; el técnico, solo sus propias rutas."""
        if "revisar" in sesion["permisos"]:
            return resumen_servicios(red)
        return resumen_servicios(red, solo_tecnico=sesion.get("tecnico_id") or "")

    @app.post("/api/servicios/{id_servicio}/reporte")
    def reportar(id_servicio: str, datos: ReporteEntrada, sesion: dict = Depends(requiere("reportar")),
                 red: RedCobertura = Depends(obtener_red)):
        """El técnico reporta su visita (y la novedad, si la hubo) en un servicio suyo."""
        novedad = datos.novedad
        return reportar_visita(red, id_servicio, datos.texto, novedad.tipo if novedad else None,
                               novedad.detalle if novedad else None, tecnico_id=sesion.get("tecnico_id") or "",
                               fecha=ahora())

    @app.patch("/api/servicios/{id_servicio}")
    def estado_de_servicio(id_servicio: str, datos: EstadoServicioEntrada, sesion: dict = Depends(requiere("revisar")),
                           red: RedCobertura = Depends(obtener_red)):
        """Quien revisa decide si el servicio se cumplió, con una nota opcional, o lo reabre."""
        return marcar_servicio(red, id_servicio, datos.estado, datos.nota, revisor=sesion["usuario"], fecha=ahora())

    @app.delete("/api/servicios", dependencies=[Depends(requiere("administrar"))])
    def reiniciar_servicios(red: RedCobertura = Depends(obtener_red)):
        red.servicios.clear()
        return {"mensaje": "Servicios reiniciados."}

    # ---------- F4: aceptación demostrable ----------

    @app.get("/api/aceptacion", dependencies=[Depends(requiere("administrar"))])
    def aceptacion():
        """Ejecuta los escenarios de éxito, zona inexistente, red desconectada y peso inválido.

        Corre sobre una copia de la red de ejemplo: no modifica la red cargada, por eso es un GET.
        """
        return ejecutar_aceptacion()

    @app.get("/api/aceptacion/evidencia", dependencies=[Depends(requiere("administrar"))])
    def evidencia_de_aceptacion():
        """Informe de la aceptación en Markdown, listo para descargar."""
        return PlainTextResponse(
            generar_reporte_markdown(ejecutar_aceptacion()),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="evidencia-aceptacion-F4.md"'},
        )

    # ---------- Sesión ----------

    @app.post("/api/sesion")
    def iniciar_sesion(datos: SesionEntrada, request: Request, respuesta: Response):
        token, sesion = request.app.state.seguridad.iniciar_sesion(datos.usuario, datos.clave)
        respuesta.set_cookie(NOMBRE_COOKIE, token, max_age=request.app.state.seguridad.duracion, path="/",
                             httponly=True, samesite="strict", secure=request.url.scheme == "https")
        return sesion

    @app.get("/api/sesion")
    def ver_sesion(sesion: dict = Depends(sesion_actual)):
        return sesion

    @app.delete("/api/sesion")
    def cerrar_sesion(request: Request, respuesta: Response):
        request.app.state.seguridad.cerrar_sesion(request.cookies.get(NOMBRE_COOKIE))
        respuesta.delete_cookie(NOMBRE_COOKIE, path="/")
        return {"mensaje": "Sesión cerrada."}

    @app.get("/api/acceso/demostracion")
    def cuentas_de_demostracion(request: Request):
        """Cuentas de ejemplo para la pantalla de acceso; vacío si se configuraron claves propias."""
        return request.app.state.seguridad.cuentas_demostracion()

    def hay_sesion(request: Request) -> bool:
        return request.app.state.seguridad.sesion_de(request.cookies.get(NOMBRE_COOKIE)) is not None

    # ---------- Páginas ----------

    app.mount("/static", StaticFiles(directory=CARPETA_STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse("/consola", status_code=303)   # la consola pide iniciar sesión

    @app.get("/acceso", include_in_schema=False)
    def acceso(request: Request):
        if hay_sesion(request):
            return RedirectResponse("/consola", status_code=303)
        return FileResponse(CARPETA_STATIC / "login.html", headers=SIN_CACHE)

    @app.get("/consola", include_in_schema=False)
    def consola(request: Request):
        if not hay_sesion(request):
            return RedirectResponse("/acceso", status_code=303)
        return FileResponse(CARPETA_STATIC / "index.html", headers=SIN_CACHE)

    return app


app = crear_app()
