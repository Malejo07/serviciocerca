# F4 — Consola de operación demostrable

## 1. Qué entrega la F4

| Requisito del brief | Dónde se cumple |
|---|---|
| Integrar configuración, cobertura y alternativa de menor costo | La consola (`/consola`) reúne todo en una sola pantalla, con tres pestañas: **Consultar**, **Configurar red** y **Seguimiento**. Las tres usan la misma red y el mismo mapa. |
| Visualización útil de zonas y conexiones, con el resultado destacado | Mapa compacto y ampliable (con vista de esquema o de Medellín, ver `docs/mapa-medellin.md`): la ruta se ilumina en ámbar y las zonas sin cobertura parpadean en rojo. El resultado en texto va primero. |
| Cambio de requisito docente | El docente no estableció ningún cambio; no aplica (ver sección 6). |
| Aceptación de éxito, zona inexistente, red desconectada y peso inválido | Pestaña **Seguimiento** (sección *Verificación del sistema*), `GET /api/aceptacion` y `tests/test_aceptacion.py`. |
| Evidencia completa de la feature | `docs/F4-evidencia.md` (generado por el propio sistema), capturas en `docs/evidencia/` y la suite de pruebas. |

## 2. Qué cambió en la interfaz

- **Landing page (`/`)**: presenta el servicio, qué preguntas resuelve, cómo responde cuando la atención no es posible y lleva a la consola.
- **Consola (`/consola`)**: los resultados van primero y el mapa ocupa una columna lateral compacta. El botón *Ampliar mapa* lo pasa a pantalla completa y `Esc` lo cierra.
- **Resultados legibles**: cada consulta muestra un veredicto con color, ícono y texto; los datos clave en cifras grandes (tramos, minutos); la ruta como una secuencia de paradas con los minutos de cada tramo; el alcance como tabla; la comparación entre menor costo y menos tramos lado a lado; y las bases como un ranking. La traza paso a paso queda plegada.
- **Sin depender de internet**: las tipografías están en `app/static/fonts/` y se sirven desde el propio proyecto.

## 3. Aceptación: los cuatro escenarios

Se ejecutan sobre una **copia de la red de ejemplo**, así que la red que el operador tiene cargada nunca se modifica.

| Escenario | Qué se ejecuta | Resultado esperado | HTTP |
|---|---|---|---|
| **Consulta normal** | Cobertura B1 → Z3 | Cubierta por el camino directo, 1 tramo | 200 |
| | Menor costo B1 → Z3 | B1 → Z2 → Z3 en 15 min; la ruta con menos tramos (B1 → Z3) cuesta 20 | 200 |
| | ¿Qué técnico llega primero a Z5? | Marta, desde B2, en 18 min | 200 |
| **Zona que no existe** | Cobertura B1 → Z99 | Error "No existe el nodo 'Z99'." | 404 |
| | Menor costo B1 → Z99 | El mismo error | 404 |
| **Zona sin conexión** | Cobertura B2 → Z4 | No cubierta; el mensaje explica que la red está desconectada | 200 |
| | Menor costo B2 → Z4 | No alcanzable, con el mismo motivo | 200 |
| | ¿Qué técnico llega primero a Z7? | Z7 no tiene trayectos de llegada; no se puede atender desde ninguna base | 200 |
| **Tiempo inválido** | Registrar B1 → Z7 con -5 min | Rechazado: "debe ser mayor que 0"; la red no cambia | 400 |
| | Registrar B1 → Z7 con 0 min | Rechazado; la red no cambia | 400 |
| | Menor costo con el peso de B1 → Z1 alterado a 0 fuera de la API | El cálculo se detiene y el error nombra el trayecto `B1 -> Z1` | 400 |

Una ruta imposible no es un error del sistema: responde 200 con el motivo. Los errores (404 y 400) quedan para peticiones mal hechas.

## 4. Cómo ejecutarla

- **Desde la consola:** pestaña *Seguimiento* (solo administrador), botón *Ejecutar verificación*. El botón *Descargar informe* guarda el informe en Markdown.
- **Por API:** `GET /api/aceptacion` (resultado en JSON) y `GET /api/aceptacion/evidencia` (informe en Markdown).
- **Desde la terminal:** `python -m app.dominio.aceptacion` imprime el informe.

## 5. Guion de demo (criterio de éxito del cliente)

1. Abrir `/` y mostrar la landing; pulsar *Abrir la consola* e iniciar sesión como `admin` (ver `docs/acceso-por-roles.md`).
2. En *Configurar red*, cargar la red de ejemplo (o registrar nodos y trayectos a mano).
3. En *Consultar*, consultar la cobertura de Aranjuez desde Base Norte.
4. Pulsar *Menor costo* y leer la comparación: 15 min por Castilla (2 tramos) frente a 20 min por el camino directo (1 tramo).
5. Pulsar *¿Qué técnico llega primero?* para Robledo.
6. Consultar una zona inexistente y una zona sin conexión, y leer las respuestas.
7. En *Configurar red*, marcar a Luis como disponible; en *Consultar*, asignar Aranjuez varias veces y ver cómo se reparte entre Ana y Luis (`docs/asignacion-equitativa.md`).
8. En *Seguimiento*, marcar qué rutas se cumplieron, revisar el resumen por técnico, ejecutar la verificación y descargar el informe.

## 6. Cambio de requisito docente

El docente no estableció ningún cambio de requisito para esta entrega, por lo que no hay nada que incorporar. Si más adelante pide uno, el dominio (`app/dominio/`) no depende de la API ni de la interfaz: la regla se cambia en un solo lugar y se verifica con las pruebas y con la aceptación.

## 7. Limitaciones

- La red vive en memoria y se borra al reiniciar el servidor.
- La aceptación usa la red de ejemplo; no valida redes propias del usuario.
- Los datos son sintéticos: no hay ubicación en tiempo real; el cumplimiento de una ruta lo registra el operador.
