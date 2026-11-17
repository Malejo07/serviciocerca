# Acceso por roles e interfaz profesional

## 1. Qué se agrega

Inicio de sesión con tres usuarios de demostración. Los permisos se **validan en la API**: ocultar un botón en la interfaz mejora la experiencia, pero la protección real está en el servidor.

| Usuario | Rol | Qué puede hacer |
|---|---|---|
| `admin` | Administrador | Todo: consultar, configurar la red, revisar reportes, vaciarla y verificar el sistema |
| `configurador` | Configurador de red | Consultar, configurar (nodos, técnicos, trayectos, ejemplo), asignar servicios y revisar los reportes de visita |
| `tecnico` | Técnico | Consultar, ver sus rutas asignadas y reportar sus visitas |

Contraseñas de demostración (solo cuando no se definen las propias, ver sección 5): `Admin2026!`, `Config2026!` y `Tecnico2026!`.

## 2. Matriz de permisos

| Acción | Técnico | Configurador | Administrador |
|---|:-:|:-:|:-:|
| Ver la red y el mapa (`GET /api/red`) | ✔ | ✔ | ✔ |
| Cobertura, menor costo y técnico que llega primero | ✔ | ✔ | ✔ |
| Ver sus rutas asignadas (el técnico solo las suyas) | ✔ | ✔ (todas) | ✔ (todas) |
| Reportar la visita y las novedades de sus rutas | ✔ | ✖ | ✖ |
| Registrar nodos, técnicos y trayectos (`POST`) | ✖ | ✔ | ✔ |
| Cambiar la disponibilidad de un técnico y asignar servicios | ✖ | ✔ | ✔ |
| Revisar los reportes y decidir si se cumplió | ✖ | ✔ | ✔ |
| Cargar la red de ejemplo | ✖ | ✔ | ✔ |
| Vaciar la red (`DELETE /api/red`) y reiniciar servicios | ✖ | ✖ | ✔ |
| Verificación del sistema y descarga del informe | ✖ | ✖ | ✔ |

Cinco permisos nombrados (`consultar`, `reportar`, `configurar`, `revisar`, `administrar`) y cada rol es un conjunto de ellos. Vaciar la red y la verificación quedan solo para el administrador porque son acciones destructivas o de verificación, no de configuración diaria. Reportar es solo del técnico: quien revisa no escribe el reporte que evalúa.

**El usuario técnico está ligado a un técnico de la red** (por defecto `tecnico` = Ana, `T1`; se cambia con `SERVICIOCERCA_TECNICO_ID`). El servidor filtra por ese técnico: no ve las rutas de otros y no puede reportar sobre ellas (403), aunque llame a la API a mano.

## 3. Contrato de la API

| Petición | Respuesta |
|---|---|
| `POST /api/sesion` con `usuario` y `clave` | 200 con usuario, rol y permisos, y cookie de sesión. 401 «Usuario o contraseña incorrectos.» (mismo mensaje si el usuario no existe). 429 tras 5 intentos fallidos |
| `GET /api/sesion` | 200 con la sesión actual; 401 si no hay sesión o expiró |
| `DELETE /api/sesion` | 200 «Sesión cerrada.»; la sesión deja de valer en el servidor |
| Cualquier ruta protegida sin sesión | 401 «Debe iniciar sesión.» |
| Ruta protegida con un rol sin permiso | 403 con el motivo, por ejemplo «El rol Técnico no tiene permiso para configurar la red.» |
| `GET /consola` sin sesión | Redirige a `/acceso` |
| `GET /acceso` y `GET /` | Públicas (inicio de sesión y landing) |

## 4. Decisiones de diseño

- **Sesión en el servidor**: la cookie guarda solo un identificador aleatorio (`secrets.token_urlsafe`). Cerrar sesión la invalida de verdad y no hay datos del usuario en el navegador.
- **Cookie** `HttpOnly` (el JavaScript no la lee) y `SameSite=Strict` (el navegador no la envía desde otros sitios, lo que frena CSRF). Se marca `Secure` cuando se sirve por HTTPS. Dura 8 horas.
- **Contraseñas con hash** `scrypt` y sal propia; se comparan en tiempo constante. Nunca se guardan ni se registran en claro (salvo las de demostración, que son constantes públicas).
- **Sin enumeración de usuarios**: usuario inexistente y clave errónea responden igual y tardan parecido.
- **Bloqueo breve**: 5 intentos fallidos bloquean ese usuario 30 segundos.
- El dominio (`app/dominio/`) no sabe nada de usuarios; la seguridad vive en `app/seguridad.py`.

## 5. Configuración

Variables de entorno opcionales: `SERVICIOCERCA_CLAVE_ADMIN`, `SERVICIOCERCA_CLAVE_CONFIGURADOR`, `SERVICIOCERCA_CLAVE_TECNICO` (y `SERVICIOCERCA_TECNICO_ID`, el técnico de la red al que está ligado ese usuario; por defecto `T1`)`. Si se define cualquiera, se desactiva el modo demostración: la pantalla de acceso deja de mostrar las cuentas de ejemplo.

## 6. Mejoras de experiencia de usuario

Basadas en lo que hoy es habitual en consolas profesionales (paneles de operación, herramientas SaaS):

**Incluidas en esta entrega**
- Pantalla de acceso de dos columnas, con error en línea, mostrar/ocultar contraseña y estado de carga en el botón.
- Menú de usuario con nombre, rol y permisos, y cierre de sesión.
- Interfaz según el rol: cada persona ve solo las pestañas y acciones que puede usar; el tecnico ve un aviso de «modo consulta».
- Confirmación antes de vaciar la red, con foco y teclado (`Esc` cancela).
- Botones con estado de carga («Calculando…») para evitar dobles clics.
- Mensaje claro cuando la sesión expira, en lugar de errores sueltos.

**Recomendadas para una siguiente etapa**
- Tema claro y oscuro, con respeto a la preferencia del sistema.
- Búsqueda rápida de nodos y atajos de teclado.
- Historial de consultas recientes y exportar el resultado (PDF o CSV).
- Registro de auditoría: quién cambió qué y cuándo.
- Gestión de usuarios y cambio de contraseña desde la interfaz.
- Persistencia de la red en base de datos y acceso con proveedor externo (SSO).

## 7. Verificación

- Pruebas automáticas (`tests/test_seguridad.py`): inicio y cierre de sesión, expiración, bloqueo, cookie, hash de claves, y la **matriz completa de permisos** (3 usuarios × 12 rutas, más el caso sin sesión).
- Verificación en navegador con los tres usuarios: pestañas y botones visibles por rol, y confirmación de que las peticiones directas a la API sin permiso responden 403.
- Capturas en `docs/evidencia/`: `07-acceso.png`, `08-acceso-error.png`, `09-admin-menu.png`, `10-confirmar-vaciar.png`, `11-configurador.png`, `12-tecnico.png`.

## 8. Limitaciones

- Las sesiones y la red viven en memoria: se pierden al reiniciar el servidor y no sirven con varios procesos.
- Los usuarios son fijos; no hay alta, baja ni cambio de contraseña desde la aplicación.
- El bloqueo por usuario puede usarse para molestar a una cuenta durante 30 segundos; es un compromiso aceptado en una demostración.
