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
