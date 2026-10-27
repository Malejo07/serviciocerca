# F2 — Consulta de cobertura

## 1. ¿Qué significa "cubrir"?

> Una zona **Z está cubierta** desde un origen **O** si **existe un camino dirigido**
> de O a Z en la red de trayectos.

- Es una pregunta de **alcance** (sí / no), **no de costo**. El costo mínimo es la F3.
- Como dato adicional se informa el **número de tramos** del camino encontrado.
  BFS lo da sin trabajo extra, pero **no es el camino más barato**.
- Se respeta la dirección de las aristas: si `Z4 -> Z5` es de un solo sentido,
  desde Z5 **no** se llega a Z4 por ese trayecto.
- La disponibilidad de técnicos **no cambia el alcance**. Se informa aparte
  (`tecnicos_disponibles`) para que el operador sepa si la base puede atender ahora.

## 2. Consultas que ofrece

| Consulta | Entrada | Respuesta |
|----------|---------|-----------|
| **Cobertura de una zona** | `origen` (cualquier nodo) + `zona` (debe ser ZONA) | `cubierta`, `camino`, `tramos`, `mensaje`, `traza` |
| **Alcance de una base** | `base` (debe ser BASE) | zonas alcanzables (con tramos), zonas no alcanzables, técnicos disponibles, `traza` |

### Respuestas ante casos especiales

| Caso | Resultado |
|------|-----------|
| Origen o zona inexistente | Error `ElementoNoEncontrado`: "No existe el nodo 'X'." |
| `zona` es una base, o la `base` de alcance es una zona | Error `DatoInvalido` con mensaje |
| Zona **sin conexión** (no tiene trayectos de llegada) | `cubierta: false`, mensaje: "…no tiene trayectos que lleguen a ella" |
| **Red desconectada** (la zona existe y tiene trayectos, pero no hay camino desde el origen) | `cubierta: false`, mensaje: "…no hay camino desde el origen; la red está desconectada entre ambos" |
| Origen = zona | `cubierta: true`, 0 tramos |

## 3. ¿BFS o DFS? Elegimos **BFS**

| Criterio | BFS (anchura) | DFS (profundidad) |
|----------|---------------|-------------------|
| ¿Responde si hay camino? | Sí, O(V + E) | Sí, O(V + E) |
| Camino que devuelve | El de **menos tramos** | Uno cualquiera (puede dar vueltas) |
| Tramos por zona | Sale gratis (nivel en el que se descubre) | No |
| Implementación | Iterativa con cola, sin riesgo de recursión profunda | Recursiva o con pila |
| Traza | Se explica por niveles: "a 1 tramo, a 2 tramos…" | Más difícil de seguir |

Ambos sirven para el alcance. BFS además entrega el número de tramos y una traza
más fácil de explicar al operador.
**Ojo:** el camino de menos tramos **no** es necesariamente el de menor costo (ver F3).

## 4. Algoritmo

```
BFS(red, origen):
    visitados = {origen}
    cola      = [origen]
    padre     = {origen: None}     # para reconstruir el camino
    tramos    = {origen: 0}
    mientras cola no vacía:
        actual = cola.sacar_primero()
        para cada vecino de actual (en orden alfabético, para que la traza sea reproducible):
            si vecino no está en visitados:
                visitados.agregar(vecino)
                padre[vecino]  = actual
                tramos[vecino] = tramos[actual] + 1
                cola.agregar_al_final(vecino)
```

Para reconstruir el camino se sigue `padre` desde la zona hasta el origen y se invierte la lista.

## 5. Traza en papel (red de ejemplo, BFS desde B1)

Lista de adyacencia de la red de ejemplo:

```
B1 -> Z1, Z2, Z3        Z4 -> Z1, Z5 (Z4->Z5 solo ida)
Z1 -> B1, Z4            Z5 -> B2, Z6   (no vuelve a Z4)
Z2 -> B1, Z3            B2 -> Z5
Z3 -> B1, Z2            Z6 -> Z5
                        Z7 -> (nada, aislada)
```

| Paso | Se saca de la cola | Vecinos | Nuevos (se encolan) | Cola después | Visitados |
|------|--------------------|---------|---------------------|--------------|-----------|
| 0 | — | — | B1 (inicio) | [B1] | {B1} |
| 1 | B1 | Z1, Z2, Z3 | Z1, Z2, Z3 | [Z1, Z2, Z3] | {B1, Z1, Z2, Z3} |
| 2 | Z1 | B1, Z4 | Z4 | [Z2, Z3, Z4] | + Z4 |
| 3 | Z2 | B1, Z3 | — | [Z3, Z4] | igual |
| 4 | Z3 | B1, Z2 | — | [Z4] | igual |
| 5 | Z4 | Z1, Z5 | Z5 | [Z5] | + Z5 |
| 6 | Z5 | B2, Z6 | B2, Z6 | [B2, Z6] | + B2, Z6 |
| 7 | B2 | Z5 | — | [Z6] | igual |
| 8 | Z6 | Z5 | — | [] | fin |

**Resultado desde B1:**
- Zonas alcanzables: Z1, Z2 y Z3 (1 tramo), Z4 (2), Z5 (3), Z6 (4).
- **No alcanzable:** Z7, que está aislada.
- Camino a Z5 (con `padre`): Z5 ← Z4 ← Z1 ← B1, es decir **B1 → Z1 → Z4 → Z5** (3 tramos).
- Camino a Z3: **B1 → Z3** (1 tramo, 15 min). Existe **B1 → Z2 → Z3** (2 tramos, 13 min),
  más barato. BFS no lo elige porque cuenta tramos, no minutos. Por eso hace falta la F3.

**Desde B2** (efecto de la dirección): B2 → Z5 → Z6 y nada más. Como Z4 → Z5 es de solo
ida, desde el sur no se llega al norte.
