from app.financiamiento import DIR_LOGOS, INSTITUCIONES, por_categoria


def test_hay_entre_10_y_20_instituciones():
    assert 10 <= len(INSTITUCIONES) <= 20


def test_los_slugs_no_se_repiten():
    slugs = [i["slug"] for i in INSTITUCIONES]
    assert len(slugs) == len(set(slugs))


def test_cada_institucion_tiene_los_campos_obligatorios():
    for inst in INSTITUCIONES:
        faltantes = {"slug", "nombre", "dominio", "url", "categoria", "tipo",
                     "etapa", "descripcion", "monograma"} - set(inst)
        assert not faltantes, f"{inst.get('slug')} sin {faltantes}"


def test_todas_las_urls_son_https_y_del_dominio_de_la_institucion():
    for inst in INSTITUCIONES:
        assert inst["url"].startswith("https://"), inst["slug"]
        assert inst["dominio"] in inst["url"], inst["slug"]


def test_hay_instituciones_chilenas_e_internacionales():
    assert por_categoria("chile")
    assert por_categoria("internacional")
    assert len(por_categoria("chile")) + len(por_categoria("internacional")) \
        == len(INSTITUCIONES)


def test_cada_institucion_resuelve_su_logo_descargado():
    sin_logo = [i["slug"] for i in por_categoria("chile") + por_categoria("internacional")
                if not i["logo"]]
    assert not sin_logo, (f"faltan logos para {sin_logo}: "
                          "correr python -m scripts.descargar_logos")


def test_no_hay_logos_huerfanos_en_static():
    slugs = {i["slug"] for i in INSTITUCIONES}
    huerfanos = [a.name for a in DIR_LOGOS.glob("*.*") if a.stem not in slugs]
    assert not huerfanos, f"logos sin institucion: {huerfanos}"
