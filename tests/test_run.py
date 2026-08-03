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
