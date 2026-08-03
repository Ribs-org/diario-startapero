"""Descarga y parseo de feeds RSS y artículos."""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
import trafilatura

HEADERS = {"User-Agent": "CopperValleyDiario/1.0 (+diario de startups)"}
TIMEOUT = 30


@dataclass
class FeedItem:
    titulo: str
    url: str
    extracto: str
    fecha: datetime  # aware, UTC


def _sin_html(texto):
    return re.sub(r"<[^>]+>", " ", texto).strip()


def parse_feed(feed_content):
    parsed = feedparser.parse(feed_content)
    items = []
    for entry in parsed.entries:
        fecha_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        link = entry.get("link")
        if not fecha_struct or not link:
            continue
        fecha = datetime(*fecha_struct[:6], tzinfo=timezone.utc)
        items.append(FeedItem(
            titulo=entry.get("title", "").strip(),
            url=link,
            extracto=_sin_html(entry.get("summary", "")),
            fecha=fecha,
        ))
    return items


def filter_recent(items, days=2, now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    return [i for i in items if i.fecha >= cutoff]


def fetch_feed(url):
    resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
    resp.raise_for_status()
    return parse_feed(resp.content)


def fetch_article_text(url):
    resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
    resp.raise_for_status()
    return trafilatura.extract(resp.text)
