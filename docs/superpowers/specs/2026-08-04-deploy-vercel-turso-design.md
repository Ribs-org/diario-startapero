# Copper Valley Diario — Deploy a la nube (Vercel + Turso + GitHub Actions)

**Fecha:** 2026-08-04
**Estado:** Aprobado por el usuario (pendiente revisión del documento escrito)
**Contexto:** v1 corre local (FastAPI + SQLite + scraper agendado en Windows).
Objetivo: todo en la nube, costo US$0/mes, sin depender del PC del usuario.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Alcance | Todo en la nube: scraper Y sitio |
| Presupuesto | Gratis (tiers free de cada servicio) |
| Enfoque | B: Vercel (web) + Turso (BD) + GitHub Actions (scraper) |
| Scraper | Se muda a GitHub Actions con cron diario; se elimina la tarea de Windows |
| BD | Turso (SQLite gestionado, protocolo libsql); local sigue con archivo SQLite |
| API keys | `ANTHROPIC_API_KEY` solo como secret de GitHub Actions; Vercel solo recibe credenciales Turso (la web nunca llama al LLM) |
| Datos existentes | Se migran las noticias del `diario.db` local a Turso (script de un solo uso) |

## Arquitectura

```
GitHub Actions (cron 11:00 UTC ≈ 7-8 AM Chile)     Vercel (free)
┌─────────────────────────────┐                ┌──────────────────────┐
│ python -m scraper.run       │   escribe      │ Sitio FastAPI        │
│ (RSS → Claude → noticias)   │ ──────────►    │ / , /chile, /mundo   │
└─────────────────────────────┘                └──────────┬───────────┘
        secrets: ANTHROPIC_API_KEY,     ┌───────────┐     │ lee
                 TURSO_URL/TOKEN        │ Turso     │ ◄───┘
                                        │ (libsql)  │
                                        └───────────┘
```

- El PC del usuario queda solo como entorno de desarrollo: tests y desarrollo
  local siguen usando el archivo SQLite local, sin red.
- Tier free de Turso (9 GB, ~1B lecturas/mes) y de Vercel (hobby) sobran para
  este tráfico. Actions: ~5-10 min/día de workflow.

## Cambios de código

1. **`db.py`** — la fábrica de conexiones gana una rama: si existen
   `TURSO_DATABASE_URL` y `TURSO_AUTH_TOKEN` en el entorno, conecta a Turso
   con el driver Python `libsql`; si no, SQLite local (comportamiento actual,
   incluida la resolución explícito → `DIARIO_DB_PATH` → default). La API
   pública de `db.py` no cambia: scraper, web y tests quedan intactos.
   *El primer paso de la implementación valida la API exacta del driver
   `libsql` contra una BD Turso real (cursores, row access por nombre,
   IntegrityError) y adapta internamente lo que haga falta sin cambiar la
   interfaz pública.*
2. **`api/index.py`** — entrypoint de Vercel que reexporta `app.main:app`.
3. **`vercel.json`** — runtime Python y ruteo (funciones + `app/static/`).
4. **`.github/workflows/scraper.yml`** — cron `0 11 * * *` (≈7-8 AM Chile
   todo el año), pasos: checkout → setup-python → pip install → 
   `python -m scraper.run`, con los tres secrets.
5. **`scripts/migrar_a_turso.py`** — un solo uso: lee el `diario.db` local y
   sube todas las filas a Turso (respetando dedup por `url_original`).

## Puesta en marcha (guiada, con el usuario)

1. Crear cuenta/BD en Turso (login con GitHub) y obtener URL + auth token.
2. Cargar secrets en el repo GitHub: `ANTHROPIC_API_KEY`,
   `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`.
3. Importar el repo en Vercel (login con GitHub) y setear las dos variables
   de Turso en el proyecto.
4. Ejecutar la migración de datos; disparar el workflow a mano
   (`workflow_dispatch`) una vez; verificar el sitio en la URL de Vercel.
5. Eliminar la tarea programada de Windows `CopperValleyDiario`
   (`schtasks /Delete`).

## Manejo de errores

- Corrida de Actions falla → GitHub notifica por email al dueño del repo; la
  ventana de 2 días del scraper recupera las noticias al día siguiente.
- Turso inaccesible desde Vercel → el sitio responde 500; aceptable para v1.
- El workflow usa los mismos try/except por fuente/artículo ya existentes.

## Testing

- La suite actual (28 tests) queda igual: SQLite local, sin red.
- Nuevos tests solo para la selección de conexión en `db.py` (rama Turso vs
  local) con el driver simulado.
- Validación end-to-end: corrida real del workflow + verificación visual del
  sitio en Vercel (no automatizada).

## Fuera de alcance

- Dominio propio (conectable gratis en Vercel más adelante).
- Fase 2 de contenido: edición semanal, archivo, búsqueda, panel admin,
  newsletter.
