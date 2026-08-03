from scraper.summarize import MAX_CHARS, summarize
from tests.fakes import FakeClient

JSON_OK = '{"titulo": "Titular propio", "resumen": "Párrafo uno.\\n\\nPárrafo dos."}'


def test_resumen_valido():
    resultado = summarize("Original", "Texto del artículo.", "TechCrunch",
                          client=FakeClient(JSON_OK))
    assert resultado == {"titulo": "Titular propio",
                         "resumen": "Párrafo uno.\n\nPárrafo dos."}


def test_tolera_fences_markdown():
    fake = FakeClient(f"```json\n{JSON_OK}\n```")
    assert summarize("Original", "Texto.", "Sifted", client=fake)["titulo"] == "Titular propio"


def test_json_invalido_retorna_none():
    assert summarize("Original", "Texto.", "Sifted", client=FakeClient("no es json")) is None


def test_faltan_claves_retorna_none():
    assert summarize("Original", "Texto.", "Sifted",
                     client=FakeClient('{"titulo": "Solo titular"}')) is None


def test_trunca_texto_largo():
    fake = FakeClient(JSON_OK)
    summarize("Original", "x" * 20000, "Sifted", client=fake)
    contenido = fake.kwargs["messages"][0]["content"]
    assert len(contenido) < MAX_CHARS + 500  # texto truncado + encabezado corto


def test_json_valido_pero_no_dict_retorna_none():
    # Valid JSON but not a dict (e.g., a list) should return None
    assert summarize("Original", "Texto.", "Sifted",
                     client=FakeClient('["a", "b"]')) is None
    # Also test with a string
    assert summarize("Original", "Texto.", "Sifted",
                     client=FakeClient('"algo salió mal"')) is None
