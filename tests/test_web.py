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


def test_financiamiento_lista_las_instituciones(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/financiamiento")
    assert r.status_code == 200
    assert "Platanus Ventures" in r.text
    assert "Y Combinator" in r.text
    assert 'href="https://platan.us/apply"' in r.text
    assert '<img src="/static/logos/platanus.ico"' in r.text


def test_los_logos_se_sirven_con_su_tipo_de_imagen(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    for archivo, tipo in [("impacta-vc.webp", "image/webp"),
                          ("corfo.png", "image/png"),
                          ("kaszek.svg", "image/svg+xml")]:
        r = client.get(f"/static/logos/{archivo}")
        assert r.status_code == 200, archivo
        assert r.headers["content-type"].startswith(tipo), archivo


def test_comunidades_lista_las_comunidades(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/comunidades")
    assert r.status_code == 200
    assert "Jump Chile" in r.text
    assert "Asech" in r.text
    assert 'href="https://openbeauchef.cl/"' in r.text
    assert '<img src="/static/logos/jump-chile.png"' in r.text


def test_los_directorios_estan_en_el_menu(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/")
    assert 'href="/financiamiento"' in r.text
    assert 'href="/comunidades"' in r.text


def test_el_favicon_es_el_logo_del_diario(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/")
    assert '<link rel="icon" type="image/png" href="/static/favicon.png">' in r.text
    imagen = client.get("/static/favicon.png")
    assert imagen.status_code == 200
    assert imagen.headers["content-type"].startswith("image/png")
    # los bots que lo piden en la raíz tampoco se quedan sin icono
    raiz = client.get("/favicon.ico")
    assert raiz.status_code == 200
    assert raiz.headers["content-type"].startswith("image/png")


def test_el_diario_lleva_la_firma_del_autor(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    for ruta in ["/", "/chile", "/financiamiento", "/comunidades"]:
        r = client.get(ruta)
        assert 'href="https://linktr.ee/vicente.pareja"' in r.text, ruta
        assert "Vicente Pareja" in r.text, ruta


def test_tarjeta_enlaza_a_la_fuente(tmp_path, monkeypatch):
    client = cliente_con_datos(tmp_path, monkeypatch)
    r = client.get("/chile")
    assert 'href="https://ej.cl/1"' in r.text
    assert "Ejemplo CL" in r.text
