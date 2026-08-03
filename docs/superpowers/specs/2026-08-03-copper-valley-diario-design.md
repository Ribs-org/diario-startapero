# Copper Valley Diario — Diseño v1

**Fecha:** 2026-08-03
**Estado:** Aprobado por el usuario (pendiente revisión del documento escrito)

## Qué es

Un diario web de noticias de startups y emprendimiento, alimentado por un scraper
automático diario. Marca: **Copper Valley Diario** (logo y paleta en `assets/`).
Dos secciones:

- **Startups Chile**
- **Startups Mundo**

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Formato | Web app con backend |
| Nombre/marca | Copper Valley Diario (100% de la marca; nada de "Diario Startupero") |
| Contenido | Resumen propio (2-3 párrafos, en español) + titular propio + enlace y cita a la fuente original |
| Frecuencia | Scraper corre 1 vez al día |
| Stack | Python: FastAPI + Jinja2 + SQLite, todo en un solo proyecto |
| LLM | API de Anthropic — Claude Haiku para clasificar y resumir |
| Moderación | Publicación automática; campo `estado` permite despublicar a mano |
| Alcance v1 | Lo más simple posible: portada + 2 páginas de sección |

**Fuera de v1 (fase 2):** edición semanal destacada, archivo por fecha, búsqueda,
panel admin, newsletter.

## Arquitectura

Monolito Python:

```
<raíz del repo>          # carpeta local: diario-startapero (solo nombre de directorio)
├── app/                  # Web (FastAPI + Jinja2)
│   ├── main.py           # rutas: / (portada), /chile, /mundo
│   ├── templates/        # base.html, portada, sección, tarjeta de noticia
│   └── static/           # CSS, logo
├── scraper/              # Pipeline diario
│   ├── run.py            # punto de entrada: python -m scraper.run
│   ├── sources.py        # lista de fuentes (RSS)
│   ├── fetch.py          # descarga feeds y artículos
│   ├── classify.py       # Claude: ¿es de startups? ¿chile o mundo?
│   └── summarize.py      # Claude: titular + resumen propios
├── db.py                 # SQLite
└── requirements.txt
```

- La web **solo lee** de SQLite; nunca llama al LLM.
- El scraper es un comando (`python -m scraper.run`) programado una vez al día
  (Programador de tareas de Windows en local; cron del hosting en producción).
- API key de Anthropic en variable de entorno (`ANTHROPIC_API_KEY`), nunca en el código.

## Modelo de datos

Tabla `articles`:

| Campo | Detalle |
|---|---|
| `id` | autoincremental |
| `url_original` | única — sirve de deduplicación |
| `fuente` | nombre del medio de origen |
| `titulo` | titular propio (generado) |
| `resumen` | resumen propio (generado) |
| `seccion` | `chile` \| `mundo` |
| `fecha_publicacion` | fecha del artículo original |
| `fecha_scrapeo` | cuándo lo procesamos |
| `estado` | `published` \| `hidden` (despublicar = UPDATE manual) |

## Fuentes (estrategia: RSS primero)

La validación técnica de cada feed es el **primer paso de la implementación**;
las que fallen se reemplazan por alternativas equivalentes.

**Orientadas a Chile/LATAM:** La Tercera / Pulso, El Mostrador (Mercados),
Contxto, Startupeable, LatamList.

**Orientadas a Mundo:** TechCrunch (Startups), Sifted, Crunchbase News,
The Next Web.

Notas:

- Diario Financiero queda fuera de v1 por paywall duro.
- La sección de una noticia la decide el **clasificador LLM según el contenido**,
  no la fuente (una fuente LATAM puede alimentar ambas secciones).

## Pipeline del scraper (corrida diaria)

1. **Fetch:** lee el RSS de cada fuente (título, enlace, extracto, fecha). Solo
   artículos de los últimos 2 días.
2. **Dedup:** descarta URLs ya presentes en la base.
3. **Filtro + clasificación** (1 llamada Claude Haiku por candidato, con título +
   extracto): ¿es sobre startups/emprendimiento? No → descartar. Sí → `chile` o `mundo`.
4. **Resumen** (1 llamada por aceptado): descarga el artículo, extrae texto
   principal con `trafilatura`, Claude genera titular propio + resumen de 2-3
   párrafos en español citando la fuente.
5. **Guardar** como `published`.

**Manejo de errores:** fuentes y artículos se procesan de forma independiente;
un fallo se loguea y se continúa — la corrida nunca se cae completa. Si el LLM
falla tras reintentos, el artículo se salta (reaparecerá mañana si sigue en el
feed). Costo estimado: ~US$0.05-0.15/día con Haiku (~50-80 candidatos, ~20-30
aceptados).

## Sitio (3 páginas, server-rendered)

- **Portada `/`:** logo + fecha del día + noticias más recientes de ambas
  secciones (las de hoy; si no hay, las últimas disponibles).
- **`/chile` y `/mundo`:** últimas ~30 noticias de la sección.
- **Tarjeta de noticia:** titular, resumen, fuente citada con enlace al
  original, etiqueta de sección.
- **Identidad visual:** paleta de `assets/paleta de colores.txt` — fondo marfil
  `#F4F1ED`, titulares azul marino `#0F1D2D`, apoyo azul pizarra `#334155`,
  secundarios gris acero `#8A9199`, acentos/enlaces cobre `#B87333` y cobre
  claro `#D4A373`. Tipografía serif de diario para titulares. Logo
  `assets/logo.png` en la cabecera. CSS a mano, sin frameworks.

## Testing

`pytest` sobre la lógica, sin depender de la red ni de sitios reales:

- Deduplicación y acceso a datos.
- Parseo de feeds con fixtures RSS guardados.
- Contrato de clasificación/resumen con el LLM simulado (mock).
- Rutas web con `TestClient` de FastAPI.

## Operación

1. Desarrollo y primera operación en local: `uvicorn` + scraper a mano /
   Programador de tareas.
2. Deploy final (tras validar en local): Railway o Render (~US$5-10/mes) con
   cron diario.
