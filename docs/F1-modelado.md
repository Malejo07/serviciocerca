# F1 — Decisiones de modelado de la red de cobertura

## 1. ¿Qué pregunta resuelve el grafo?

> "Desde una base, ¿a qué zonas se puede llegar y con qué costo?"

Todo el modelo se diseña para responder esa pregunta (F2: alcance, F3: costo mínimo).

## 2. Nodos

Un **nodo es una ubicación física** de la ciudad. Hay dos tipos:

| Tipo   | Significado                                         |
|--------|-----------------------------------------------------|
| `BASE` | Punto desde donde salen los técnicos.               |
| `ZONA` | Barrio que puede solicitar mantenimiento.           |

Las bases y las zonas comparten el mismo espacio de identificadores, porque ambas
son lugares por donde se puede pasar. Una base puede ser punto intermedio de un trayecto.

## 3. Aristas

Una **arista es un trayecto operativo** entre dos ubicaciones. Su peso es el
**tiempo estimado en minutos** (siempre > 0).

Se eligió una sola unidad (minutos) para que los costos se puedan sumar sin
mezclar tiempo con distancia.

## 4. ¿Una conexión se recorre en ambos sentidos?

El grafo se guarda **dirigido** (lista de adyacencia `origen -> {destino: minutos}`).
Al registrar un trayecto, el coordinador indica `bidireccional`:

- `bidireccional = true` (por defecto): calle de doble vía con el mismo tiempo en
  ambos sentidos. Se crean las dos aristas `A -> B` y `B -> A`.
- `bidireccional = false`: vía de un solo sentido, o tiempos distintos en cada
  sentido (por ejemplo, subida y bajada). Se crea solo `A -> B`. Si se quiere el
  regreso con otro tiempo, se registra `B -> A` aparte.

**Justificación:** un grafo dirigido puede representar los dos casos. Uno no
dirigido no puede representar vías de un solo sentido. Así cada conexión deja
explícito si se puede recorrer al revés.

## 5. Técnicos: ¿atributo o relación?

| Opción | Ventaja | Desventaja |
|--------|---------|------------|
| **Atributo**: el técnico pertenece a una base y tiene `disponible: bool` | El grafo sigue siendo solo de lugares; BFS y Dijkstra no cambian. La disponibilidad solo filtra qué bases pueden ser origen. | No modela técnicos que se mueven entre bases. Están fuera de alcance. |
| **Relación**: arista técnico -> zona | Expresa directamente "quién atiende dónde". | Mezcla "puede atender" con "trayecto físico". Un recorrido podría "pasar por un técnico" como si fuera un lugar, y habría que tipar y filtrar aristas en cada algoritmo. |

**Decisión: atributo.** El técnico **no es un nodo**. Así no se mezclan técnico y zona en el grafo.

## 6. Validaciones

| Regla | Error |
|-------|-------|
| Identificador vacío o con caracteres no permitidos (solo letras, números, `-`, `_`, máx. 30) | `DatoInvalido` |
| Identificadores sin distinguir mayúsculas (`z1` = `Z1`, se normalizan a mayúsculas) | — |
| Nodo o técnico con ID ya existente | `ElementoDuplicado` |
| Tipo de nodo distinto de `BASE`/`ZONA` | `DatoInvalido` |
| Técnico asignado a una base que no existe o a una zona | `ElementoNoEncontrado` / `DatoInvalido` |
| Trayecto con origen o destino inexistente | `ElementoNoEncontrado` |
| Trayecto de un nodo a sí mismo | `DatoInvalido` |
| Trayecto repetido (misma dirección ya registrada) | `ElementoDuplicado` |
| Peso no numérico, ≤ 0, infinito o NaN | `DatoInvalido` |

Las validaciones están en el **dominio** (`app/dominio/red.py`), no solo en la API.
Así se cumplen sin importar desde dónde se use la red: API, pruebas o algoritmos.

## 7. Red de ejemplo (`app/datos/red_ejemplo.json`)

Once nodos (2 bases y 9 zonas de Medellín y Bello) y ocho trayectos adicionales entre ellos. Los tiempos son
**aproximados, de hora pico, y sintéticos**; las ubicaciones también son aproximadas.

```
 Z1 Bello ──14── B1 Base Norte ──7── Z2 Castilla ──8── Z3 Aranjuez
  │20                  └──────────── 20 (directo) ──────────┘
 Z4 Manrique
  │ 28 (solo ida)
  ▼
 Z5 Robledo ──18── B2 Base Sur
  │  \               │
  17   12             14
  │      \            │
 Z6 Candelaria       Z8 La América     (Z5 ──12── Z8, B2 ──14── Z8)
  │7
 Z9 Boston

 Z7 Poblado: aislada, sin trayectos
```

| Trayecto | Minutos | Sentido |
|---|---|---|
| Base Norte ↔ Bello | 14 | Ambos |
| Base Norte ↔ Castilla | 7 | Ambos |
| Base Norte ↔ Aranjuez (directo) | 20 | Ambos |
| Castilla ↔ Aranjuez | 8 | Ambos |
| Bello ↔ Manrique | 20 | Ambos |
| Manrique → Robledo | 28 | **Solo ida** |
| Base Sur ↔ Robledo | 18 | Ambos |
| Robledo ↔ Candelaria | 17 | Ambos |
| Robledo ↔ La América | 12 | Ambos |
| Base Sur ↔ La América | 14 | Ambos |
| Candelaria ↔ Boston | 7 | Ambos |

- **Técnicos (4):** Ana (B1, disponible), Luis (B1, no disponible), Marta (B2, disponible), Carlos (B2, no disponible).
- `Z4 -> Z5` es de **un solo sentido**: desde B1 se llega a Z5, Z6, Z8 y Z9, pero desde B2 no se llega al norte (B1 y Z1 a Z4).
- `Z7` está **aislada**. Sirve para probar "zona sin conexión" en F2.
- **Menos tramos no es menos tiempo:** `B1 -> Z3` directo cuesta 20 (1 tramo), porque cruza una zona muy congestionada,
  pero `B1 -> Z2 -> Z3` cuesta 15 (7 + 8, 2 tramos). Es el caso de F3.

## 8. Cumplimiento de F1

| Requisito del brief | Dónde se cumple |
|---------------------|-----------------|
| Registrar entidades y conexiones válidas | `RedCobertura.agregar_nodo/agregar_tecnico/agregar_trayecto`, `POST /api/nodos`, `/api/tecnicos`, `/api/trayectos` |
| Especificar qué representa nodo y arista | Secciones 2, 3 y 5 de este documento |
| Validar identificadores, duplicados y pesos positivos | `app/dominio/red.py` + `tests/test_red.py` |
| Consultar la red por API e interfaz mínima | `GET /api/red`, página `/`, documentación automática en `/docs` |
| Justificar si una conexión se recorre en ambos sentidos | Sección 4 + campo `bidireccional` |

Pruebas: `pytest -v` ejecuta 41 pruebas (dominio y API).
