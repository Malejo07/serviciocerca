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
