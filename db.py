"""Acceso a datos de Copper Valley Diario (SQLite local o Turso vía HTTP)."""
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
    conn = _TursoConn(
        os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://") + "/v2/pipeline",
        os.environ["TURSO_AUTH_TOKEN"],
    )
    conn.execute(SCHEMA)
    return conn


def _a_hrana(valor):
    if valor is None:
        return {"type": "null", "value": None}
    if isinstance(valor, bool):
        return {"type": "integer", "value": str(int(valor))}
    if isinstance(valor, int):
        return {"type": "integer", "value": str(valor)}
    if isinstance(valor, float):
        return {"type": "float", "value": valor}
    return {"type": "text", "value": str(valor)}


def _de_hrana(celda):
    tipo = celda["type"]
    if tipo == "null":
        return None
    if tipo == "integer":
        return int(celda["value"])
    if tipo == "float":
        return float(celda["value"])
    return celda["value"]


class TursoError(Exception):
    """Error devuelto por Turso al ejecutar una sentencia."""


class _Resultado:
    def __init__(self, res):
        self.description = [(c["name"],) for c in res["cols"]]
        self._filas = [tuple(_de_hrana(c) for c in fila) for fila in res["rows"]]

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return self._filas


class _TursoConn:
    """Superficie mínima de sqlite3.Connection sobre Turso v2/pipeline (autocommit)."""

    def __init__(self, url, token):
        self._url = url
        self._token = token

    def execute(self, sql, params=()):
        import httpx  # import perezoso: solo se necesita con Turso
        stmt = {"sql": sql, "args": [_a_hrana(p) for p in params]}
        r = httpx.post(
            self._url,
            json={"requests": [{"type": "execute", "stmt": stmt}, {"type": "close"}]},
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=30,
        )
        r.raise_for_status()
        resultado = r.json()["results"][0]
        if resultado["type"] == "error":
            raise TursoError(resultado["error"]["message"])
        return _Resultado(resultado["response"]["result"])

    def commit(self):
        pass

    def close(self):
        pass


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
    cur = conn.execute(query, params)
    columnas = [d[0] for d in cur.description]
    return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
