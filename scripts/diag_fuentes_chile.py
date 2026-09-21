"""Diagnóstico temporal: candidatos a fuentes RSS con foco en startups de Chile."""
from datetime import datetime, timezone

from scraper import fetch

CANDIDATOS = [
    ("Contxto - tag Chile", "https://contxto.com/es/tag/chile/feed/"),
    ("LatamList - tag Chile", "https://latamlist.com/tag/chile/feed/"),
    ("Startups Latam", "https://startupslatam.com/feed/"),
    ("Forbes Chile", "https://forbes.cl/feed/"),
    ("Diario Financiero", "https://www.df.cl/rss"),
    ("El Mostrador - Mercados", "https://www.elmostrador.cl/mercados/feed/"),
    ("TrendTic", "https://www.trendtic.cl/feed/"),
    ("Emol Economía", "https://www.emol.com/rss/rss.asp?canal=economia"),
]

for nombre, url in CANDIDATOS:
    try:
        items = fetch.fetch_feed(url)
    except Exception as e:
        print(f"\n=== {nombre}: ERROR {type(e).__name__}: {e}")
        continue
    ahora = datetime.now(timezone.utc)
    recientes = [i for i in items if (ahora - i.fecha).days <= 14]
    print(f"\n=== {nombre}: {len(items)} items, {len(recientes)} de los últimos 14 días")
    for item in items[:5]:
        print(f"  ({item.fecha.date()}) {item.titulo[:95]}")
