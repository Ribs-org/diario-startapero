# Newsletter: captura de suscriptores

**Fecha:** 2026-08-07
**Estado:** aprobado

## Objetivo

Permitir que un lector deje su nombre y su email, y guardarlos en la base de
datos del diario. No se envía ningún correo: esta etapa solo construye la lista.

## Alcance

Incluye:

- Tabla `suscriptores` en la misma base (Turso en producción, SQLite en tests).
- Botón "Suscribirse" en la navegación, presente en las cinco secciones.
- Modal con el formulario, y página `/suscribirse` con el mismo formulario.
- Endpoint `POST /suscribirse` compartido por ambos.
- Honeypot y validación de entrada.
- Tests de la capa de datos y del endpoint.

No incluye: envío de correos, doble opt-in, baja de suscripción, panel de
administración. Cuando el diario empiece a enviar correos hará falta doble
opt-in y un enlace de baja; eso es un proyecto aparte.

## Datos

Segunda tabla en `db.py`, junto a `articles`:

```sql
CREATE TABLE IF NOT EXISTS suscriptores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    fecha_alta TEXT NOT NULL,
    origen TEXT NOT NULL
)
```

- `email` se normaliza en Python con `.strip().lower()` antes de guardar. La
  restricción `UNIQUE` alcanza entonces para que `Vicente@X.com` y
  `vicente@x.com` sean el mismo suscriptor, sin depender de collations que
  puedan comportarse distinto entre SQLite y Turso.
- `origen` vale `modal` o `pagina`, para saber cuál convierte.
- `fecha_alta` en ISO 8601, como las fechas de `articles`.

`get_connection()` ya ejecuta el esquema en cada conexión. La tabla nueva se
crea ahí mismo, tanto en la rama SQLite como en `_turso_connection()`. El
adaptador Turso ejecuta una sentencia por llamada, así que el esquema vive en
dos constantes (`SCHEMA` y `SCHEMA_SUSCRIPTORES`) y se ejecutan por separado.
No hay migración manual: la tabla aparece en Turso la primera vez que alguien
entre al sitio después del despliegue.

Funciones nuevas:

- `insert_suscriptor(conn, *, nombre, email, fecha_alta, origen)` — usa
  `INSERT OR IGNORE`. Si el email ya existía no falla ni duplica.
- `list_suscriptores(conn)` — devuelve la lista completa, más reciente primero.
  Existe para los tests y para uso futuro; el sitio no la expone.

## Backend

`GET /suscribirse` renderiza `suscribirse.html`.

`POST /suscribirse` recibe un formulario con `nombre`, `email`, `sitio_web`
(honeypot) y `origen`. Valida:

- `nombre`: entre 1 y 80 caracteres una vez recortado.
- `email`: hasta 254 caracteres y con formato razonable (una expresión regular
  simple; validar RFC 5322 completo no aporta nada aquí).
- `origen`: se acepta solo `modal` o `pagina`; cualquier otra cosa se guarda
  como `pagina`.

El honeypot `sitio_web` está oculto por CSS. Un humano no lo ve; un bot que
rellena todos los campos sí. Si llega con contenido, la respuesta es de éxito y
no se guarda nada — el bot no aprende que fue detectado.

Los duplicados también responden éxito. Decirle a quien envía el formulario
"ese correo ya está suscrito" le confirma a cualquiera si una persona
determinada está en la lista.

La forma de la respuesta depende del encabezado `Accept`:

- Si pide JSON (el modal, vía `fetch`): `{"ok": true, "mensaje": "..."}`, o
  `{"ok": false, "mensaje": "..."}` con estado 422 si la validación falla.
- Si no (formulario clásico sin JavaScript): vuelve a renderizar
  `suscribirse.html` con el mensaje correspondiente.

Esto agrega la dependencia `python-multipart`, que es lo que FastAPI necesita
para leer formularios. Va a `requirements.txt`.

## Frontend

En `base.html`, al final de la navegación, un enlace `Suscribirse` destacado en
cobre (clase `nav-suscribirse`).

Es un `<a href="/suscribirse">` real. Si hay JavaScript, un handler intercepta
el clic y abre un `<dialog>` nativo; si no lo hay, el enlace lleva a la página.
Progressive enhancement: sin librerías, sin CDN, sin recursos externos.

El modal y la página comparten el parcial `_form_suscripcion.html`, de modo que
el formulario está definido una sola vez. El parcial recibe `origen` para
distinguir de dónde viene el alta.

El JavaScript son unas veinte líneas al final de `base.html`: abrir el
diálogo, cerrar al hacer clic fuera, enviar por `fetch` y reemplazar el
formulario por el mensaje de respuesta.

Estilos en `style.css`, con la paleta existente: `--cobre` para el botón,
`--marfil` de fondo, borde superior cobre como las tarjetas.

## Tests

`tests/test_suscriptores.py`, contra SQLite local (el `conftest` que ya existe
borra las variables `TURSO_*`):

Capa de datos:
- Alta y recuperación.
- Email duplicado: no duplica ni lanza excepción.
- Normalización: mayúsculas y espacios alrededor del email colapsan al mismo
  registro.

Endpoint, con `TestClient`:
- Alta válida por JSON: responde `ok` y aparece en la base.
- Alta válida por formulario: responde HTML con el mensaje de éxito.
- Honeypot con contenido: responde éxito y **no** guarda nada.
- Email inválido: responde error y no guarda nada.
- Nombre vacío: responde error y no guarda nada.
- Duplicado: responde éxito y sigue habiendo un solo registro.
- `GET /suscribirse` responde 200 y contiene el formulario.

## Lectura de la lista

Por la consola SQL de Turso, igual que para despublicar notas:

```sql
SELECT nombre, email, fecha_alta, origen FROM suscriptores ORDER BY id DESC;
```

Desde ahí se exporta a CSV cuando haga falta. No se agrega ninguna ruta ni
script: son datos personales, y cuanta menos superficie pública tengan, mejor.
