# Brief de cliente — ServicioCerca

## Cliente y problema

ServicioCerca coordina técnicos para mantenimiento de equipos en barrios de una ciudad. Cuando entra una solicitud, necesita saber qué zonas pueden atenderse desde una base y cuál técnico podría llegar con menor costo estimado. Hoy esa decisión depende de llamadas y conocimiento informal.

## Usuarios

- **Coordinador de operaciones:** registra bases, técnicos, zonas y conexiones.
- **Operador de atención:** consulta cobertura y alternativa de atención.

## Alcance

Datos sintéticos: bases/técnicos, zonas y trayectos con tiempo o distancia positiva. No incluye ubicación en tiempo real, geolocalización, turnos complejos, pagos ni asignación automática multi-técnico.

## Feature 1 — Red de cobertura

### Valor de negocio
El coordinador configura zonas y conexiones operativas asociadas a bases/técnicos.

### Debe permitir

- registrar entidades y conexiones con datos válidos;
- especificar qué representa cada nodo y arista;
- validar identificadores, duplicados y pesos positivos;
- consultar la red por API e interfaz mínima;
- justificar si una conexión puede o no recorrerse en ambos sentidos.

### Pistas, no receta

No mezclen “técnico” y “zona” sin explicar qué pregunta resolverá el grafo. Pueden modelar disponibilidad como atributo o como relación; comparen implicaciones antes de elegir.

## Feature 2 — Consulta de cobertura

### Valor de negocio
El operador sabe si una solicitud está dentro de una cobertura posible y qué zonas pueden alcanzarse desde una base.

### Debe permitir

- recibir origen y zona solicitada, o una base para listar alcance;
- usar BFS o DFS implementado por el equipo y justificarlo;
- retornar resultado legible ante red desconectada, origen inexistente o zona sin conexión;
- incluir una traza de un ejemplo pequeño.

### Pistas, no receta

Primero definan qué significa “cubrir”: ¿existencia de camino, número de pasos o costo? Esta feature trata principalmente de alcance, no de optimización.

## Feature 3 — Alternativa de atención de menor costo

### Valor de negocio
El operador consulta una ruta o alternativa de llegada con menor tiempo/distancia estimada.

### Debe permitir

- recibir origen y destino de servicio;
- devolver camino y costo total cuando exista;
- rechazar o tratar de forma explícita pesos que invaliden el algoritmo elegido;
- explicar un caso donde la menor cantidad de tramos no es el menor costo;
- probar casos de ruta posible e imposible.

### Pistas, no receta

Investiguen cómo mantener costos candidatos y cómo reconstruir el camino final. La elección debe estar respaldada por las condiciones de los pesos, no por popularidad del algoritmo.

## Feature 4 — Consola de operación demostrable

### Valor de negocio
El equipo de atención consulta cobertura y alternativa de servicio sin interpretar estructuras internas.

### Debe permitir

- integrar configuración, cobertura y alternativa de menor costo;
- mostrar una visualización útil de zonas/conexiones y destacar resultado;
- incorporar el cambio de requisito docente;
- ejecutar aceptación de éxito, zona inexistente, red desconectada y peso inválido;
- entregar evidencia completa de feature.

## Criterio de éxito del cliente

En una demo, el operador registra la red, consulta una zona, recibe una alternativa entendible y observa respuestas consistentes cuando la atención no es posible.
