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
