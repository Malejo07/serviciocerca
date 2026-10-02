"""Aplicación FastAPI de ServicioCerca."""
from dataclasses import asdict
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.dominio.carga import red_de_ejemplo
from app.dominio.errores import DatoInvalido, ElementoDuplicado, ElementoNoEncontrado, ErrorRed
from app.dominio.red import RedCobertura
from app.esquemas import NodoEntrada, RedSalida, TecnicoEntrada, TrayectoEntrada

CARPETA_STATIC = Path(__file__).resolve().parent / "static"

CODIGOS_HTTP = {
    DatoInvalido: 400,
    ElementoNoEncontrado: 404,
    ElementoDuplicado: 409,
}


def crear_app() -> FastAPI:
    app = FastAPI(title="ServicioCerca", description="Red de cobertura de técnicos")
    app.state.red = RedCobertura()  # la red vive en memoria (datos sintéticos)

    # ---------- Manejo de errores legible ----------

    @app.exception_handler(ErrorRed)
    async def manejar_error_red(_: Request, exc: ErrorRed):
        return JSONResponse(status_code=CODIGOS_HTTP.get(type(exc), 400), content={"error": exc.mensaje})

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

    @app.get("/api/red", response_model=RedSalida)
    def consultar_red(red: RedCobertura = Depends(obtener_red)):
        return {
            "nodos": [asdict(n) for n in red.nodos.values()],
            "tecnicos": [asdict(t) for t in red.tecnicos.values()],
            "trayectos": [asdict(t) for t in red.trayectos()],
        }

    @app.post("/api/nodos", status_code=201)
    def registrar_nodo(datos: NodoEntrada, red: RedCobertura = Depends(obtener_red)):
        return asdict(red.agregar_nodo(datos.id, datos.nombre, datos.tipo))

    @app.post("/api/tecnicos", status_code=201)
    def registrar_tecnico(datos: TecnicoEntrada, red: RedCobertura = Depends(obtener_red)):
        return asdict(red.agregar_tecnico(datos.id, datos.nombre, datos.base_id, datos.disponible))

    @app.post("/api/trayectos", status_code=201)
    def registrar_trayecto(datos: TrayectoEntrada, red: RedCobertura = Depends(obtener_red)):
        creados = red.agregar_trayecto(datos.origen, datos.destino, datos.minutos, datos.bidireccional)
        return [asdict(t) for t in creados]

    @app.post("/api/red/ejemplo")
    def cargar_ejemplo(request: Request):
        request.app.state.red = red_de_ejemplo()
        return {"mensaje": "Red de ejemplo cargada."}

    @app.delete("/api/red")
    def vaciar_red(request: Request):
        request.app.state.red = RedCobertura()
        return {"mensaje": "Red vaciada."}

    # ---------- Interfaz mínima ----------

    @app.get("/", include_in_schema=False)
    def inicio():
        return FileResponse(CARPETA_STATIC / "index.html")

    return app


app = crear_app()
