from scraper.sources import SOURCES, fuentes_con_foco


def test_toda_fuente_tiene_nombre_y_feed():
    for s in SOURCES:
        assert s["nombre"] and s["feed_url"].startswith("https://")


def test_no_hay_feeds_duplicados():
    urls = [s["feed_url"] for s in SOURCES]
    assert len(urls) == len(set(urls))


def test_no_hay_nombres_duplicados():
    nombres = [s["nombre"] for s in SOURCES]
    assert len(nombres) == len(set(nombres))


def test_existen_fuentes_dedicadas_a_chile():
    """La sección Chile se moría porque ninguna fuente cubría startups chilenas."""
    assert len(fuentes_con_foco("chile")) >= 2


def test_startupeable_fue_retirada():
    """Su feed lleva desde 2025-12-30 sin publicar: aportaba 0 noticias."""
    assert all(s["nombre"] != "Startupeable" for s in SOURCES)


def test_el_foco_declarado_es_valido():
    for s in SOURCES:
        assert s.get("foco") in (None, "chile", "latam", "mundo")


def test_las_fuentes_de_bajo_volumen_miran_mas_atras():
    """LatamList - Chile publica ~1 vez por semana: con 48 h de ventana no aporta
    casi nunca. Ampliarla no cuesta API (el dedupe por URL corre antes de
    clasificar) ni desborda: esos feeds traen 10 items en total."""
    por_nombre = {s["nombre"]: s for s in SOURCES}
    assert por_nombre["LatamList - Chile"]["dias"] >= 14
    assert por_nombre["Startups Latam"]["dias"] >= 7
    assert por_nombre["Contxto"]["dias"] >= 7


def test_las_fuentes_de_alto_volumen_mantienen_ventana_corta():
    """La Tercera - Pulso trae ~53 items cada 48 h y The Next Web publica a
    diario: ampliarles la ventana dispararía el costo de clasificación."""
    por_nombre = {s["nombre"]: s for s in SOURCES}
    assert por_nombre["La Tercera - Pulso"].get("dias", 2) <= 2
    for s in fuentes_con_foco("mundo"):
        assert s.get("dias", 2) <= 3
