import pytest
from fastapi.testclient import TestClient

import db
from app.main import app, get_db

JSON = {"accept": "application/json"}


def make_conn(tmp_path):
    return db.get_connection(tmp_path / "test.db")


@pytest.fixture
def conn(tmp_path):
    """Cada request abre su conexión, como en producción; el test usa la suya.

    TestClient corre la app en otro hilo y sqlite3 no deja compartir una
    conexión entre hilos.
    """
    ruta = tmp_path / "test.db"

    def db_de_prueba():
        conexion = db.get_connection(ruta)
        try:
            yield conexion
        finally:
            conexion.close()

    app.dependency_overrides[get_db] = db_de_prueba
    conexion = db.get_connection(ruta)
    yield conexion
    conexion.close()
    app.dependency_overrides.clear()


@pytest.fixture
def cliente(conn):
    return TestClient(app)


def enviar(cliente, *, nombre="Vicente", email="vicente@ej.cl", sitio_web="",
           origen="pagina", headers=None):
    return cliente.post(
        "/suscribirse",
        data={"nombre": nombre, "email": email, "sitio_web": sitio_web,
              "origen": origen},
        headers=headers or {},
    )


def alta(conn, email, nombre="Vicente", origen="pagina"):
    db.insert_suscriptor(
        conn,
        nombre=nombre,
        email=email,
        fecha_alta="2026-08-07T10:00:00",
        origen=origen,
    )


def test_alta_y_listado(tmp_path):
    conn = make_conn(tmp_path)
    alta(conn, "vicente@ej.cl", nombre="Vicente", origen="modal")
    filas = db.list_suscriptores(conn)
    assert len(filas) == 1
    assert filas[0]["nombre"] == "Vicente"
    assert filas[0]["email"] == "vicente@ej.cl"
    assert filas[0]["origen"] == "modal"


def test_email_duplicado_no_duplica_ni_lanza(tmp_path):
    conn = make_conn(tmp_path)
    alta(conn, "vicente@ej.cl")
    alta(conn, "vicente@ej.cl", nombre="Otro Nombre")
    filas = db.list_suscriptores(conn)
    assert len(filas) == 1
    assert filas[0]["nombre"] == "Vicente"


def test_email_se_normaliza_a_minusculas_y_sin_espacios(tmp_path):
    conn = make_conn(tmp_path)
    alta(conn, "  Vicente@Ej.CL  ")
    filas = db.list_suscriptores(conn)
    assert filas[0]["email"] == "vicente@ej.cl"


def test_mayusculas_distintas_son_el_mismo_suscriptor(tmp_path):
    conn = make_conn(tmp_path)
    alta(conn, "vicente@ej.cl")
    alta(conn, "VICENTE@EJ.CL")
    assert len(db.list_suscriptores(conn)) == 1


def test_listado_devuelve_el_mas_reciente_primero(tmp_path):
    conn = make_conn(tmp_path)
    alta(conn, "uno@ej.cl", nombre="Uno")
    alta(conn, "dos@ej.cl", nombre="Dos")
    assert [f["nombre"] for f in db.list_suscriptores(conn)] == ["Dos", "Uno"]


def test_get_suscribirse_muestra_el_formulario(cliente):
    r = cliente.get("/suscribirse")
    assert r.status_code == 200
    assert 'name="email"' in r.text


def test_el_boton_esta_en_la_navegacion(cliente):
    assert 'href="/suscribirse"' in cliente.get("/").text


def test_alta_por_json_guarda_y_responde_ok(cliente, conn):
    r = enviar(cliente, nombre="Vicente", email="vicente@ej.cl",
               origen="modal", headers=JSON)
    assert r.status_code == 200
    assert r.json()["ok"] is True
    filas = db.list_suscriptores(conn)
    assert [(f["nombre"], f["email"], f["origen"]) for f in filas] == [
        ("Vicente", "vicente@ej.cl", "modal")]


def test_alta_por_formulario_devuelve_html_con_el_mensaje(cliente, conn):
    r = enviar(cliente)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert len(db.list_suscriptores(conn)) == 1


def test_honeypot_relleno_responde_ok_pero_no_guarda(cliente, conn):
    r = enviar(cliente, sitio_web="http://spam.example", headers=JSON)
    assert r.json()["ok"] is True
    assert db.list_suscriptores(conn) == []


@pytest.mark.parametrize("email", ["sin-arroba", "a@", "@ej.cl", "", "a@b",
                                   "con espacio@ej.cl", "x" * 250 + "@ej.cl"])
def test_email_invalido_no_guarda_y_responde_error(cliente, conn, email):
    r = enviar(cliente, email=email, headers=JSON)
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert db.list_suscriptores(conn) == []


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 81])
def test_nombre_invalido_no_guarda_y_responde_error(cliente, conn, nombre):
    r = enviar(cliente, nombre=nombre, headers=JSON)
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert db.list_suscriptores(conn) == []


def test_duplicado_responde_ok_y_no_duplica(cliente, conn):
    enviar(cliente, email="vicente@ej.cl", headers=JSON)
    r = enviar(cliente, email="VICENTE@ej.cl", nombre="Otro", headers=JSON)
    assert r.json()["ok"] is True
    assert len(db.list_suscriptores(conn)) == 1


def test_origen_desconocido_se_guarda_como_pagina(cliente, conn):
    enviar(cliente, origen="inventado", headers=JSON)
    assert db.list_suscriptores(conn)[0]["origen"] == "pagina"


def test_la_fecha_de_alta_queda_registrada(cliente, conn):
    enviar(cliente, headers=JSON)
    assert db.list_suscriptores(conn)[0]["fecha_alta"].startswith("20")
