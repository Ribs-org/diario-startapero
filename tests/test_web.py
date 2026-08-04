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
