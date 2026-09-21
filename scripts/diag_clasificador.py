"""Diagnóstico temporal: qué traen los feeds Chile/LATAM y cómo responde el clasificador."""
import anthropic

from scraper import classify, fetch
from scraper.sources import SOURCES

CHILE_LATAM = ["La Tercera - Pulso", "Fayerwayer", "Contxto", "Startupeable", "LatamList"]

client = anthropic.Anthropic()

for source in SOURCES:
    if source["nombre"] not in CHILE_LATAM:
        continue
    try:
        items = fetch.filter_recent(fetch.fetch_feed(source["feed_url"]))
    except Exception as e:
        print(f"\n=== {source['nombre']}: ERROR {type(e).__name__}: {e}")
        continue
    print(f"\n=== {source['nombre']}: {len(items)} items en las últimas 48 h")
    for item in items[:6]:
        respuesta = client.messages.create(
            model=classify.MODEL,
            max_tokens=10,
            system=classify.SYSTEM,
            messages=[{"role": "user",
                       "content": f"Titular: {item.titulo}\nExtracto: {item.extracto}"}],
        )
        bruto = respuesta.content[0].text.strip()
        print(f"  [{bruto:>10}] {item.titulo[:90]}")
