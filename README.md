# Copper Valley Diario

Diario web de noticias de startups y emprendimiento, con dos secciones de
noticias — **Startups Chile** y **Startups Mundo** — y dos directorios:
**Financiamiento** y **Comunidades**. Un scraper diario lee fuentes RSS, filtra
y clasifica cada noticia con Claude y publica un titular y resumen propios que
citan y enlazan la fuente original.

Los dos directorios son estáticos: no pasan por el scraper ni por la base de
datos. Los listados viven en `app/financiamiento.py` y `app/comunidades.py`,
sus logos en `app/static/logos/` y la ficha que comparten en
`app/templates/_ficha.html`.

El botón **Suscribirse** de la navegación abre un modal con el formulario del
newsletter, y la página `/suscribirse` muestra el mismo formulario para
compartir por enlace. Ambos guardan nombre y correo en la tabla
`suscriptores`. Por ahora solo se junta la lista: el diario no envía correos.

## Producción

- **Sitio:** https://diario-startapero.vercel.app (Vercel, lee Turso)
- **Scraper:** GitHub Actions, diario a las 11:00 UTC (`.github/workflows/scraper.yml`);
  corrida manual: pestaña Actions → "Scraper diario" → Run workflow.
- **Base de datos:** Turso (`copper-valley-news`). Credenciales: secrets del
  repo (Actions) y environment variables (Vercel).
- **Despublicar una nota:** en https://app.turso.tech → la BD → SQL console:
  `UPDATE articles SET estado = 'hidden' WHERE url_original = '...';`
- **Ver los suscriptores del newsletter:** misma SQL console:
  `SELECT nombre, email, fecha_alta, origen FROM suscriptores ORDER BY id DESC;`
  (`origen` dice si el alta vino del modal o de la página `/suscribirse`).

## Desarrollo local

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest -q          # tests (siempre SQLite local)
.venv\Scripts\uvicorn.exe app.main:app --port 8000   # sitio local con diario.db local
.venv\Scripts\python.exe -m scraper.run        # corrida local (BD local, salvo TURSO_* en el entorno)
```

- Validar fuentes RSS: `.venv\Scripts\python.exe -m scripts.validar_fuentes`
- Agregar una ficha a Financiamiento o Comunidades: sumarla a
  `app/financiamiento.py` o `app/comunidades.py` y correr
  `.venv\Scripts\python.exe -m scripts.descargar_logos` para bajar su logo al
  repo. Si el sitio no publica un logo usable, la ficha muestra el monograma.
- Revisar que los enlaces de ambos directorios sigan vivos:
  `.venv\Scripts\python.exe -m scripts.validar_directorios`
- `app/static/favicon.png` es el emblema del logo recortado en cuadrado
  (region 163,38 275x220 de `logo.png`, centrada sobre el fondo marfil).
- BD local de desarrollo: `diario.db` (SQLite) en la raíz del repo.
