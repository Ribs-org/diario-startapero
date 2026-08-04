from scraper.classify import classify
from tests.fakes import FakeClient


def test_clasifica_chile():
    fake = FakeClient("chile")
    assert classify("Startup chilena levanta ronda", "extracto", client=fake) == "chile"
    assert "Startup chilena levanta ronda" in fake.kwargs["messages"][0]["content"]


def test_clasifica_mundo():
    assert classify("YC anuncia batch", "extracto", client=FakeClient("mundo")) == "mundo"


def test_descartar_retorna_none():
    assert classify("Resultados del fútbol", "extracto", client=FakeClient("descartar")) is None


def test_respuesta_inesperada_retorna_none():
    assert classify("Titular", "extracto", client=FakeClient("no estoy seguro")) is None


def test_normaliza_mayusculas_y_espacios():
    assert classify("Titular", "extracto", client=FakeClient("  Chile \n")) == "chile"
