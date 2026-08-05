# Copper Valley Diario

Diario web de noticias de startups y emprendimiento, con dos secciones:
**Startups Chile** y **Startups Mundo**. Un scraper diario lee fuentes RSS,
filtra y clasifica cada noticia con Claude y publica un titular y resumen
propios que citan y enlazan la fuente original.

## Producción

- **Sitio:** https://diario-startapero.vercel.app (Vercel, lee Turso)
- **Scraper:** GitHub Actions, diario a las 11:00 UTC (`.github/workflows/scraper.yml`);
  corrida manual: pestaña Actions → "Scraper diario" → Run workflow.
- **Base de datos:** Turso (`copper-valley-news`). Credenciales: secrets del
  repo (Actions) y environment variables (Vercel).
- **Despublicar una nota:** en https://app.turso.tech → la BD → SQL console:
  `UPDATE articles SET estado = 'hidden' WHERE url_original = '...';`

## Desarrollo local

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest -q          # tests (siempre SQLite local)
.venv\Scripts\uvicorn.exe app.main:app --port 8000   # sitio local con diario.db local
.venv\Scripts\python.exe -m scraper.run        # corrida local (BD local, salvo TURSO_* en el entorno)
```

- Validar fuentes RSS: `.venv\Scripts\python.exe -m scripts.validar_fuentes`
- BD local de desarrollo: `diario.db` (SQLite) en la raíz del repo.
