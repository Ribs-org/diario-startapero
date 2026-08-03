"""Corrida diaria del scraper: python -m scraper.run"""
import logging
from datetime import datetime, timezone

import anthropic

import db
from scraper import classify, fetch, summarize
from scraper.sources import SOURCES

log = logging.getLogger("scraper")


def process_item(conn, client, source, item):
    """Procesa un candidato; True si quedó guardado como publicado."""
    if db.article_exists(conn, item.url):
        return False
    seccion = classify.classify(item.titulo, item.extracto, client=client)
    if seccion is None:
        return False
    texto = None
    try:
        texto = fetch.fetch_article_text(item.url)
    except Exception:
        log.warning("No se pudo descargar %s; se usará el extracto", item.url)
    if not texto:
        texto = item.extracto
    resultado = summarize.summarize(item.titulo, texto, source["nombre"],
                                    client=client)
    if resultado is None:
        log.warning("Resumen inválido para %s; se salta", item.url)
        return False
    db.insert_article(
        conn,
        url_original=item.url,
        fuente=source["nombre"],
        titulo=resultado["titulo"],
        resumen=resultado["resumen"],
        seccion=seccion,
        fecha_publicacion=item.fecha.date().isoformat(),
        fecha_scrapeo=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return True


def process_source(conn, client, source):
    items = fetch.filter_recent(fetch.fetch_feed(source["feed_url"]))
    guardados = 0
    for item in items:
        try:
            if process_item(conn, client, source, item):
                guardados += 1
        except Exception:
            log.exception("Error procesando %s", item.url)
    return guardados


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    conn = db.get_connection()
    client = anthropic.Anthropic()
    total = 0
    for source in SOURCES:
        try:
            n = process_source(conn, client, source)
            log.info("%s: %d noticias nuevas", source["nombre"], n)
            total += n
        except Exception:
            log.exception("Fuente caída, se continúa: %s", source["nombre"])
    log.info("Corrida completa: %d noticias nuevas en total", total)


if __name__ == "__main__":
    main()
