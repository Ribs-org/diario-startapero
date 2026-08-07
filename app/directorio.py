"""Piezas comunes de los directorios estáticos del diario.

Financiamiento y Comunidades son la misma ficha con distinto contenido: un
logo cliqueable, un nombre, una linea de contexto y un enlace al sitio de la
institucion. Este modulo resuelve los logos que `scripts/descargar_logos.py`
dejo en `app/static/logos/`; las listas viven en `app.financiamiento` y
`app.comunidades`.
"""
from pathlib import Path

DIR_LOGOS = Path(__file__).parent / "static" / "logos"


def ruta_logo(slug):
    """URL del logo descargado, sin importar su extensión. None si no hay."""
    for archivo in sorted(DIR_LOGOS.glob(f"{slug}.*")):
        return f"/static/logos/{archivo.name}"
    return None


def por_categoria(entradas, categoria):
    """Entradas de la categoría, cada una con su `logo` ya resuelto."""
    return [dict(entrada, logo=ruta_logo(entrada["slug"]))
            for entrada in entradas if entrada["categoria"] == categoria]
