"""Filtra y clasifica noticias con Claude: chile / mundo / descartar."""
import anthropic

MODEL = "claude-haiku-4-5-20251001"

SYSTEM = (
    "Eres el editor de Copper Valley Diario, un diario sobre startups y "
    "emprendimiento. Recibirás la fuente, el titular y el extracto de una "
    "noticia. Responde con UNA sola palabra:\n"
    "- chile: si trata sobre startups, emprendimiento o venture capital y su "
    "foco es Chile o una startup chilena.\n"
    "- mundo: si trata sobre startups, emprendimiento o venture capital de "
    "cualquier otro país o a nivel global.\n"
    "- descartar: si NO trata sobre startups ni emprendimiento (política, "
    "deportes, farándula, empresas tradicionales, macroeconomía general, etc.).\n"
    "\n"
    "Importante sobre la sección chile: la mayoría de las noticias sobre "
    "startups chilenas NUNCA mencionan la palabra 'Chile' en el titular; solo "
    "nombran a la empresa. Si reconoces que la startup fue fundada o tiene su "
    "sede en Chile (Betterfly, Fracttal, Haulmer, Cornershop, NotCo, Buk, "
    "Xepelin, Toku, Houm, Fintual, Broota, Poliglota, Justo, Examedi, "
    "Reversso, Lemontech, Webdox, Zippedi, Carryt, Ecoterra, entre muchas "
    "otras), responde chile aunque el texto no diga Chile. Ante la duda entre "
    "chile y mundo, elige chile solo si hay una conexión chilena real."
)


def _contexto(fuente, foco):
    if not fuente:
        return ""
    linea = f"Fuente: {fuente}"
    if foco == "chile":
        linea += " (medio que cubre exclusivamente el ecosistema chileno)"
    elif foco == "latam":
        linea += " (medio latinoamericano: verifica el país de la startup)"
    return linea + "\n"


def classify(titulo, extracto, fuente=None, foco=None, client=None):
    client = client or anthropic.Anthropic()
    respuesta = client.messages.create(
        model=MODEL,
        max_tokens=10,
        system=SYSTEM,
        messages=[{"role": "user",
                   "content": (f"{_contexto(fuente, foco)}"
                               f"Titular: {titulo}\nExtracto: {extracto}")}],
    )
    texto = respuesta.content[0].text.strip().lower()
    if texto in ("chile", "mundo"):
        return texto
    return None
