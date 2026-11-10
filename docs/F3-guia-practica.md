# F3 — Guía práctica: cómo funciona el menor costo y cómo practicarlo

Esta guía explica la F3 paso a paso y propone ejercicios para hacer en la interfaz.
La justificación técnica completa está en `docs/F3-menor-costo.md`.

---

## 1. ¿Qué problema resuelve la F3?

La F2 responde **"¿se puede llegar?"**. La F3 responde **"¿cuál es la forma más rápida de llegar?"**.

Ofrece dos consultas:

| Botón en la interfaz | Pregunta del operador | Entrada | Respuesta |
|----------------------|------------------------|---------|-----------|
| **Menor costo** | "Desde esta base, ¿cuál es la ruta más rápida a esta zona?" | origen + zona | camino, minutos, tramos y comparación con la ruta de menos tramos |
| **¿Qué técnico llega primero?** | "Entró una solicitud en esta zona, ¿a quién envío?" | solo la zona | la base y los técnicos disponibles que llegan antes, más la comparación de todas las bases |

---

## 2. La idea clave: menos tramos ≠ menos minutos

En la red de ejemplo, para ir de **B1 (Base Norte)** a **Z3 (Aranjuez)**:

```
          15 min (directo)
   B1 ───────────────────── Z3
    │                       │
  6 min                   7 min
    │                       │
    └──────── Z2 ───────────┘
            Castilla
```

| Ruta | Tramos | Minutos | ¿Quién la elige? |
|------|--------|---------|------------------|
| B1 → Z3 | **1** | 15 | BFS (F2), que cuenta tramos |
| B1 → Z2 → Z3 | 2 | **13** | Dijkstra (F3), que suma minutos |

BFS (F2) es como contar **cuántas calles** se recorren. Dijkstra (F3) es como mirar **cuánto se demora** cada calle.

---

## 3. Dijkstra explicado con palabras simples

Dijkstra es como **una mancha de agua que avanza más rápido por las calles cortas**:
siempre "inunda" primero el lugar al que se llega en **menos minutos**.

Usa tres cosas:

| Concepto | Qué es | En el código |
|----------|--------|--------------|
| **Costo candidato** | El mejor tiempo conocido *hasta ahora* para llegar a un nodo. Puede mejorar. | `dist` |
| **Definitivo** | Un nodo cuyo tiempo ya no puede mejorar. | `definitivos` |
| **Padre** | Desde qué nodo se llegó con ese tiempo, para reconstruir la ruta. | `padre` |

### El algoritmo en 4 pasos
1. El origen cuesta **0**. Los demás, "infinito" (todavía no se conocen).
2. Se saca el nodo **pendiente con menor costo** y se marca **definitivo**.
3. **Relajación:** para cada vecino se calcula `candidato = costo actual + minutos del trayecto`.
   Si el candidato es **menor** que lo que ya se conocía, se actualiza (✔). Si no, se ignora (✘).
4. Se repite hasta que el destino sea definitivo (ya se tiene la respuesta) o se acaben los pendientes (no hay ruta).

Para sacar siempre el de menor costo se usa un **montículo** (`heapq`), una estructura que entrega
el mínimo de forma eficiente.

### ¿Por qué un nodo definitivo ya no puede mejorar?
Porque **todos los tiempos son positivos**. Si Z2 sale con 6 minutos y es el menor pendiente,
cualquier otro camino a Z2 pasaría por un nodo que ya cuesta 6 o más, y luego **sumaría** minutos.
No puede quedar por debajo de 6.

**¿Qué pasaría con pesos negativos?** Dijkstra fallaría. Ejemplo: A→B = 2, A→C = 5, C→B = −4.
Dijkstra marca B como definitivo con 2, pero el camino real A→C→B cuesta 1.
Por eso el sistema **rechaza pesos ≤ 0** dos veces: al registrar el trayecto (F1) y al calcular (F3).

---

## 4. Traza paso a paso: B1 → Z3

Es la misma tabla que muestra la interfaz en *"Ver paso a paso del cálculo (Dijkstra)"*:

| Paso | Sale (costo) | Costos candidatos | Pendientes | Qué pasó |
|------|--------------|-------------------|------------|----------|
| 0 | inicio | — | B1:0 | B1 empieza con costo 0. |
| 1 | B1 (0) | Z1:4 ✔, Z2:6 ✔, Z3:15 ✔ | Z1:4, Z2:6, Z3:15 | Se descubren los vecinos de B1. Z3 aparece con 15 por el camino directo. |
| 2 | Z1 (4) | B1:8 ✘, Z4:9 ✔ | Z2:6, Z4:9, Z3:15 | Volver a B1 costaría 8, peor que 0 (✘). Se descubre Manrique con 9. |
| 3 | Z2 (6) | B1:12 ✘, **Z3:13 ✔** | Z4:9, Z3:13 | **Momento clave:** por Castilla, Z3 cuesta 13, mejor que 15. Su padre pasa a ser Z2. |
| 4 | Z4 (9) | Z1:14 ✘, Z5:21 ✔ | Z3:13, Z5:21 | Se descubre Robledo con 21. |
| 5 | **Z3 (13)** | — | Z5:21 | Z3 es el menor pendiente: queda definitivo con 13 y **el algoritmo se detiene**. |

**Reconstrucción:** padre de Z3 = Z2, padre de Z2 = B1. Al revés: **B1 → Z2 → Z3, 13 min.**

La columna *Pendientes* muestra los costos candidatos de los nodos que todavía no son definitivos.

---

## 5. La mejora: "¿Qué técnico llega primero?"

El cliente necesita saber **qué técnico podría llegar con menor costo**. Para eso:

1. Se toma cada **base** de la red.
2. Se ejecuta **Dijkstra** desde esa base hasta la zona.
3. Solo compiten las bases que **llegan** y tienen **técnicos disponibles**.
4. Gana la de **menor costo**. Si hay empate, gana la de ID menor (B1 antes que B2), para que el resultado sea siempre el mismo.

Si la base más cercana **no tiene técnicos disponibles**, el sistema lo explica, para que el operador sepa
por qué no se eligió la más cercana.

> No es asignación automática (eso está fuera de alcance): es una **recomendación** para el operador.

**Complejidad:** una ejecución de Dijkstra por base, es decir, `B × O((V + E) log V)`.
Con pocas bases es muy rápido.

---

## 6. Ejercicios para practicar en la interfaz

**Preparación:**
```
.venv\Scripts\activate
uvicorn app.main:app --reload
```
Abra http://127.0.0.1:8000 y presione **Cargar red de ejemplo**.
Puede escribir los IDs a mano o hacer **clic en el mapa**: una base llena "Origen" y una zona llena "Zona".

### Bloque A: Menor costo

| # | Origen | Zona | Botón | Resultado esperado | Qué aprende |
|---|--------|------|-------|--------------------|-------------|
| A1 | B1 | Z3 | Menor costo | 🟢 **13 min** por B1 → Z2 → Z3 (2 tramos). Aviso: la ruta de menos tramos (B1 → Z3) cuesta 15 min, **2 min más**. | Menos tramos ≠ menor costo. |
| A2 | B1 | Z3 | Consultar cobertura | 🟢 B1 → Z3 en **1 tramo** | Compare con A1: BFS elige otra ruta. |
| A3 | B1 | Z1 | Menor costo | 🟢 **4 min** por B1 → Z1. Sin aviso. | Cuando ambas rutas coinciden, no hay advertencia. |
| A4 | B1 | Z5 | Menor costo | 🟢 **21 min** por B1 → Z1 → Z4 → Z5 (3 tramos) | Ruta de varios tramos. |
| A5 | B2 | Z6 | Menor costo | 🟢 **9 min** por B2 → Z5 → Z6 | Desde la otra base. |
| A6 | B2 | Z4 | Menor costo | 🔴 "no es alcanzable… red desconectada" | Z4 → Z5 es de solo ida: la dirección importa. |
| A7 | B1 | Z7 | Menor costo | 🔴 "no tiene trayectos que lleguen a ella" | Zona aislada. |
| A8 | B99 | Z1 | Menor costo | 🔴 "No existe el nodo 'B99'" | Origen inexistente. |
| A9 | (vacío) | Z3 | Menor costo | 🔴 "Indique el origen y la zona…" | Menor costo necesita los dos datos. |

En A1, abra **"Ver paso a paso del cálculo (Dijkstra)"** y compare con la tabla de la sección 4.

### Bloque B: ¿Qué técnico llega primero?

Solo escriba la **zona**. El origen se llena solo con la base ganadora.

| # | Zona | Resultado esperado | Qué aprende |
|---|------|--------------------|-------------|
| B1 | Z5 | 🟢 **Marta desde B2, 5 min**. Comparación: B2 · 5 min · Marta / B1 · 21 min · Ana | Gana la base más rápida, no la primera de la lista. |
| B2 | Z3 | 🟢 **Ana desde B1, 13 min** por B1 → Z2 → Z3. Comparación: B2 · no llega | Usa el menor costo; B2 no llega por la dirección. |
| B3 | Z6 | 🟢 **Marta desde B2, 9 min** (B1 tardaría 25) | — |
| B4 | Z1 | 🟢 **Ana desde B1, 4 min**. Luis no aparece. | Luis está en B1 pero **no disponible**. |
| B5 | Z7 | 🔴 "no tiene trayectos…" y ninguna base llega | Zona aislada. |
| B6 | B1 | 🔴 "'B1' es una base; la zona solicitada debe ser una ZONA" | El destino debe ser una zona. |

### Bloque C: Modificar la red y ver cómo cambia la respuesta

Use el panel **Administrar la red** (abajo).

**C1. Una base cercana sin técnicos**
1. Registre el nodo `B3`, "Base Centro", tipo **Base**.
2. Registre el técnico `T4`, "Pedro", base `B3`, con **Disponible desmarcado**.
3. Registre el trayecto `B3` → `Z3`, `2` minutos, ambos sentidos.
4. Zona `Z3` → **¿Qué técnico llega primero?**

Resultado esperado: 🟢 **Ana desde B1, 13 min**, con el aviso *"B3 llega en 2 min, pero no tiene técnicos disponibles"*.
En la comparación, **B3 · 2 min · sin técnicos disponibles** aparece en rojo.

**C2. Ahora sí hay técnico**
5. Registre el técnico `T5`, "Sofía", base `B3`, **Disponible marcado**.
6. Repita la consulta para `Z3`.

Resultado esperado: 🟢 **Sofía desde B3, 2 min**.

**C3. Crear un atajo** (antes, presione *Cargar red de ejemplo* para volver a la red original)
1. Registre el trayecto `Z1` → `Z3`, `1` minuto, ambos sentidos.
2. Origen `B1`, zona `Z3` → **Menor costo**.

Resultado esperado: 🟢 **5 min** por B1 → Z1 → Z3, y la ruta directa de 15 min cuesta **10 min más**.
Lo que se aprende: cambiar un solo trayecto puede cambiar toda la ruta óptima.

**C4. Intentar un peso inválido**
1. Registre un trayecto `B1` → `Z4` con `0` minutos, y luego con `-3`.

Resultado esperado: 🔴 *"El tiempo del trayecto debe ser mayor que 0"*. Esta es la **primera defensa** (F1).
La segunda defensa está dentro de Dijkstra y se prueba en `tests/test_costo.py`, alterando el grafo por fuera de la API.

---

## 7. Ejercicio en papel (para practicar la traza)

Red dirigida: `S→A = 1`, `S→B = 4`, `A→B = 2`, `A→C = 6`, `B→C = 3`. Calcule el menor costo de **S a C**.

```
      1        6
  S ────► A ────────► C
  │       │           ▲
 4│      2│           │3
  └─────► B ──────────┘
```

<details>
<summary>Ver solución</summary>

| Paso | Sale (costo) | Costos candidatos | Pendientes |
|------|--------------|-------------------|------------|
| 0 | inicio | — | S:0 |
| 1 | S (0) | A:1 ✔, B:4 ✔ | A:1, B:4 |
| 2 | A (1) | B:3 ✔ (mejora 4), C:7 ✔ | B:3, C:7 |
| 3 | B (3) | C:6 ✔ (mejora 7) | C:6 |
| 4 | C (6) | — | — |

**Respuesta:** S → A → B → C, **6 min** (3 tramos). BFS elegiría S → A → C (2 tramos), que cuesta **7 min**.

Puede comprobarlo en la interfaz: *Vaciar red*, registre `S` como base y `A`, `B`, `C` como zonas,
los 5 trayectos **sin** "ambos sentidos", y consulte **Menor costo** de `S` a `C`.
</details>

---

## 8. Preguntas frecuentes

| Pregunta | Respuesta |
|----------|-----------|
| ¿Por qué Dijkstra y no BFS? | BFS minimiza tramos. Aquí los trayectos tienen tiempos distintos y se quiere minimizar minutos. |
| ¿Por qué no Bellman-Ford? | Bellman-Ford sirve con pesos negativos, pero es más lento: O(V·E). Nuestros pesos son tiempos, siempre positivos. |
| ¿Qué es "relajar"? | Revisar si llegar a un vecino pasando por el nodo actual es más barato que lo conocido. Si lo es, se actualiza. |
| ¿Por qué se detiene antes de visitar todo? | Cuando el destino sale de la cola ya es definitivo: su costo no puede mejorar. |
| ¿Qué es la "eliminación perezosa"? | Cuando un costo mejora se mete una entrada nueva en el montículo. La vieja no se borra; se ignora cuando sale. |
| ¿Qué pasa si hay empate? | Los vecinos se recorren en orden alfabético y el padre solo cambia si la mejora es estricta, así que el resultado es siempre el mismo. |
| ¿La disponibilidad cambia la ruta? | No cambia el costo de una ruta. Solo decide qué bases compiten en "¿Qué técnico llega primero?". |
| ¿Cómo sabemos que Dijkstra está bien? | Hay una prueba que lo compara contra fuerza bruta (probar todos los caminos) en 200 redes aleatorias. |
