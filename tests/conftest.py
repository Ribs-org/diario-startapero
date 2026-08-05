import pytest


@pytest.fixture(autouse=True)
def sin_turso(monkeypatch):
    """Los tests siempre usan SQLite local, aunque el entorno tenga Turso."""
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
