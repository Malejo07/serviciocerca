# Mapa de Medellín con geolocalización

## 1. Qué se agrega

Cada nodo (base o zona) puede tener **latitud y longitud**. Si tiene, aparece en su lugar real sobre un mapa de Medellín; si no, solo aparece en el esquema. El mapa tiene dos vistas que se alternan con un botón, sin perder nada de lo anterior:

| Vista | Qué muestra |
|---|---|
| **Esquema** | El grafo animado de siempre, con los nodos distribuidos automáticamente |
| **Mapa** | Los mismos nodos y conexiones sobre el mapa de Medellín (OpenStreetMap), con la ruta del resultado resaltada |

## 2. Reglas de los datos

- La latitud y la longitud son **opcionales**, pero van **juntas**: o se indican las dos o ninguna.
- Latitud entre -90 y 90; longitud entre -180 y 180; números finitos (no se aceptan texto, `NaN` ni infinito).
- Los nodos sin ubicación siguen funcionando en todas las consultas. En el mapa se avisa cuáles no aparecen.
- La red de ejemplo trae ubicaciones **aproximadas** de Bello, Castilla, Aranjuez, Manrique, Robledo, Candelaria, El Poblado, La América y Boston, y de las dos bases.

## 3. API

| Petición | Cambio |
|---|---|
| `POST /api/nodos` | Acepta `latitud` y `longitud` (opcionales). 400 si viene solo una o están fuera de rango |
| `GET /api/red` | Cada nodo devuelve `latitud` y `longitud` (`null` si no tiene) |

## 4. Decisiones

- **Mosaicos de OpenStreetMap, librería Leaflet incluida en el proyecto** (`app/static/vendor/leaflet/`). Solo las imágenes del mapa vienen de internet; todo lo demás funciona sin conexión.
- **Si no hay internet**, los marcadores y las rutas se siguen viendo sobre fondo liso, la pantalla avisa y se puede volver a la vista Esquema.
- El mapa base se oscurece con un filtro para que combine con la consola.
- Al elegir la vista queda recordada en el navegador. Si la red tiene ubicaciones, se abre en «Mapa».
- Los nombres y datos se escriben como texto (nunca como HTML) en marcadores y etiquetas.
- Atribución a OpenStreetMap visible en el mapa, como exige su licencia.

## 5. Qué esperar (y qué no)

- Las conexiones se dibujan como **líneas rectas** entre nodos, no siguen las calles. Seguir calles exigiría un servicio de rutas aparte.
- Los **minutos de cada trayecto son datos registrados**, no se calculan con la distancia del mapa. En el ejemplo son aproximaciones de hora pico, sintéticas: el trayecto directo Base Norte–Aranjuez (20 min) es lento a propósito, porque cruza una zona muy congestionada.
- Las ubicaciones de ejemplo son aproximadas y no oficiales.
- Para uso comercial con mucho tráfico, los mosaicos públicos de OpenStreetMap tienen límites de uso: conviene contratar un proveedor de mapas o alojar los propios.
- El navegador de quien usa la consola consulta a OpenStreetMap para descargar el mapa (recibe su dirección IP y la zona que mira).

## 6. Verificación

- Pruebas automáticas (`tests/test_coordenadas.py`): validación de coordenadas (juntas, rango, números finitos, límites exactos), red de ejemplo ubicada en el valle de Medellín, API y servicio local de Leaflet.
- Verificación en navegador: la vista Mapa se abre sola cuando hay ubicaciones; marcadores, ruta resaltada, zona sin cobertura en rojo, clic en un marcador que rellena el origen, alternancia con el esquema, mapa ampliado, aviso de nodos sin ubicación y aviso cuando no hay internet.
- Capturas en `docs/evidencia/`: `13-mapa-sin-internet.png`, `14-mapa-medellin-ruta.png`, `15-mapa-ampliado.png`.
- **Importante:** el entorno donde se desarrolló no puede descargar mosaicos de OpenStreetMap, así que las capturas 14 y 15 usan un mosaico de relleno para ver la disposición. El aspecto real del mapa base debe comprobarse abriendo la aplicación con internet.

## 7. Siguiente etapa sugerida

- Elegir la ubicación de un nodo haciendo clic en el mapa.
- Calcular o sugerir los minutos a partir de rutas reales por calles.
- Mapa sin internet con los mosaicos alojados en el propio servidor.
