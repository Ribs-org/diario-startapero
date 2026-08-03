# Copper Valley Diario v1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Diario web de startups (Copper Valley Diario) con scraper diario que lee RSS, clasifica y resume con Claude, y publica en un sitio FastAPI con secciones Startups Chile y Startups Mundo.

**Architecture:** Monolito Python: un scraper por comandos (`python -m scraper.run`) escribe en SQLite; una web FastAPI + Jinja2 server-rendered solo lee de SQLite. El LLM (Claude Haiku) se usa únicamente en el scraper, nunca en la web.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, SQLite (stdlib `sqlite3`), feedparser, httpx, trafilatura, SDK `anthropic`, pytest.

**Spec:** `docs/superpowers/specs/2026-08-03-copper-valley-diario-design.md`

## Global Constraints

- La marca es **"Copper Valley Diario"** en todos los textos visibles; nunca usar "Diario Startupero".
- Todos los textos del sitio y los prompts piden contenido en **español**.
- Modelo LLM: `claude-haiku-4-5-20251001` (constante `MODEL` en cada módulo que llama al LLM).
- La API key va SOLO en la variable de entorno `ANTHROPIC_API_KEY`; jamás en el código ni en git.
- Valores de `seccion`: exactamente `'chile'` o `'mundo'`. Valores de `estado`: `'published'` o `'hidden'`.
- Los tests NUNCA tocan la red ni la API real: fixtures RSS locales y clientes LLM falsos.
- La ruta de la BD se resuelve así: argumento explícito → env `DIARIO_DB_PATH` → `diario.db` junto a `db.py`.
- Entorno de desarrollo: Windows + PowerShell; el venv es `.venv` y los tests se corren con `python -m pytest -q` desde la raíz del repo.
- Paleta (de `assets/paleta de colores.txt`): marfil `#F4F1ED` fondo, azul marino `#0F1D2D` titulares, azul pizarra `#334155` apoyo, gris acero `#8A9199` secundarios, cobre `#B87333` acento/enlaces, cobre claro `#D4A373` detalles.
- **Nota deploy:** el deploy a Vercel (elegido en el spec) queda FUERA de este plan: Vercel es serverless y no persiste SQLite, así que al llegar a esa fase hay que decidir BD gestionada (Turso/Postgres) u otro host. Este plan termina con el diario funcionando y agendado en local.

---

### Task 1: Scaffold del proyecto + capa de datos (`db.py`)

**Files:**
- Create: `requirements.txt`, `.gitignore`, `db.py`, `tests/test_db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces: `db.get_connection(db_path=None) -> sqlite3.Connection` (crea la tabla si no existe, `row_factory=sqlite3.Row`); `db.article_exists(conn, url_original) -> bool`; `db.insert_article(conn, *, url_original, fuente, titulo, resumen, seccion, fecha_publicacion, fecha_scrapeo) -> None` (estado por defecto `'published'`; URL duplicada lanza `sqlite3.IntegrityError`); `db.list_articles(conn, seccion=None, limit=30) -> list[sqlite3.Row]` (solo `published`, orden `fecha_publicacion DESC, id DESC`).

- [ ] **Step 1: Crear venv e instalar dependencias**

Crear `requirements.txt`:

```
fastapi
uvicorn[standard]
jinja2
feedparser
httpx
trafilatura
anthropic
pytest
```

Crear `.gitignore`:

```
.venv/
__pycache__/
*.pyc
diario.db
.env
```

Ejecutar en PowerShell desde la raíz del repo:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

(En los pasos siguientes, `python` = `.venv\Scripts\python.exe`; activar con `.venv\Scripts\Activate.ps1` si se prefiere.)

- [ ] **Step 2: Escribir los tests que fallan**

Crear `tests/test_db.py`:

```python
import sqlite3

import pytest

import db


def make_conn(tmp_path):
    return db.get_connection(tmp_path / "test.db")


def insertar(conn, url, titulo="Titular", seccion="chile", fecha_pub="2026-08-03"):
    db.insert_article(
        conn,
        url_original=url,
        fuente="Fuente de Prueba",
        titulo=titulo,
        resumen="Un resumen de prueba.",
        seccion=seccion,
        fecha_publicacion=fecha_pub,
        fecha_scrapeo="2026-08-03T10:00:00",
    )


def test_insert_y_exists(tmp_path):
    conn = make_conn(tmp_path)
    assert not db.article_exists(conn, "https://ej.cl/nota-1")
    insertar(conn, "https://ej.cl/nota-1")
    assert db.article_exists(conn, "https://ej.cl/nota-1")


def test_url_duplicada_lanza_error(tmp_path):
    conn = make_conn(tmp_path)
    insertar(conn, "https://ej.cl/nota-1")
    with pytest.raises(sqlite3.IntegrityError):
        insertar(conn, "https://ej.cl/nota-1")


def test_list_articles_filtra_y_ordena(tmp_path):
    conn = make_conn(tmp_path)
    insertar(conn, "https://ej.cl/vieja", titulo="Chile vieja", fecha_pub="2026-08-01")
    insertar(conn, "https://ej.cl/nueva", titulo="Chile nueva", fecha_pub="2026-08-03")
    insertar(conn, "https://ej.com/mundo", titulo="Mundo", seccion="mundo")
    rows = db.list_articles(conn, seccion="chile")
    assert [r["titulo"] for r in rows] == ["Chile nueva", "Chile vieja"]


def test_list_articles_excluye_hidden(tmp_path):
    conn = make_conn(tmp_path)
    insertar(conn, "https://ej.cl/nota-1", titulo="Visible")
    insertar(conn, "https://ej.cl/nota-2", titulo="Oculta")
    conn.execute("UPDATE articles SET estado = 'hidden' WHERE titulo = 'Oculta'")
    conn.commit()
    rows = db.list_articles(conn)
    assert [r["titulo"] for r in rows] == ["Visible"]


def test_list_articles_respeta_limit(tmp_path):
    conn = make_conn(tmp_path)
    for i in range(5):
        insertar(conn, f"https://ej.cl/nota-{i}")
    assert len(db.list_articles(conn, limit=3)) == 3
```

- [ ] **Step 3: Verificar que fallan**

Run: `python -m pytest tests/test_db.py -q`
Expected: FAIL/ERROR con `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 4: Implementar `db.py`**

```python
"""Acceso a datos de Copper Valley Diario (SQLite)."""
import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "diario.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_original TEXT NOT NULL UNIQUE,
    fuente TEXT NOT NULL,
    titulo TEXT NOT NULL,
    resumen TEXT NOT NULL,
    seccion TEXT NOT NULL CHECK (seccion IN ('chile', 'mundo')),
    fecha_publicacion TEXT NOT NULL,
    fecha_scrapeo TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'published' CHECK (estado IN ('published', 'hidden'))
)
"""


def get_connection(db_path=None):
    path = Path(db_path or os.environ.get("DIARIO_DB_PATH") or DEFAULT_DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def article_exists(conn, url_original):
    row = conn.execute(
        "SELECT 1 FROM articles WHERE url_original = ?", (url_original,)
    ).fetchone()
    return row is not None


def insert_article(conn, *, url_original, fuente, titulo, resumen, seccion,
                   fecha_publicacion, fecha_scrapeo):
    conn.execute(
        """INSERT INTO articles
           (url_original, fuente, titulo, resumen, seccion,
            fecha_publicacion, fecha_scrapeo)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (url_original, fuente, titulo, resumen, seccion,
         fecha_publicacion, fecha_scrapeo),
    )
    conn.commit()


def list_articles(conn, seccion=None, limit=30):
    query = "SELECT * FROM articles WHERE estado = 'published'"
    params = []
    if seccion:
        query += " AND seccion = ?"
        params.append(seccion)
    query += " ORDER BY fecha_publicacion DESC, id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(query, params).fetchall()
```

- [ ] **Step 5: Verificar que pasan**

Run: `python -m pytest tests/test_db.py -q`
Expected: 5 passed

- [ ] **Step 6: Commit**

```powershell
git add requirements.txt .gitignore db.py tests/test_db.py
git commit -m "feat: scaffold del proyecto y capa de datos SQLite"
```

---

### Task 2: Lectura de feeds (`scraper/fetch.py`)

**Files:**
- Create: `scraper/__init__.py` (vacío), `scraper/fetch.py`, `tests/fixtures/sample_feed.xml`, `tests/test_fetch.py`
- Test: `tests/test_fetch.py`

**Interfaces:**
- Produces: dataclass `FeedItem(titulo: str, url: str, extracto: str, fecha: datetime)` (fecha aware en UTC); `parse_feed(feed_content) -> list[FeedItem]` (descarta entradas sin fecha o sin link; extracto sin HTML); `filter_recent(items, days=2, now=None) -> list[FeedItem]`; `fetch_feed(url) -> list[FeedItem]` (red); `fetch_article_text(url) -> str | None` (red, extrae texto con trafilatura).

- [ ] **Step 1: Crear fixture RSS**

Crear `tests/fixtures/sample_feed.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Feed de prueba</title>
    <item>
      <title>Startup A levanta US$5M</title>
      <link>https://ejemplo.com/a</link>
      <description>La startup A &lt;b&gt;anunció&lt;/b&gt; una ronda semilla.</description>
      <pubDate>Mon, 03 Aug 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Noticia vieja</title>
      <link>https://ejemplo.com/b</link>
      <description>Una noticia antigua.</description>
      <pubDate>Mon, 20 Jul 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Sin fecha</title>
      <link>https://ejemplo.com/c</link>
      <description>Entrada sin pubDate.</description>
    </item>
  </channel>
</rss>
```

- [ ] **Step 2: Escribir los tests que fallan**

Crear `tests/test_fetch.py`:

```python
from datetime import datetime, timezone
from pathlib import Path

from scraper.fetch import filter_recent, parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "sample_feed.xml"


def cargar():
    return parse_feed(FIXTURE.read_text(encoding="utf-8"))


def test_parse_feed_extrae_items():
    items = cargar()
    assert len(items) == 2  # descarta la entrada sin fecha
    a = items[0]
    assert a.titulo == "Startup A levanta US$5M"
    assert a.url == "https://ejemplo.com/a"
    assert "anunció" in a.extracto
    assert "<b>" not in a.extracto
    assert a.fecha == datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)


def test_filter_recent_deja_solo_lo_nuevo():
    items = cargar()
    now = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
    recientes = filter_recent(items, days=2, now=now)
    assert [i.url for i in recientes] == ["https://ejemplo.com/a"]
```

- [ ] **Step 3: Verificar que fallan**

Run: `python -m pytest tests/test_fetch.py -q`
Expected: FAIL/ERROR con `ModuleNotFoundError: No module named 'scraper'`

- [ ] **Step 4: Implementar `scraper/fetch.py`** (y crear `scraper/__init__.py` vacío)

```python
"""Descarga y parseo de feeds RSS y artículos."""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
import trafilatura

HEADERS = {"User-Agent": "CopperValleyDiario/1.0 (+diario de startups)"}
TIMEOUT = 30


@dataclass
class FeedItem:
    titulo: str
    url: str
    extracto: str
    fecha: datetime  # aware, UTC


def _sin_html(texto):
    return re.sub(r"<[^>]+>", " ", texto).strip()


def parse_feed(feed_content):
    parsed = feedparser.parse(feed_content)
    items = []
    for entry in parsed.entries:
        fecha_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        link = entry.get("link")
        if not fecha_struct or not link:
            continue
        fecha = datetime(*fecha_struct[:6], tzinfo=timezone.utc)
        items.append(FeedItem(
            titulo=entry.get("title", "").strip(),
            url=link,
            extracto=_sin_html(entry.get("summary", "")),
            fecha=fecha,
        ))
    return items


def filter_recent(items, days=2, now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    return [i for i in items if i.fecha >= cutoff]


def fetch_feed(url):
    resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
    resp.raise_for_status()
    return parse_feed(resp.content)


def fetch_article_text(url):
    resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
    resp.raise_for_status()
    return trafilatura.extract(resp.text)
```

- [ ] **Step 5: Verificar que pasan**

Run: `python -m pytest tests/test_fetch.py -q`
Expected: 2 passed

- [ ] **Step 6: Commit**

```powershell
git add scraper/ tests/fixtures/ tests/test_fetch.py
git commit -m "feat: lectura y parseo de feeds RSS con filtro de recientes"
```

---

### Task 3: Clasificador LLM (`scraper/classify.py`)

**Files:**
- Create: `scraper/classify.py`, `tests/fakes.py`, `tests/test_classify.py`
- Test: `tests/test_classify.py`

**Interfaces:**
- Consumes: nada del proyecto (solo SDK `anthropic`).
- Produces: `classify(titulo, extracto, client=None) -> str | None` — retorna `'chile'`, `'mundo'` o `None` (descartar / respuesta inesperada). `client` acepta cualquier objeto con `messages.create(**kwargs)` (inyección para tests); si es `None` crea `anthropic.Anthropic()`. También `tests/fakes.py` con `FakeClient` reutilizable por las tareas 4 y 5.

- [ ] **Step 1: Crear el cliente falso compartido**

Crear `tests/fakes.py`:

```python
"""Dobles de prueba compartidos."""
from types import SimpleNamespace


class FakeClient:
    """Imita anthropic.Anthropic(): client.messages.create(...) -> respuesta fija."""

    def __init__(self, texto_respuesta):
        self._texto = texto_respuesta
        self.kwargs = None  # guarda la última llamada para inspección
        self.messages = self

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text=self._texto)])
```

- [ ] **Step 2: Escribir los tests que fallan**

Crear `tests/test_classify.py`:

```python
from scraper.classify import classify
from tests.fakes import FakeClient


def test_clasifica_chile():
    fake = FakeClient("chile")
    assert classify("Startup chilena levanta ronda", "extracto", client=fake) == "chile"
    assert "Startup chilena levanta ronda" in fake.kwargs["messages"][0]["content"]


def test_clasifica_mundo():
    assert classify("YC anuncia batch", "extracto", client=FakeClient("mundo")) == "mundo"


def test_descartar_retorna_none():
    assert classify("Resultados del fútbol", "extracto", client=FakeClient("descartar")) is None


def test_respuesta_inesperada_retorna_none():
    assert classify("Titular", "extracto", client=FakeClient("no estoy seguro")) is None


def test_normaliza_mayusculas_y_espacios():
    assert classify("Titular", "extracto", client=FakeClient("  Chile \n")) == "chile"
```

- [ ] **Step 3: Verificar que fallan**

Run: `python -m pytest tests/test_classify.py -q`
Expected: FAIL/ERROR con `ModuleNotFoundError: No module named 'scraper.classify'`

- [ ] **Step 4: Implementar `scraper/classify.py`**

```python
"""Filtra y clasifica noticias con Claude: chile / mundo / descartar."""
import anthropic

MODEL = "claude-haiku-4-5-20251001"

SYSTEM = (
    "Eres el editor de Copper Valley Diario, un diario sobre startups y "
    "emprendimiento. Recibirás el titular y el extracto de una noticia. "
    "Responde con UNA sola palabra:\n"
    "- chile: si trata sobre startups, emprendimiento o venture capital y su "
    "foco es Chile o una startup chilena.\n"
    "- mundo: si trata sobre startups, emprendimiento o venture capital de "
    "cualquier otro país o a nivel global.\n"
    "- descartar: si NO trata sobre startups ni emprendimiento (política, "
    "deportes, farándula, empresas tradicionales, macroeconomía general, etc.)."
)


def classify(titulo, extracto, client=None):
    client = client or anthropic.Anthropic()
    respuesta = client.messages.create(
        model=MODEL,
        max_tokens=10,
        system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"Titular: {titulo}\nExtracto: {extracto}"}],
    )
    texto = respuesta.content[0].text.strip().lower()
    if texto in ("chile", "mundo"):
        return texto
    return None
```

- [ ] **Step 5: Verificar que pasan**

Run: `python -m pytest tests/test_classify.py -q`
Expected: 5 passed

- [ ] **Step 6: Commit**

```powershell
git add scraper/classify.py tests/fakes.py tests/test_classify.py
git commit -m "feat: clasificador LLM chile/mundo/descartar"
```

---

### Task 4: Redactor de resúmenes (`scraper/summarize.py`)

**Files:**
- Create: `scraper/summarize.py`, `tests/test_summarize.py`
- Test: `tests/test_summarize.py`

**Interfaces:**
- Consumes: `tests/fakes.FakeClient` (de Task 3).
- Produces: `summarize(titulo_original, texto, fuente, client=None) -> dict | None` — retorna `{"titulo": str, "resumen": str}` o `None` si la respuesta del LLM no es JSON válido o le faltan claves. Trunca `texto` a `MAX_CHARS = 6000`. Tolera respuestas envueltas en fences ``` de markdown.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_summarize.py`:

```python
from scraper.summarize import MAX_CHARS, summarize
from tests.fakes import FakeClient

JSON_OK = '{"titulo": "Titular propio", "resumen": "Párrafo uno.\\n\\nPárrafo dos."}'


def test_resumen_valido():
    resultado = summarize("Original", "Texto del artículo.", "TechCrunch",
                          client=FakeClient(JSON_OK))
    assert resultado == {"titulo": "Titular propio",
                         "resumen": "Párrafo uno.\n\nPárrafo dos."}


def test_tolera_fences_markdown():
    fake = FakeClient(f"```json\n{JSON_OK}\n```")
    assert summarize("Original", "Texto.", "Sifted", client=fake)["titulo"] == "Titular propio"


def test_json_invalido_retorna_none():
    assert summarize("Original", "Texto.", "Sifted", client=FakeClient("no es json")) is None


def test_faltan_claves_retorna_none():
    assert summarize("Original", "Texto.", "Sifted",
                     client=FakeClient('{"titulo": "Solo titular"}')) is None


def test_trunca_texto_largo():
    fake = FakeClient(JSON_OK)
    summarize("Original", "x" * 20000, "Sifted", client=fake)
    contenido = fake.kwargs["messages"][0]["content"]
    assert len(contenido) < MAX_CHARS + 500  # texto truncado + encabezado corto
```

- [ ] **Step 2: Verificar que fallan**

Run: `python -m pytest tests/test_summarize.py -q`
Expected: FAIL/ERROR con `ModuleNotFoundError: No module named 'scraper.summarize'`

- [ ] **Step 3: Implementar `scraper/summarize.py`**

```python
"""Genera titular y resumen propios con Claude."""
import json
import re

import anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_CHARS = 6000

SYSTEM = (
    "Eres periodista de Copper Valley Diario, un diario en español sobre "
    "startups y emprendimiento. A partir del texto entregado escribe:\n"
    "- Un titular propio, informativo y sobrio (sin clickbait).\n"
    "- Un resumen propio de 2 a 3 párrafos en español, fiel al texto. No "
    "inventes datos ni cifras que no estén en el texto.\n"
    'Responde SOLO con JSON válido, sin texto adicional: '
    '{"titulo": "...", "resumen": "..."}'
)


def summarize(titulo_original, texto, fuente, client=None):
    client = client or anthropic.Anthropic()
    contenido = (f"Fuente: {fuente}\n"
                 f"Titular original: {titulo_original}\n\n"
                 f"Texto:\n{texto[:MAX_CHARS]}")
    respuesta = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": contenido}],
    )
    bruto = respuesta.content[0].text.strip()
    bruto = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", bruto)
    try:
        datos = json.loads(bruto)
    except json.JSONDecodeError:
        return None
    if not datos.get("titulo") or not datos.get("resumen"):
        return None
    return {"titulo": datos["titulo"], "resumen": datos["resumen"]}
```

- [ ] **Step 4: Verificar que pasan**

Run: `python -m pytest tests/test_summarize.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```powershell
git add scraper/summarize.py tests/test_summarize.py
git commit -m "feat: redactor de titular y resumen propios con Claude"
```

---

### Task 5: Fuentes y orquestador (`scraper/sources.py`, `scraper/run.py`)

**Files:**
- Create: `scraper/sources.py`, `scraper/run.py`, `tests/test_run.py`
- Test: `tests/test_run.py`

**Interfaces:**
- Consumes: `db.*` (Task 1), `scraper.fetch` (Task 2), `scraper.classify.classify` (Task 3), `scraper.summarize.summarize` (Task 4).
- Produces: `SOURCES: list[dict]` con claves `nombre` y `feed_url`; `process_item(conn, client, source, item) -> bool` (True si guardó); `process_source(conn, client, source) -> int` (cantidad guardada; errores por ítem no la abortan); `main()` (entry point de `python -m scraper.run`; errores por fuente no abortan la corrida).

- [ ] **Step 1: Crear `scraper/sources.py`**

Las URLs son candidatas; la Task 7 las valida contra la red y reemplaza las que fallen.

```python
"""Fuentes RSS de Copper Valley Diario (validadas en la task de puesta en marcha)."""

SOURCES = [
    # Orientadas a Chile / LATAM
    {"nombre": "La Tercera - Pulso",
     "feed_url": "https://www.latercera.com/arc/outboundfeeds/rss/category/pulso/?outputType=xml"},
    {"nombre": "El Mostrador - Mercados",
     "feed_url": "https://www.elmostrador.cl/categoria/mercados/feed/"},
    {"nombre": "Contxto", "feed_url": "https://contxto.com/feed/"},
    {"nombre": "Startupeable", "feed_url": "https://startupeable.com/feed/"},
    {"nombre": "LatamList", "feed_url": "https://latamlist.com/feed/"},
    # Orientadas a Mundo
    {"nombre": "TechCrunch - Startups",
     "feed_url": "https://techcrunch.com/category/startups/feed/"},
    {"nombre": "Sifted", "feed_url": "https://sifted.eu/feed"},
    {"nombre": "Crunchbase News", "feed_url": "https://news.crunchbase.com/feed/"},
    {"nombre": "The Next Web", "feed_url": "https://thenextweb.com/feed"},
]
```

- [ ] **Step 2: Escribir los tests que fallan**

Crear `tests/test_run.py`:

```python
from datetime import datetime, timezone

import db
from scraper import run
from scraper.fetch import FeedItem


FUENTE = {"nombre": "Fuente Test", "feed_url": "https://ejemplo.com/feed"}


def item(url, titulo="Titular"):
    return FeedItem(titulo=titulo, url=url, extracto="Extracto de prueba",
                    fecha=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc))


def preparar(monkeypatch, tmp_path, items, seccion="chile"):
    conn = db.get_connection(tmp_path / "test.db")
    monkeypatch.setattr(run.fetch, "fetch_feed", lambda url: items)
    monkeypatch.setattr(run.fetch, "filter_recent", lambda items, **kw: items)
    monkeypatch.setattr(run.fetch, "fetch_article_text", lambda url: "Texto completo.")
    monkeypatch.setattr(run.classify, "classify",
                        lambda t, e, client=None: seccion)
    monkeypatch.setattr(run.summarize, "summarize",
                        lambda t, x, f, client=None: {"titulo": "Nuestro titular",
                                                      "resumen": "Nuestro resumen."})
    return conn


def test_guarda_articulo_nuevo(monkeypatch, tmp_path):
    conn = preparar(monkeypatch, tmp_path, [item("https://ejemplo.com/a")])
    assert run.process_source(conn, client=None, source=FUENTE) == 1
    fila = db.list_articles(conn)[0]
    assert fila["titulo"] == "Nuestro titular"
    assert fila["seccion"] == "chile"
    assert fila["fuente"] == "Fuente Test"


def test_no_duplica_articulos(monkeypatch, tmp_path):
    conn = preparar(monkeypatch, tmp_path, [item("https://ejemplo.com/a")])
    run.process_source(conn, client=None, source=FUENTE)
    assert run.process_source(conn, client=None, source=FUENTE) == 0


def test_descarta_lo_que_no_es_startup(monkeypatch, tmp_path):
    conn = preparar(monkeypatch, tmp_path, [item("https://ejemplo.com/a")],
                    seccion=None)
    assert run.process_source(conn, client=None, source=FUENTE) == 0
    assert db.list_articles(conn) == []


def test_error_en_un_item_no_aborta_el_resto(monkeypatch, tmp_path):
    conn = preparar(monkeypatch, tmp_path,
                    [item("https://ejemplo.com/a"), item("https://ejemplo.com/b")])

    def resumen_con_falla(t, x, f, client=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(run.summarize, "summarize", resumen_con_falla)
    # todos los ítems fallan al resumir, pero la corrida no lanza excepción
    assert run.process_source(conn, client=None, source=FUENTE) == 0


def test_usa_extracto_si_no_hay_texto_completo(monkeypatch, tmp_path):
    conn = preparar(monkeypatch, tmp_path, [item("https://ejemplo.com/a")])
    monkeypatch.setattr(run.fetch, "fetch_article_text", lambda url: None)
    capturado = {}

    def capturar(t, texto, f, client=None):
        capturado["texto"] = texto
        return {"titulo": "T", "resumen": "R"}

    monkeypatch.setattr(run.summarize, "summarize", capturar)
    run.process_source(conn, client=None, source=FUENTE)
    assert capturado["texto"] == "Extracto de prueba"
```

- [ ] **Step 3: Verificar que fallan**

Run: `python -m pytest tests/test_run.py -q`
Expected: FAIL/ERROR con `ImportError`/`ModuleNotFoundError` sobre `scraper.run`

- [ ] **Step 4: Implementar `scraper/run.py`**

```python
"""Corrida diaria del scraper: python -m scraper.run"""
import logging
from datetime import datetime, timezone

import anthropic

import db
from scraper import classify, fetch, summarize
from scraper.sources import SOURCES

log = logging.getLogger("scraper")


def process_item(conn, client, source, item):
    """Procesa un candidato; True si quedó guardado como publicado."""
    if db.article_exists(conn, item.url):
        return False
    seccion = classify.classify(item.titulo, item.extracto, client=client)
    if seccion is None:
        return False
    texto = None
    try:
        texto = fetch.fetch_article_text(item.url)
    except Exception:
        log.warning("No se pudo descargar %s; se usará el extracto", item.url)
    if not texto:
        texto = item.extracto
    resultado = summarize.summarize(item.titulo, texto, source["nombre"],
                                    client=client)
    if resultado is None:
        log.warning("Resumen inválido para %s; se salta", item.url)
        return False
    db.insert_article(
        conn,
        url_original=item.url,
        fuente=source["nombre"],
        titulo=resultado["titulo"],
        resumen=resultado["resumen"],
        seccion=seccion,
        fecha_publicacion=item.fecha.date().isoformat(),
        fecha_scrapeo=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return True


def process_source(conn, client, source):
    items = fetch.filter_recent(fetch.fetch_feed(source["feed_url"]))
    guardados = 0
    for item in items:
        try:
            if process_item(conn, client, source, item):
                guardados += 1
        except Exception:
            log.exception("Error procesando %s", item.url)
    return guardados


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    conn = db.get_connection()
    client = anthropic.Anthropic()
    total = 0
    for source in SOURCES:
        try:
            n = process_source(conn, client, source)
            log.info("%s: %d noticias nuevas", source["nombre"], n)
            total += n
        except Exception:
            log.exception("Fuente caída, se continúa: %s", source["nombre"])
    log.info("Corrida completa: %d noticias nuevas en total", total)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Verificar que pasan (y que nada se rompió)**

Run: `python -m pytest -q`
Expected: todos los tests del proyecto en verde (los 5 de esta task incluidos)

- [ ] **Step 6: Commit**

```powershell
git add scraper/sources.py scraper/run.py tests/test_run.py
git commit -m "feat: orquestador del scraper diario con fuentes RSS"
```

---

### Task 6: Sitio web (FastAPI + Jinja2 + estilos)

**Files:**
- Create: `app/__init__.py` (vacío), `app/main.py`, `app/templates/base.html`, `app/templates/home.html`, `app/templates/section.html`, `app/templates/_card.html`, `app/static/style.css`, `app/static/logo.png` (copiado de `assets/logo.png`), `tests/test_web.py`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `db.get_connection()` (resuelve la ruta vía env `DIARIO_DB_PATH`), `db.list_articles(conn, seccion, limit)`.
- Produces: app FastAPI `app.main:app` con rutas `GET /` (portada, 10 por sección), `GET /chile` y `GET /mundo` (30 por sección).

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_web.py`:

```python
from fastapi.testclient import TestClient

import db


def cliente_con_datos(tmp_path, monkeypatch):
    monkeypatch.setenv("DIARIO_DB_PATH", str(tmp_path / "test.db"))
    conn = db.get_connection()
    db.insert_article(conn, url_original="https://ej.cl/1", fuente="Ejemplo CL",
                      titulo="Titular chileno", resumen="Resumen chileno.",
                      seccion="chile", fecha_publicacion="2026-08-03",
                      fecha_scrapeo="2026-08-03T10:00:00")
    db.insert_article(conn, url_original="https://ej.com/2", fuente="Ejemplo EN",
                      titulo="Titular mundial", resumen="Resumen mundial.",
                      seccion="mundo", fecha_publicacion="2026-08-03",
                      fecha_scrapeo="2026-08-03T10:00:00")
    conn.close()
    from app.main import app
    return TestClient(app)


def test_portada_muestra_ambas_secciones(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/")
    assert r.status_code == 200
    assert "Copper Valley Diario" in r.text
    assert "Titular chileno" in r.text
    assert "Titular mundial" in r.text


def test_seccion_chile_solo_muestra_chile(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/chile")
    assert r.status_code == 200
    assert "Titular chileno" in r.text
    assert "Titular mundial" not in r.text


def test_seccion_mundo_solo_muestra_mundo(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/mundo")
    assert r.status_code == 200
    assert "Titular mundial" in r.text
    assert "Titular chileno" not in r.text


def test_tarjeta_enlaza_a_la_fuente(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/chile")
    assert 'href="https://ej.cl/1"' in r.text
    assert "Ejemplo CL" in r.text
```

- [ ] **Step 2: Verificar que fallan**

Run: `python -m pytest tests/test_web.py -q`
Expected: FAIL/ERROR con `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Copiar el logo e implementar la app**

```powershell
New-Item -ItemType Directory -Force app\static, app\templates | Out-Null
Copy-Item assets\logo.png app\static\logo.png
```

Crear `app/__init__.py` vacío y `app/main.py`:

```python
"""Web de Copper Valley Diario: solo lee de SQLite."""
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db

BASE = Path(__file__).parent
app = FastAPI(title="Copper Valley Diario")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_hoy():
    hoy = date.today()
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def get_db():
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.get("/")
def portada(request: Request, conn=Depends(get_db)):
    return templates.TemplateResponse(request, "home.html", {
        "chile": db.list_articles(conn, "chile", limit=10),
        "mundo": db.list_articles(conn, "mundo", limit=10),
        "fecha_hoy": fecha_hoy(),
    })


@app.get("/chile")
def seccion_chile(request: Request, conn=Depends(get_db)):
    return templates.TemplateResponse(request, "section.html", {
        "titulo_seccion": "Startups Chile",
        "articulos": db.list_articles(conn, "chile", limit=30),
    })


@app.get("/mundo")
def seccion_mundo(request: Request, conn=Depends(get_db)):
    return templates.TemplateResponse(request, "section.html", {
        "titulo_seccion": "Startups Mundo",
        "articulos": db.list_articles(conn, "mundo", limit=30),
    })
```

- [ ] **Step 4: Crear las plantillas**

`app/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Copper Valley Diario{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="cabecera">
    <a href="/"><img src="/static/logo.png" alt="Copper Valley Diario" class="logo"></a>
    <nav>
      <a href="/">Portada</a>
      <a href="/chile">Startups Chile</a>
      <a href="/mundo">Startups Mundo</a>
    </nav>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
  <footer>
    <p>Una publicación de Copper Valley · Resúmenes propios que citan y
    enlazan siempre a su fuente original.</p>
  </footer>
</body>
</html>
```

`app/templates/_card.html`:

```html
<article class="tarjeta">
  <span class="etiqueta etiqueta-{{ articulo['seccion'] }}">
    {{ 'Startups Chile' if articulo['seccion'] == 'chile' else 'Startups Mundo' }}
  </span>
  <h2>{{ articulo['titulo'] }}</h2>
  <p class="resumen">{{ articulo['resumen'] }}</p>
  <p class="fuente">Fuente:
    <a href="{{ articulo['url_original'] }}" target="_blank" rel="noopener">{{ articulo['fuente'] }}</a>
    · {{ articulo['fecha_publicacion'] }}</p>
</article>
```

`app/templates/home.html`:

```html
{% extends "base.html" %}
{% block content %}
<p class="fecha-hoy">{{ fecha_hoy }}</p>
<div class="portada">
  <section>
    <h1>Startups Chile</h1>
    {% for articulo in chile %}{% include "_card.html" %}
    {% else %}<p class="vacio">Aún no hay noticias en esta sección.</p>{% endfor %}
  </section>
  <section>
    <h1>Startups Mundo</h1>
    {% for articulo in mundo %}{% include "_card.html" %}
    {% else %}<p class="vacio">Aún no hay noticias en esta sección.</p>{% endfor %}
  </section>
</div>
{% endblock %}
```

`app/templates/section.html`:

```html
{% extends "base.html" %}
{% block title %}{{ titulo_seccion }} — Copper Valley Diario{% endblock %}
{% block content %}
<h1>{{ titulo_seccion }}</h1>
{% for articulo in articulos %}{% include "_card.html" %}
{% else %}<p class="vacio">Aún no hay noticias en esta sección.</p>{% endfor %}
{% endblock %}
```

- [ ] **Step 5: Crear `app/static/style.css`** (paleta del spec, serif de diario)

```css
:root {
  --marfil: #F4F1ED;
  --azul-marino: #0F1D2D;
  --azul-pizarra: #334155;
  --gris-acero: #8A9199;
  --cobre: #B87333;
  --cobre-claro: #D4A373;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--marfil);
  color: var(--azul-pizarra);
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.6;
}

.cabecera {
  text-align: center;
  padding: 1.5rem 1rem 0.5rem;
  border-bottom: 3px double var(--azul-marino);
}

.logo { max-height: 110px; }

nav { margin: 0.75rem 0; }

nav a {
  color: var(--azul-marino);
  text-decoration: none;
  margin: 0 1rem;
  font-variant: small-caps;
  letter-spacing: 0.08em;
}

nav a:hover { color: var(--cobre); }

main { max-width: 1000px; margin: 0 auto; padding: 1rem; }

.fecha-hoy {
  text-align: center;
  color: var(--gris-acero);
  font-style: italic;
  margin-top: 0;
}

.portada {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

@media (max-width: 760px) {
  .portada { grid-template-columns: 1fr; }
}

h1 {
  color: var(--azul-marino);
  border-bottom: 2px solid var(--cobre);
  padding-bottom: 0.3rem;
}

.tarjeta {
  background: #fff;
  border: 1px solid #e3ded7;
  border-top: 3px solid var(--cobre);
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.tarjeta h2 {
  color: var(--azul-marino);
  margin: 0.4rem 0;
  font-size: 1.25rem;
}

.etiqueta {
  font-size: 0.7rem;
  font-family: Arial, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #fff;
  background: var(--azul-pizarra);
  padding: 0.15rem 0.5rem;
}

.etiqueta-chile { background: var(--cobre); }

.resumen { white-space: pre-line; }

.fuente { color: var(--gris-acero); font-size: 0.85rem; }

.fuente a { color: var(--cobre); }

.vacio { color: var(--gris-acero); font-style: italic; }

footer {
  text-align: center;
  color: var(--gris-acero);
  font-size: 0.85rem;
  border-top: 1px solid var(--gris-acero);
  margin-top: 2rem;
  padding: 1rem;
}
```

- [ ] **Step 6: Verificar que pasan (proyecto completo)**

Run: `python -m pytest -q`
Expected: todos los tests en verde (los 4 de esta task incluidos)

- [ ] **Step 7: Vistazo manual**

```powershell
.venv\Scripts\uvicorn.exe app.main:app --port 8000
```

Abrir http://127.0.0.1:8000 — debe verse cabecera con logo, secciones vacías con el mensaje "Aún no hay noticias" (la BD real todavía no tiene datos). Detener con Ctrl+C.

- [ ] **Step 8: Commit**

```powershell
git add app/ tests/test_web.py
git commit -m "feat: sitio web con portada y secciones Chile/Mundo"
```

---

### Task 7: Puesta en marcha — validar fuentes reales, primera corrida y agenda diaria

Esta task toca la red y la API real; requiere `ANTHROPIC_API_KEY` del usuario.

**Files:**
- Create: `scripts/validar_fuentes.py`, `README.md`
- Modify: `scraper/sources.py` (reemplazar URLs que fallen)

**Interfaces:**
- Consumes: `SOURCES`, `scraper.fetch.fetch_feed`, `scraper.fetch.filter_recent`, `scraper.run.main`.

- [ ] **Step 1: Crear `scripts/validar_fuentes.py`**

```python
"""Prueba cada feed de sources.py contra la red e informa su estado.

Uso: python -m scripts.validar_fuentes  (crear también scripts/__init__.py vacío)
"""
from scraper.fetch import fetch_feed, filter_recent
from scraper.sources import SOURCES


def main():
    for source in SOURCES:
        try:
            items = fetch_feed(source["feed_url"])
            recientes = filter_recent(items)
            estado = "OK   " if items else "VACIO"
            print(f"{estado} {source['nombre']}: "
                  f"{len(items)} items, {len(recientes)} recientes")
        except Exception as e:
            print(f"FALLO {source['nombre']}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Validar y corregir fuentes**

Run: `python -m scripts.validar_fuentes`

Para cada fuente `FALLO` o `VACIO`: buscar la URL RSS correcta del medio (probar `/feed/`, `/rss`, o buscar "RSS" en el sitio) y actualizar `scraper/sources.py`. Si un medio no tiene RSS utilizable, reemplazarlo por otro equivalente de la misma categoría (Chile/LATAM o Mundo) y anotarlo en el commit. Repetir hasta que todas las fuentes den `OK`.

- [ ] **Step 3: Primera corrida real del scraper**

```powershell
$env:ANTHROPIC_API_KEY = "<la key del usuario — pedírsela, no inventarla>"
python -m scraper.run
```

Expected: log por fuente con "N noticias nuevas" y al final "Corrida completa". Verificar contenido:

```powershell
python -c "import db; conn = db.get_connection(); print(len(db.list_articles(conn, limit=100)), 'articulos')"
```

Expected: > 0 artículos. Levantar `uvicorn app.main:app` y revisar visualmente portada, /chile y /mundo con noticias reales.

- [ ] **Step 4: Agendar la corrida diaria (7:00 AM)**

Guardar la key como variable de usuario de Windows (persistente) y crear la tarea:

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $env:ANTHROPIC_API_KEY, "User")
schtasks /Create /SC DAILY /ST 07:00 /TN "CopperValleyDiario" /TR "cmd /c cd /d C:\Users\vpareja\Desktop\Ribs\diario-startapero && .venv\Scripts\python.exe -m scraper.run"
```

Verificar con `schtasks /Query /TN "CopperValleyDiario"`.

- [ ] **Step 5: Escribir `README.md`**

```markdown
# Copper Valley Diario

Diario web de noticias de startups y emprendimiento, con dos secciones:
**Startups Chile** y **Startups Mundo**. Un scraper diario lee fuentes RSS,
filtra y clasifica cada noticia con Claude y publica un titular y resumen
propios que citan y enlazan la fuente original.

## Cómo correr

```powershell
# 1. Instalar
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Scraper (requiere ANTHROPIC_API_KEY en el entorno)
.venv\Scripts\python.exe -m scraper.run

# 3. Web
.venv\Scripts\uvicorn.exe app.main:app --port 8000
```

La corrida diaria está agendada a las 7:00 con el Programador de tareas de
Windows (tarea `CopperValleyDiario`).

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Operación

- Despublicar una nota: `UPDATE articles SET estado = 'hidden' WHERE url_original = '...'`
- Validar fuentes RSS: `python -m scripts.validar_fuentes`
- Base de datos: `diario.db` (SQLite) en la raíz del repo.
```

- [ ] **Step 6: Commit final**

```powershell
python -m pytest -q   # todo en verde antes de commitear
git add scripts/ scraper/sources.py README.md
git commit -m "feat: validación de fuentes, primera edición y agenda diaria"
```
