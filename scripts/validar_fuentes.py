"""Prueba cada feed de sources.py contra la red e informa su estado.

Uso: python -m scripts.validar_fuentes
"""
from scraper.fetch import fetch_feed, filter_recent
from scraper.sources import SOURCES


def main():
    for source in SOURCES:
        try:
            items = fetch_feed(source["feed_url"])
            recientes = filter_recent(items)
            estado = "OK   " if items else "VACIO"
            print(f"{estado} {source['nombre']}: "
                  f"{len(items)} items, {len(recientes)} recientes")
        except Exception as e:
            print(f"FALLO {source['nombre']}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
