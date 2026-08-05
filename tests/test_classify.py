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


def test_incluye_el_nombre_de_la_fuente_en_el_prompt():
    fake = FakeClient("mundo")
    classify("Titular", "extracto", fuente="LatamList - Chile", client=fake)
    assert "LatamList - Chile" in fake.kwargs["messages"][0]["content"]


def test_marca_las_fuentes_con_foco_chileno():
    """Sin esta señal, 'Fracttal raises $35M' (startup chilena) cae en mundo."""
    fake = FakeClient("chile")
    classify("Fracttal raises $35M", "", fuente="LatamList - Chile", foco="chile",
             client=fake)
    contenido = fake.kwargs["messages"][0]["content"]
    assert "chileno" in contenido.lower() or "Chile" in contenido


def test_sin_foco_no_afirma_chilenidad():
    fake = FakeClient("mundo")
    classify("Startup brasileña levanta ronda", "", fuente="LatamList", client=fake)
    contenido = fake.kwargs["messages"][0]["content"]
    assert "cubre exclusivamente" not in contenido


def test_el_prompt_del_sistema_explica_que_las_chilenas_cuentan_sin_decir_chile():
    fake = FakeClient("chile")
    classify("Titular", "extracto", client=fake)
    assert "chilena" in fake.kwargs["system"].lower()
