from datetime import datetime, timezone
from pathlib import Path

from scraper.fetch import filter_recent, parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "sample_feed.xml"


def cargar():
    return parse_feed(FIXTURE.read_text(encoding="utf-8"))


def test_parse_feed_extrae_items():
    items = cargar()
    assert len(items) == 2  # descarta la entrada sin fecha
    a = items[0]
    assert a.titulo == "Startup A levanta US$5M"
    assert a.url == "https://ejemplo.com/a"
    assert "anunció" in a.extracto
    assert "<b>" not in a.extracto
    assert a.fecha == datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)


def test_filter_recent_deja_solo_lo_nuevo():
    items = cargar()
    now = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
    recientes = filter_recent(items, days=2, now=now)
    assert [i.url for i in recientes] == ["https://ejemplo.com/a"]
