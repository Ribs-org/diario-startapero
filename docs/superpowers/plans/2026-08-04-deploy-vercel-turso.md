# Deploy Vercel + Turso + GitHub Actions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mover el Copper Valley Diario a la nube con costo US$0: scraper en GitHub Actions (cron diario), base de datos en Turso, sitio en Vercel; el PC del usuario queda solo para desarrollo.

**Architecture:** `db.py` gana una rama de conexión a Turso activada por variables de entorno, manteniendo su API pública intacta (SQLite local sigue siendo el default para dev/tests). Un workflow de Actions corre `python -m scraper.run` a diario contra Turso; Vercel sirve `app.main:app` leyendo Turso. Migración única de los datos locales.

**Tech Stack:** Turso (protocolo libsql), driver Python `libsql` (o `libsql-client` como fallback multiplataforma), GitHub Actions, Vercel `@vercel/python`, FastAPI existente.

**Spec:** `docs/superpowers/specs/2026-08-04-deploy-vercel-turso-design.md`

## Global Constraints

- Ningún secreto en código ni en git: `ANTHROPIC_API_KEY` solo como secret de GitHub Actions; `TURSO_DATABASE_URL`/`TURSO_AUTH_TOKEN` como secrets de Actions y variables de entorno de Vercel.
- La API pública de `db.py` (`get_connection`, `article_exists`, `insert_article`, `list_articles`) NO cambia de firma; scraper, web y tests existentes no se tocan salvo lo indicado.
- Precedencia de conexión: argumento `db_path` explícito → env `DIARIO_DB_PATH` → env `TURSO_*` (ambas presentes) → archivo local `diario.db`.
- La suite pytest sigue sin tocar red ni servicios reales; los 28 tests existentes deben seguir en verde en cada task.
- Entorno local: Windows + PowerShell; venv `.venv`; tests con `.venv\Scripts\python.exe -m pytest -q` desde la raíz. Cloud: Linux (Actions `ubuntu-latest`, Vercel).
- Cron del workflow: `0 11 * * *` (≈ 7-8 AM Chile todo el año) + `workflow_dispatch` para corridas manuales.
- Marca "Copper Valley Diario" en todo texto visible; textos en español.
- Repo GitHub: `Ribs-org/diario-startapero` (gh CLI ya autenticado con scope repo).

---

### Task 1: Cuenta Turso + spike del driver (decisión A/B)

Task interactiva (requiere al usuario) y con red. Sin TDD: es una validación
técnica cuyo resultado fija el driver de las tasks siguientes.

**Files:**
- Create: `scripts/spike_turso.py` (temporal — se BORRA al final de la task, no se commitea)

**Interfaces:**
- Produces: decisión **DRIVER = A (`libsql`)** o **DRIVER = B (`libsql-client`)**, registrada en el reporte; variables de entorno de usuario `TURSO_DATABASE_URL` y `TURSO_AUTH_TOKEN` seteadas en Windows.

- [ ] **Step 1: Crear la BD en Turso (con el usuario)**

Pedir al usuario que entre a https://app.turso.tech (login con GitHub), cree
un grupo/BD llamada `copper-valley-diario`, y desde la página de la BD copie:
- la URL (`libsql://copper-valley-diario-<org>.turso.io`)
- un auth token (botón "Generate Token", sin expiración o larga duración)

y las guarde en su Windows (terminal aparte, para no exponer el token en el chat):

```powershell
setx TURSO_DATABASE_URL "libsql://copper-valley-diario-<org>.turso.io"
setx TURSO_AUTH_TOKEN "<token>"
```

Verificar (sin imprimir el token):

```powershell
[Environment]::GetEnvironmentVariable("TURSO_DATABASE_URL","User")
([Environment]::GetEnvironmentVariable("TURSO_AUTH_TOKEN","User")).Length -gt 20
```

- [ ] **Step 2: Probar la instalación del driver preferido en Windows**

```powershell
.venv\Scripts\python.exe -m pip install libsql
```

- Si instala sin error (hay wheel win_amd64) → candidato **DRIVER = A**.
- Si falla la instalación → `.venv\Scripts\python.exe -m pip install libsql-client` → **DRIVER = B**.

- [ ] **Step 3: Spike contra la BD real**

Crear `scripts/spike_turso.py` con AMBAS variantes y correr solo la del driver instalado:

```python
"""Spike temporal: valida la API del driver contra la BD Turso real. NO COMMITEAR."""
import os

URL = os.environ["TURSO_DATABASE_URL"]
TOKEN = os.environ["TURSO_AUTH_TOKEN"]


def spike_a():
    import libsql
    conn = libsql.connect(URL, auth_token=TOKEN)
    conn.execute("CREATE TABLE IF NOT EXISTS spike (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE)")
    conn.commit()
    conn.execute("INSERT INTO spike (nombre) VALUES (?)", ("uno",))
    conn.commit()
    cur = conn.execute("SELECT * FROM spike WHERE nombre = ?", ("uno",))
    print("description:", cur.description)
    print("fetchone:", cur.fetchone())
    try:
        conn.execute("INSERT INTO spike (nombre) VALUES (?)", ("uno",))
        conn.commit()
        print("DUPLICADO NO LANZÓ ERROR (anotar)")
    except Exception as e:
        print("error de duplicado:", type(e).__name__, e)
    conn.execute("DROP TABLE spike")
    conn.commit()


def spike_b():
    import libsql_client
    client = libsql_client.create_client_sync(url=URL.replace("libsql://", "https://"), auth_token=TOKEN)
    client.execute("CREATE TABLE IF NOT EXISTS spike (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE)")
    client.execute("INSERT INTO spike (nombre) VALUES (?)", ["uno"])
    rs = client.execute("SELECT * FROM spike WHERE nombre = ?", ["uno"])
    print("columns:", rs.columns)
    print("rows:", [tuple(r) for r in rs.rows])
    try:
        client.execute("INSERT INTO spike (nombre) VALUES (?)", ["uno"])
        print("DUPLICADO NO LANZÓ ERROR (anotar)")
    except Exception as e:
        print("error de duplicado:", type(e).__name__, e)
    client.execute("DROP TABLE spike")
    client.close()


if __name__ == "__main__":
    spike_a()  # o spike_b() según el driver instalado
```

Correr cargando las env vars de usuario en el proceso:

```powershell
$env:TURSO_DATABASE_URL = [Environment]::GetEnvironmentVariable("TURSO_DATABASE_URL","User")
$env:TURSO_AUTH_TOKEN = [Environment]::GetEnvironmentVariable("TURSO_AUTH_TOKEN","User")
.venv\Scripts\python.exe -m scripts.spike_turso
```

Registrar en el reporte: driver elegido, forma exacta de `description`/`columns`,
comportamiento de fetchone/fetchall, y el tipo de excepción de duplicado.
Si el DRIVER A instala pero el spike falla contra la BD real, pasar a DRIVER B
y repetir el spike.

- [ ] **Step 4: Borrar el spike y no commitear nada**

```powershell
Remove-Item scripts\spike_turso.py
git status --short   # debe quedar limpio
```

---

### Task 2: Rama Turso en `db.py` + normalización de filas

**Files:**
- Modify: `db.py`
- Modify: `requirements.txt` (agregar el driver elegido en Task 1)
- Create: `tests/conftest.py`
- Test: `tests/test_db_turso.py`

**Interfaces:**
- Consumes: decisión DRIVER A/B de Task 1.
- Produces: `db.get_connection()` con precedencia `db_path` → `DIARIO_DB_PATH` → `TURSO_*` → default local; `db.list_articles` retorna `list[dict]` (acceso por nombre igual que antes); resto de la API sin cambios. Tasks 3-5 dependen de que `db.get_connection()` conecte a Turso cuando solo hay `TURSO_*` en el entorno.

- [ ] **Step 1: Crear `tests/conftest.py`** (blinda la suite contra credenciales Turso presentes en la máquina)

```python
import pytest


@pytest.fixture(autouse=True)
def sin_turso(monkeypatch):
    """Los tests siempre usan SQLite local, aunque el entorno tenga Turso."""
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
```

- [ ] **Step 2: Escribir los tests que fallan**

Crear `tests/test_db_turso.py` (el módulo del driver se inyecta falso en
`sys.modules`; nunca se usa el real):

```python
import sys
import types

import db


def fake_driver(monkeypatch, registro):
    """Inyecta un módulo 'libsql' falso que registra la conexión."""
    modulo = types.ModuleType("libsql")

    class FakeCursor:
        description = [("id",), ("titulo",)]

        def fetchall(self):
            return [(1, "Titular remoto")]

        def fetchone(self):
            return (1, "Titular remoto")

    class FakeConn:
        def execute(self, sql, params=()):
            registro.setdefault("sqls", []).append(sql)
            return FakeCursor()

        def commit(self):
            registro["commit"] = True

    def connect(url, auth_token):
        registro["url"] = url
        registro["auth_token"] = auth_token
        return FakeConn()

    modulo.connect = connect
    monkeypatch.setitem(sys.modules, "libsql", modulo)


def test_usa_turso_cuando_solo_hay_credenciales(monkeypatch):
    registro = {}
    fake_driver(monkeypatch, registro)
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection()
    assert registro["url"] == "libsql://ejemplo.turso.io"
    assert registro["auth_token"] == "token-fake"
    assert any("CREATE TABLE" in s for s in registro["sqls"])  # aplicó el schema


def test_db_path_explicito_gana_a_turso(monkeypatch, tmp_path):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection(tmp_path / "local.db")  # no debe importar libsql
    assert db.list_articles(conn) == []


def test_diario_db_path_gana_a_turso(monkeypatch, tmp_path):
    monkeypatch.setenv("DIARIO_DB_PATH", str(tmp_path / "local.db"))
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection()
    assert db.list_articles(conn) == []


def test_list_articles_devuelve_dicts_con_driver_remoto(monkeypatch):
    registro = {}
    fake_driver(monkeypatch, registro)
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection()
    filas = db.list_articles(conn)
    assert filas == [{"id": 1, "titulo": "Titular remoto"}]
```

Nota (solo si Task 1 decidió DRIVER B): el fake inyecta `libsql_client` en vez
de `libsql`, con `create_client_sync(url=..., auth_token=...)` que registra la
llamada y devuelve un cliente falso con `execute(sql, params)` que retorna un
objeto con `columns = ("id", "titulo")` y `rows = [(1, "Titular remoto")]`.
Las aserciones de los 4 tests no cambian.

- [ ] **Step 3: Verificar que fallan**

Run: `.venv\Scripts\python.exe -m pytest tests/test_db_turso.py -q`
Expected: FAIL (get_connection ignora TURSO_* y va a SQLite local; el primer test no ve `registro["url"]`)

- [ ] **Step 4: Implementar en `db.py`**

Reemplazar `get_connection` y `list_articles`; agregar `_turso_connection`.
Versión para **DRIVER A** (`libsql`):

```python
def get_connection(db_path=None):
    destino = db_path or os.environ.get("DIARIO_DB_PATH")
    if (destino is None and os.environ.get("TURSO_DATABASE_URL")
            and os.environ.get("TURSO_AUTH_TOKEN")):
        return _turso_connection()
    path = Path(destino or DEFAULT_DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def _turso_connection():
    import libsql  # import perezoso: el paquete solo se necesita con Turso
    conn = libsql.connect(
        os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def list_articles(conn, seccion=None, limit=30):
    query = "SELECT * FROM articles WHERE estado = 'published'"
    params = []
    if seccion:
        query += " AND seccion = ?"
        params.append(seccion)
    query += " ORDER BY fecha_publicacion DESC, id DESC LIMIT ?"
    params.append(limit)
    cur = conn.execute(query, params)
    columnas = [d[0] for d in cur.description]
    return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
```

(`article_exists` e `insert_article` quedan como están: usan
`execute(...).fetchone()`, `execute(...)` + `commit()`, compatibles con ambos
backends para DRIVER A.)

Versión para **DRIVER B** (`libsql-client`) — `_turso_connection` devuelve un
adaptador con la misma superficie que usamos de sqlite3:

```python
def _turso_connection():
    import libsql_client
    client = libsql_client.create_client_sync(
        url=os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://"),
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )
    conn = _TursoConn(client)
    conn.execute(SCHEMA)
    return conn


class _Resultado:
    def __init__(self, rs):
        self.description = [(nombre,) for nombre in rs.columns]
        self._filas = [tuple(f) for f in rs.rows]

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return self._filas


class _TursoConn:
    """Superficie mínima de sqlite3.Connection sobre libsql-client (autocommit)."""

    def __init__(self, client):
        self._client = client

    def execute(self, sql, params=()):
        return _Resultado(self._client.execute(sql, list(params)))

    def commit(self):
        pass

    def close(self):
        self._client.close()
```

Agregar al final de `requirements.txt` el driver elegido: `libsql` o `libsql-client`.
Si en Task 1 el driver A no tenía wheel de Windows pero se eligió igual para
cloud (no aplica por defecto — solo si Task 1 lo decidió así explícitamente),
usar marcador de entorno: `libsql ; sys_platform == "linux"`.

- [ ] **Step 5: Verificar toda la suite**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: 32 passed (28 existentes + 4 nuevos), 1 warning preexistente. Los
tests existentes de `db` siguen pasando porque `dict` también se indexa por
nombre de columna.

- [ ] **Step 6: Commit**

```powershell
git add db.py requirements.txt tests/conftest.py tests/test_db_turso.py
git commit -m "feat: conexion opcional a Turso en db.py con fallback local"
```

---

### Task 3: Migración de datos local → Turso (corrida real)

**Files:**
- Create: `scripts/migrar_a_turso.py`

**Interfaces:**
- Consumes: `db.get_connection()` (rama Turso vía env), `db.article_exists`, `db.insert_article`; el `diario.db` local con las noticias existentes.
- Produces: BD Turso poblada con todas las noticias locales.

- [ ] **Step 1: Crear `scripts/migrar_a_turso.py`**

```python
"""Migración de un solo uso: sube el diario.db local a Turso.

Uso (PowerShell, con TURSO_DATABASE_URL y TURSO_AUTH_TOKEN en el entorno):
  .venv\Scripts\python.exe -m scripts.migrar_a_turso
"""
import os
import sqlite3
from pathlib import Path

import db

LOCAL = Path(__file__).resolve().parent.parent / "diario.db"


def main():
    if not (os.environ.get("TURSO_DATABASE_URL") and os.environ.get("TURSO_AUTH_TOKEN")):
        raise SystemExit("Faltan TURSO_DATABASE_URL / TURSO_AUTH_TOKEN en el entorno")
    origen = sqlite3.connect(LOCAL)
    origen.row_factory = sqlite3.Row
    filas = origen.execute(
        "SELECT * FROM articles WHERE estado = 'published' ORDER BY id"
    ).fetchall()
    destino = db.get_connection()  # con TURSO_* presentes conecta a Turso
    migradas = saltadas = 0
    for f in filas:
        if db.article_exists(destino, f["url_original"]):
            saltadas += 1
            continue
        db.insert_article(
            destino,
            url_original=f["url_original"], fuente=f["fuente"],
            titulo=f["titulo"], resumen=f["resumen"], seccion=f["seccion"],
            fecha_publicacion=f["fecha_publicacion"],
            fecha_scrapeo=f["fecha_scrapeo"],
        )
        migradas += 1
    print(f"Migradas: {migradas} | Saltadas (ya existían): {saltadas}")


if __name__ == "__main__":
    main()
```

(Notas: solo migra `published` — hoy no hay `hidden`. Es re-ejecutable: la
segunda corrida salta todo por dedup.)

- [ ] **Step 2: Ejecutar la migración**

```powershell
$env:TURSO_DATABASE_URL = [Environment]::GetEnvironmentVariable("TURSO_DATABASE_URL","User")
$env:TURSO_AUTH_TOKEN = [Environment]::GetEnvironmentVariable("TURSO_AUTH_TOKEN","User")
.venv\Scripts\python.exe -m scripts.migrar_a_turso
```

Expected: `Migradas: <N> | Saltadas: 0` con N = cantidad de noticias locales.

- [ ] **Step 3: Verificar contra Turso**

```powershell
.venv\Scripts\python.exe -c "import db; conn = db.get_connection(); print(len(db.list_articles(conn, limit=200)), 'articulos en Turso')"
```

(mismo shell, con las env vars aún seteadas). Expected: N articulos. Re-correr
la migración y verificar `Saltadas: N` (idempotencia).

- [ ] **Step 4: Suite en verde y commit**

```powershell
.venv\Scripts\python.exe -m pytest -q
git add scripts/migrar_a_turso.py
git commit -m "feat: script de migracion unica de diario.db local a Turso"
```

---

### Task 4: Workflow de GitHub Actions (scraper diario)

**Files:**
- Create: `.github/workflows/scraper.yml`

**Interfaces:**
- Consumes: `python -m scraper.run` (sin cambios), secrets del repo.
- Produces: corrida diaria automática del scraper contra Turso.

- [ ] **Step 1: Crear `.github/workflows/scraper.yml`**

```yaml
name: Scraper diario

on:
  schedule:
    - cron: "0 11 * * *"   # ≈ 7-8 AM Chile todo el año
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Instalar dependencias
        run: pip install -r requirements.txt
      - name: Correr scraper
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
        run: python -m scraper.run
```

- [ ] **Step 2: Cargar los secrets del repo con gh (sin exponerlos en el chat)**

```powershell
[Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY","User") | gh secret set ANTHROPIC_API_KEY --repo Ribs-org/diario-startapero
[Environment]::GetEnvironmentVariable("TURSO_DATABASE_URL","User") | gh secret set TURSO_DATABASE_URL --repo Ribs-org/diario-startapero
[Environment]::GetEnvironmentVariable("TURSO_AUTH_TOKEN","User") | gh secret set TURSO_AUTH_TOKEN --repo Ribs-org/diario-startapero
gh secret list --repo Ribs-org/diario-startapero
```

Expected: los 3 secrets listados.

- [ ] **Step 3: Commit y push (el workflow debe estar en el repo remoto para poder dispararse)**

```powershell
git add .github/workflows/scraper.yml
git commit -m "feat: workflow diario del scraper en GitHub Actions"
git push origin main
```

- [ ] **Step 4: Corrida manual de verificación**

```powershell
gh workflow run scraper.yml --repo Ribs-org/diario-startapero
Start-Sleep -Seconds 20
gh run list --workflow scraper.yml --repo Ribs-org/diario-startapero --limit 1
gh run watch --repo Ribs-org/diario-startapero --exit-status
```

Expected: run `completed success`. Luego verificar que Turso siguió/creció:

```powershell
$env:TURSO_DATABASE_URL = [Environment]::GetEnvironmentVariable("TURSO_DATABASE_URL","User")
$env:TURSO_AUTH_TOKEN = [Environment]::GetEnvironmentVariable("TURSO_AUTH_TOKEN","User")
.venv\Scripts\python.exe -c "import db; conn = db.get_connection(); print(len(db.list_articles(conn, limit=500)), 'articulos en Turso')"
```

(la mayoría de las noticias del día ya existen → dedup; el conteo debe ser ≥ el de Task 3).

---

### Task 5: Sitio en Vercel

**Files:**
- Create: `api/index.py`, `vercel.json`, `.vercelignore`

**Interfaces:**
- Consumes: `app.main:app` (sin cambios), variables `TURSO_*` en Vercel.
- Produces: sitio público en `https://<proyecto>.vercel.app`.

- [ ] **Step 1: Crear los archivos de Vercel**

`api/index.py`:

```python
"""Entrypoint de Vercel: expone la app FastAPI existente."""
from app.main import app  # noqa: F401
```

`vercel.json`:

```json
{
  "version": 2,
  "builds": [{ "src": "api/index.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "api/index.py" }]
}
```

`.vercelignore`:

```
.venv/
diario.db
docs/
assets/
tests/
scripts/
.github/
.claude/
```

- [ ] **Step 2: Commit y push**

```powershell
git add api/ vercel.json .vercelignore
git commit -m "feat: configuracion de deploy del sitio en Vercel"
git push origin main
```

- [ ] **Step 3: Importar el proyecto en Vercel (con el usuario)**

Pedir al usuario: entrar a https://vercel.com/new (login con GitHub), importar
`Ribs-org/diario-startapero`, y antes de "Deploy" agregar las Environment
Variables `TURSO_DATABASE_URL` y `TURSO_AUTH_TOKEN` (los mismos valores que
guardó en Windows; puede copiarlos de `app.turso.tech`). Framework preset:
"Other". Deploy.

- [ ] **Step 4: Verificar el sitio publicado**

Con la URL que entregue Vercel (`https://<proyecto>.vercel.app`):

```powershell
Invoke-WebRequest https://<proyecto>.vercel.app/ -UseBasicParsing | Select-Object -ExpandProperty StatusCode
Invoke-WebRequest https://<proyecto>.vercel.app/mundo -UseBasicParsing | Select-Object -ExpandProperty StatusCode
```

Expected: 200 y 200; abrir en navegador y confirmar visualmente portada con
noticias reales, logo y estilos (los estáticos se sirven vía la función).
Si `/static/style.css` diera 404 o 500, revisar que la ruta catch-all de
`vercel.json` esté enrutando a `api/index.py` (es la única ruta definida).

---

### Task 6: Cutover — apagar la tarea local y documentar

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: todo lo anterior funcionando (workflow verde, sitio arriba).

- [ ] **Step 1: Eliminar la tarea programada de Windows**

```powershell
schtasks /Delete /TN "CopperValleyDiario" /F
schtasks /Query /TN "CopperValleyDiario" 2>$null; if (-not $?) { "OK: tarea eliminada" }
```

- [ ] **Step 2: Actualizar `README.md`**

Reemplazar la sección "Cómo correr" y "Operación" para reflejar la realidad
cloud (mantener el resto):

```markdown
## Producción

- **Sitio:** https://<proyecto>.vercel.app (Vercel, lee Turso)
- **Scraper:** GitHub Actions, diario a las 11:00 UTC (`.github/workflows/scraper.yml`);
  corrida manual: pestaña Actions → "Scraper diario" → Run workflow.
- **Base de datos:** Turso (`copper-valley-diario`). Credenciales: secrets del
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
```

(sustituir `<proyecto>` por la URL real que dio Vercel).

- [ ] **Step 3: Suite en verde, commit y push**

```powershell
.venv\Scripts\python.exe -m pytest -q
git add README.md
git commit -m "docs: operacion en la nube (Vercel + Turso + Actions)"
git push origin main
```
