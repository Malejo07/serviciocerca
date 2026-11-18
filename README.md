# ServicioCerca

Proyecto académico: red de cobertura de técnicos modelada como grafo.

## Requisitos
- Python 3.12+

## Instalación
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Ejecutar
```bash
uvicorn app.main:app --reload
```
- Interfaz: http://127.0.0.1:8000
- Documentación de la API: http://127.0.0.1:8000/docs

## Pruebas
```bash
pytest -v
```

## Funcionalidades
- **F1** Red de bases, zonas, técnicos y trayectos (`docs/F1-modelado.md`).
- **F2** Cobertura con BFS: `GET /api/cobertura`, `GET /api/cobertura/alcance/{base}` (`docs/F2-cobertura.md`).
- **F3** Menor costo con Dijkstra: `GET /api/menor-costo?origen=B1&zona=Z3` y
  qué técnico llega primero: `GET /api/menor-costo/mejor-base?zona=Z5`
  (`docs/F3-menor-costo.md`, guía práctica en `docs/F3-guia-practica.md`).
- **F4** Consola de operación demostrable: landing en `/`, consola en `/consola` (consultas, configuración y
  aceptación), `GET /api/aceptacion` y `GET /api/aceptacion/evidencia`. Las tipografías van incluidas en
  `app/static/fonts/` (funciona sin internet). Ver `docs/F4-consola.md` y `docs/F4-evidencia.md`.
- **Asignación equitativa**: `POST /api/servicios` asigna la zona al técnico con menos servicios entre los que
  llegan casi igual de rápido; `PATCH /api/tecnicos/{id}` cambia la disponibilidad sin borrar al técnico; la pestaña
  *Seguimiento* muestra rutas asignadas y cumplimiento (`docs/asignacion-equitativa.md`). El perfil **técnico** ve
  solo sus rutas y reporta cada visita y sus novedades; el administrador o el configurador revisan y deciden si se cumplió.
- **Mapa de Medellín**: los nodos pueden tener latitud y longitud y verse sobre un mapa real (OpenStreetMap),
  con alternancia a la vista Esquema (`docs/mapa-medellin.md`). Solo las imágenes del mapa necesitan internet.
- **Acceso por roles**: pantalla `/acceso` y tres usuarios de demostración. Los permisos se validan en la API
  (`docs/acceso-por-roles.md`).

| Usuario | Contraseña (demo) | Rol |
|---|---|---|
| `admin` | `Admin2026!` | Administrador: todo |
| `configurador` | `Config2026!` | Consulta y configura la red |
| `tecnico` | `Tecnico2026!` | Técnico (ligado a Ana, T1): ve sus rutas y reporta sus visitas |

Para usar claves propias (y ocultar las cuentas de demostración) defina `SERVICIOCERCA_CLAVE_ADMIN`,
`SERVICIOCERCA_CLAVE_CONFIGURADOR` y `SERVICIOCERCA_CLAVE_TECNICO` (y `SERVICIOCERCA_TECNICO_ID`, el técnico de la red al que está ligado ese usuario; por defecto `T1`)` antes de iniciar el servidor.
