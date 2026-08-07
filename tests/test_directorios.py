"""Reglas comunes a los dos directorios estáticos: Financiamiento y Comunidades."""
import pytest

from app import comunidades, financiamiento
from app.directorio import DIR_LOGOS, ruta_logo

CATALOGOS = {
    "financiamiento": financiamiento.INSTITUCIONES,
    "comunidades": comunidades.COMUNIDADES,
}
TODAS = financiamiento.INSTITUCIONES + comunidades.COMUNIDADES

CAMPOS = {"slug", "nombre", "dominio", "url", "categoria", "tipo", "detalle",
          "descripcion", "monograma"}

# Hoy todas las fichas tienen logo descargado. Si alguna aparece acá, es que
# se cayó un logo que sí teníamos (o que entró una ficha sin correr el script).
SIN_LOGO = set()


@pytest.mark.parametrize("nombre", CATALOGOS)
def test_cada_catalogo_tiene_entre_10_y_20_fichas(nombre):
    assert 10 <= len(CATALOGOS[nombre]) <= 20


def test_los_slugs_no_se_repiten_entre_catalogos():
    slugs = [f["slug"] for f in TODAS]
    assert len(slugs) == len(set(slugs))


def test_cada_ficha_tiene_los_campos_obligatorios():
    for ficha in TODAS:
        assert not CAMPOS - set(ficha), f"{ficha.get('slug')}: {CAMPOS - set(ficha)}"


def test_las_urls_son_https_y_del_dominio_de_la_ficha():
    for ficha in TODAS:
        assert ficha["url"].startswith("https://"), ficha["slug"]
        assert ficha["dominio"] in ficha["url"], ficha["slug"]


def test_las_categorias_cubren_todas_las_fichas():
    assert (len(financiamiento.por_categoria("chile"))
            + len(financiamiento.por_categoria("internacional"))
            == len(financiamiento.INSTITUCIONES))
    assert (len(comunidades.por_categoria("universitaria"))
            + len(comunidades.por_categoria("red"))
            == len(comunidades.COMUNIDADES))


def test_solo_las_fichas_conocidas_se_quedan_sin_logo():
    sin_logo = {f["slug"] for f in TODAS if not ruta_logo(f["slug"])}
    assert sin_logo == SIN_LOGO, ("cambió qué fichas tienen logo; correr "
                                  "python -m scripts.descargar_logos")


def test_una_ficha_sin_logo_cae_al_monograma():
    assert ruta_logo("institucion-que-no-existe") is None


def test_no_hay_logos_huerfanos_en_static():
    slugs = {f["slug"] for f in TODAS}
    huerfanos = [a.name for a in DIR_LOGOS.glob("*.*") if a.stem not in slugs]
    assert not huerfanos, f"logos sin ficha: {huerfanos}"
