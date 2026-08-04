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
