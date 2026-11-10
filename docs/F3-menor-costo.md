# F3 — Alternativa de atención de menor costo

## 1. ¿Qué se pide?
Dado un **origen** y una **zona de servicio**, devolver el **camino de menor tiempo total** (en minutos) y su costo, o decir
con claridad que no existe ruta. La F2 ya responde *si* se puede llegar; la F3 responde *cuál es la mejor forma*.

## 2. ¿Por qué BFS no sirve aquí?
BFS minimiza **tramos**, no **minutos**. En la red de ejemplo:

| Ruta B1 → Z3 (Aranjuez) | Tramos | Minutos |
|--------------------------|--------|---------|
| Directa `B1 -> Z3` (la que elige BFS) | **1** | 15 |
| Por Castilla `B1 -> Z2 -> Z3` | 2 | **13** |

La ruta con menos tramos es 2 minutos **más lenta**. Este es el caso que la API reporta en `comparacion_bfs`.

## 3. ¿Por qué Dijkstra? (la elección sale de las condiciones de los pesos)

| Condición de los pesos | Algoritmo correcto |
|------------------------|--------------------|
| Todos iguales (o sin peso) | BFS |
| **Todos positivos** (nuestro caso) | **Dijkstra** |
| Pueden ser negativos, sin ciclos negativos | Bellman-Ford |
| Ciclo de peso negativo | No existe camino mínimo |

Los trayectos son **tiempos de viaje**: el sistema ya rechaza al registrar cualquier peso que no sea un número finito
**estrictamente mayor que 0** (`validar_peso`). Con pesos positivos, el primer nodo que sale de la cola de prioridad ya
tiene su costo **definitivo**: llegar a él por otro camino solo puede sumar más. Esa es la propiedad que hace correcto a
Dijkstra, y por eso no hace falta pagar el costo extra de Bellman-Ford.

**Tratamiento explícito de pesos inválidos.** Además de validar al registrar, el algoritmo vuelve a validar **cada trayecto
que recorre**. Si alguien alterara el grafo por fuera de la API (peso 0, negativo, NaN, infinito, texto), la consulta se
detiene con `DatoInvalido` y un mensaje que indica el trayecto, en vez de devolver una ruta incorrecta.
La misma validación (`peso_del_trayecto`) se aplica al sumar el costo de la ruta de menos tramos que se usa
para comparar. Dijkstra se detiene al llegar al destino y puede no haber revisado todos esos tramos.

## 4. Cómo funciona (a mano)
Se mantienen dos tablas: `dist` (mejor costo **candidato** conocido para cada nodo) y `padre` (desde quién se llegó con ese costo).

1. `dist[origen] = 0`; todos los demás son infinito (aún no descubiertos).
2. Se saca de la cola el nodo **no definitivo de menor costo**. Queda **definitivo**.
3. **Relajación:** para cada vecino se calcula `candidato = dist[actual] + peso`. Si es **estrictamente menor** que `dist[vecino]`,
   se actualizan `dist[vecino]` y `padre[vecino]`.
4. Se repite hasta sacar el destino (ya es definitivo, se puede parar) o hasta vaciar la cola (no hay ruta).
5. El camino se reconstruye siguiendo `padre` desde el destino hasta el origen y volteando la lista.

La cola es un **montículo (heap)** de `heapq`. Cuando un costo mejora se inserta una entrada nueva y la vieja se descarta al
sacarla (*eliminación perezosa*). Complejidad: **O((V + E) log V)**.

En la traza, la columna **Cola** muestra los **costos candidatos de los nodos aún no definitivos**. No es el
contenido literal del heap, que puede tener entradas viejas que se descartan al sacarlas.

### Traza en papel: B1 → Z3
| Paso | Sale (costo) | Relajaciones (vecino: candidato) | Cola después |
|------|--------------|----------------------------------|--------------|
| 0 | inicio | — | B1:0 |
| 1 | B1 (0) | Z1:4 ✔, Z2:6 ✔, Z3:15 ✔ | Z1:4, Z2:6, Z3:15 |
| 2 | Z1 (4) | B1:8 ✘, Z4:9 ✔ | Z2:6, Z4:9, Z3:15 |
| 3 | Z2 (6) | B1:12 ✘, Z3:**13** ✔ (mejora 15) | Z4:9, Z3:13 |
| 4 | Z4 (9) | Z1:14 ✘, Z5:21 ✔ | Z3:13, Z5:21 |
| 5 | **Z3 (13)** | destino: se detiene | Z5:21 |

Camino: `Z3 ← Z2 ← B1` → **B1 → Z2 → Z3, 13 min, 2 tramos.** (✔ = mejora el costo conocido, ✘ = no lo mejora.)

## 5. Decisiones y casos especiales
- **Origen** puede ser cualquier nodo; el **destino** debe ser una ZONA (igual que la F2).
- Se respeta la **dirección** de los trayectos (`Z4 -> Z5` no se recorre de vuelta).
- **Empates:** los vecinos se recorren en orden alfabético y `padre` solo cambia ante una mejora *estricta*, así que el
  resultado es reproducible.
- Origen = destino: costo 0, camino de un solo nodo.
- Ruta imposible: `alcanzable: false` (código 200, no es un error) con el mismo mensaje de la F2 según sea zona sin conexión
  o red desconectada.
- La **disponibilidad de técnicos** no afecta el costo; sigue informándose aparte en la consulta de alcance.

## 6. Pruebas (`tests/test_costo.py`, `tests/test_api_costo.py`)
Traza igual a la de papel · caso donde menos tramos no es menor costo · rutas de 1 y varios tramos · ruta imposible
(dirección y zona aislada) · origen = destino · nodos inexistentes y destino que es base · pesos inválidos
(0, negativo, NaN, infinito, texto, booleano), también en la ruta de comparación · decimales · empates · **comparación con fuerza bruta** sobre 200 redes
aleatorias · la consulta no modifica la red · API (200, 404, 400).

## 7. Limitaciones
- No admite pesos negativos (no tienen sentido para tiempos de viaje).
- Los pesos son números de punto flotante: se redondea el resultado a 6 decimales.
- Es una consulta punto a punto; elegir automáticamente la mejor base para una zona sería una extensión natural.