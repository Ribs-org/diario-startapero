"""Fuentes RSS de Copper Valley Diario.

El campo `foco` declara qué ecosistema cubre el feed y viaja hasta el
clasificador: los titulares de startups chilenas (p. ej. "Fracttal raises
$35M") casi nunca dicen "Chile", así que la procedencia es la única señal
fiable de chilenidad.

El campo `dias` es la ventana de frescura del feed. Por defecto 2 (corrida
diaria con solapamiento). Se amplía en los feeds de bajo volumen: publican
una o dos veces por semana y con 48 h no aportarían casi nunca. Ampliarla no
cuesta API —el dedupe por URL corre antes de clasificar— ni desborda, porque
esos feeds devuelven una decena de items en total.

Para revisar el estado de los feeds: python -m scripts.validar_fuentes
"""

SOURCES = [
    # Dedicadas al ecosistema chileno
    {"nombre": "LatamList - Chile",
     "feed_url": "https://latamlist.com/tag/chile/feed/",
     "foco": "chile", "dias": 30},
    {"nombre": "TrendTic",
     "feed_url": "https://www.trendtic.cl/feed/",
     "foco": "chile", "dias": 7},
    {"nombre": "La Tercera - Pulso",
     "feed_url": "https://www.latercera.com/arc/outboundfeeds/rss/category/pulso/?outputType=xml",
     "foco": "chile", "dias": 2},  # ~53 items cada 48 h: ventana corta a propósito
    # LATAM: aportan rondas chilenas con frecuencia
    {"nombre": "Startups Latam",
     "feed_url": "https://startupslatam.com/feed/",
     "foco": "latam", "dias": 7},
    {"nombre": "Contxto", "feed_url": "https://contxto.com/es/feed/",
     "foco": "latam", "dias": 7},
    {"nombre": "LatamList", "feed_url": "https://latamlist.com/feed/",
     "foco": "latam", "dias": 7},
    {"nombre": "iupana", "feed_url": "https://iupana.com/feed/",
     "foco": "latam", "dias": 7},
    {"nombre": "Fayerwayer", "feed_url": "https://www.fayerwayer.com/feed/",
     "foco": "latam", "dias": 2},
    # Orientadas a Mundo
    {"nombre": "TechCrunch - Startups",
     "feed_url": "https://techcrunch.com/category/startups/feed/",
     "foco": "mundo", "dias": 2},
    {"nombre": "Sifted", "feed_url": "https://sifted.eu/feed",
     "foco": "mundo", "dias": 2},
    {"nombre": "Crunchbase News", "feed_url": "https://news.crunchbase.com/feed/",
     "foco": "mundo", "dias": 2},
    {"nombre": "The Next Web", "feed_url": "https://thenextweb.com/feed",
     "foco": "mundo", "dias": 2},
]


def fuentes_con_foco(foco):
    """Fuentes declaradas para un ecosistema ('chile', 'latam', 'mundo')."""
    return [s for s in SOURCES if s.get("foco") == foco]
