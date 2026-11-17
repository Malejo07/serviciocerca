# Asignación equitativa, reportes de visita y seguimiento

La consola ya recomendaba qué técnico llega primero. Ahora también puede **asignar** el servicio y repartir el trabajo entre los técnicos.

## 1. Cómo se asigna

1. Se calcula la ruta más rápida (Dijkstra) desde cada base que tenga técnicos disponibles.
2. Se toma el mejor tiempo posible. Compiten los técnicos que lleguen a **menos de N minutos** de ese tiempo (N = *diferencia máxima de tiempo*, 10 por defecto).
3. Entre ellos gana quien tiene **menos servicios asignados**. Si empatan, el que llega más rápido; si siguen empatando, el código de técnico.

El técnico queda asignado por la ruta de su base y el servicio guarda esa ruta, los minutos y los tramos. Un técnico asignado sigue disponible para recibir más servicios.

**Ejemplo con la red de ejemplo** (Ana y Luis en la Base Norte, a 15 min de Aranjuez):

| Servicio | Técnicos que compiten | Gana | Motivo |
|---|---|---|---|
| S1 | Ana (0 servicios) | Ana | Es la única disponible; Luis no lo está. |
| S2 | Ana (1), Luis (0) | Luis | Luis lleva menos servicios (activado en *Configurar red*). |
| S3 | Ana (1), Luis (1) | Ana | Empatan; el código T1 va primero. |
| S4 | Ana (2), Luis (1) | Luis | Reparte la carga. |

**Tolerancia.** Para Robledo, Marta llega en 18 min desde la Base Sur y Ana en 62 min desde la Base Norte. Con 10 min de tolerancia Ana queda fuera y siempre va Marta; con 50 min de tolerancia, cuando Marta ya lleva más servicios, el sistema puede enviar a Ana para repartir. Con tolerancia 0 gana siempre el más rápido.

## 2. Disponibilidad sin borrar al técnico

En *Configurar red → Técnicos* cada fila tiene el botón **Marcar disponible / no disponible** (`PATCH /api/tecnicos/{id}`). Así no hay que eliminar y volver a crear al técnico, y se conserva su historial de servicios. Los técnicos no disponibles no reciben asignaciones.

## 3. Reporte de visita, novedades y revisión

**Flujo:** el servicio se asigna (*En ruta*) → el técnico reporta la visita (*Por revisar*) → el administrador o el configurador decide (*Cumplida* o *No cumplida*).

- **Técnico** (usuario `tecnico`, ligado a Ana): en **Seguimiento → Mis rutas** ve solo sus servicios. Con **Reportar visita** escribe cómo fue y, si hubo problema, marca *Hubo una novedad* con su tipo (tráfico o vía cerrada, cliente ausente, sin acceso, falla de equipo, otra) y el detalle. Puede corregir el reporte mientras nadie lo haya revisado.
- **Revisor** (administrador o configurador): ve todos los técnicos y rutas, con las que esperan revisión primero. Lee el reporte y la novedad y pulsa **Se cumplió** o **No se cumplió** con una nota opcional. Puede **Reabrir** un servicio para que el técnico corrija.
- El resumen por técnico muestra asignados, por revisar, cumplidos, no cumplidos, novedades y porcentaje de cumplimiento (cumplidos sobre los ya revisados).
- Cada reporte y revisión guarda quién y cuándo.

La pestaña también incluye, solo para el administrador, la **Verificación del sistema** (antes «Aceptación»): cuatro casos que comprueban que el sistema responde bien.

Límites: reporte hasta 1000 caracteres, detalle de la novedad y nota hasta 500. Los textos se muestran siempre como texto, nunca como HTML.

## 4. API

| Petición | Qué hace | Permiso |
|---|---|---|
| `PATCH /api/tecnicos/{id}` `{"disponible": true}` | Cambia la disponibilidad | configurar |
| `POST /api/servicios` `{"zona": "Z3", "tolerancia": 10}` | Asigna y devuelve el técnico, la ruta y los candidatos | configurar |
| `GET /api/servicios` | Resumen y servicios (el técnico solo ve los suyos) | consultar |
| `POST /api/servicios/{id}/reporte` `{"texto": "...", "novedad": {"tipo": "TRAFICO", "detalle": "..."}}` | El técnico reporta la visita; el servicio queda `POR_REVISAR` | reportar (solo servicios propios) |
| `PATCH /api/servicios/{id}` `{"estado": "CUMPLIDO", "nota": "..."}` | El revisor marca `CUMPLIDO`, `NO_CUMPLIDO` o `ASIGNADO` (reabrir) | revisar |
| `DELETE /api/servicios` | Reinicia los servicios | administrar |

Errores: zona inexistente 404; zona que es una base o tolerancia inválida 400; sin técnico disponible que llegue (zona sin conexión o sin técnicos) 409, y no se guarda nada.

## 5. Limitaciones

- Los servicios viven en memoria, igual que la red; cargar otra red los reinicia.
- La equidad cuenta servicios, no minutos de trabajo.
- El cumplimiento lo decide una persona a partir del reporte; no se mide con tiempos reales ni hay adjuntos (fotos).
