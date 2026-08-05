"""Migración de un solo uso: sube el diario.db local a Turso.

Uso (PowerShell, con TURSO_DATABASE_URL y TURSO_AUTH_TOKEN en el entorno):
  .venv\\Scripts\\python.exe -m scripts.migrar_a_turso
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
