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

```
        4          5             12 (solo ida)
  B1 ------- Z1 ------- Z4 ---------------> Z5 ------- B2
  | \                                       |    5
 6|  \ 15                                  4|
  |   \                                     |
  Z2 --- Z3                                 Z6
     7
                    Z7 (aislada, sin trayectos)
```

- **Técnicos:** Ana (B1, disponible), Luis (B1, no disponible), Marta (B2, disponible).
- `Z4 -> Z5` es de **un solo sentido**: desde B1 se llega a Z5 y Z6, pero desde B2 no se llega a B1.
- `Z7` está **aislada**. Servirá para probar "zona sin conexión" en F2.
- `B1 -> Z3` directo cuesta 15 (1 tramo), pero `B1 -> Z2 -> Z3` cuesta 13 (2 tramos).
  Servirá para el caso de F3 donde menos tramos no es lo mismo que menor costo.

## 8. Cumplimiento de F1

| Requisito del brief | Dónde se cumple |
|---------------------|-----------------|
| Registrar entidades y conexiones válidas | `RedCobertura.agregar_nodo/agregar_tecnico/agregar_trayecto`, `POST /api/nodos`, `/api/tecnicos`, `/api/trayectos` |
| Especificar qué representa nodo y arista | Secciones 2, 3 y 5 de este documento |
| Validar identificadores, duplicados y pesos positivos | `app/dominio/red.py` + `tests/test_red.py` |
| Consultar la red por API e interfaz mínima | `GET /api/red`, página `/`, documentación automática en `/docs` |
| Justificar si una conexión se recorre en ambos sentidos | Sección 4 + campo `bidireccional` |

Pruebas: `pytest -v` ejecuta 41 pruebas (dominio y API).
