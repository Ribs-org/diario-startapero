"""Tests de la rama Turso de db.py: adaptador HTTP v2/pipeline (sin red real)."""
import httpx

import db


def respuesta_hrana(sql):
    """Arma una respuesta v2/pipeline: filas solo para SELECT."""
    if sql.strip().upper().startswith("SELECT"):
        resultado = {
            "cols": [{"name": "id"}, {"name": "titulo"}],
            "rows": [[
                {"type": "integer", "value": "1"},
                {"type": "text", "value": "Titular remoto"},
            ]],
        }
    else:
        resultado = {"cols": [], "rows": []}
    return {
        "results": [
            {"type": "ok", "response": {"type": "execute", "result": resultado}},
            {"type": "ok", "response": {"type": "close"}},
        ]
    }


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def fake_http(monkeypatch, registro):
    """Intercepta httpx.post y registra URL, auth y SQLs enviados."""

    def post(url, json=None, headers=None, timeout=None):
        registro["url"] = url
        registro["auth"] = headers["Authorization"]
        sql = json["requests"][0]["stmt"]["sql"]
        registro.setdefault("sqls", []).append(sql)
        return FakeResponse(respuesta_hrana(sql))

    monkeypatch.setattr(httpx, "post", post)


def test_usa_turso_cuando_solo_hay_credenciales(monkeypatch):
    registro = {}
    fake_http(monkeypatch, registro)
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    db.get_connection()
    assert registro["url"] == "https://ejemplo.turso.io/v2/pipeline"
    assert registro["auth"] == "Bearer token-fake"
    assert any("CREATE TABLE" in s for s in registro["sqls"])  # aplicó el schema


def test_db_path_explicito_gana_a_turso(monkeypatch, tmp_path):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection(tmp_path / "local.db")  # no debe tocar la red
    assert db.list_articles(conn) == []


def test_diario_db_path_gana_a_turso(monkeypatch, tmp_path):
    monkeypatch.setenv("DIARIO_DB_PATH", str(tmp_path / "local.db"))
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection()
    assert db.list_articles(conn) == []


def test_list_articles_devuelve_dicts_con_driver_remoto(monkeypatch):
    registro = {}
    fake_http(monkeypatch, registro)
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://ejemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-fake")
    conn = db.get_connection()
    filas = db.list_articles(conn)
    assert filas == [{"id": 1, "titulo": "Titular remoto"}]
