"""Filtra y clasifica noticias con Claude: chile / mundo / descartar."""
import anthropic

MODEL = "claude-haiku-4-5-20251001"

SYSTEM = (
    "Eres el editor de Copper Valley Diario, un diario sobre startups y "
    "emprendimiento. Recibirás el titular y el extracto de una noticia. "
    "Responde con UNA sola palabra:\n"
    "- chile: si trata sobre startups, emprendimiento o venture capital y su "
    "foco es Chile o una startup chilena.\n"
    "- mundo: si trata sobre startups, emprendimiento o venture capital de "
    "cualquier otro país o a nivel global.\n"
    "- descartar: si NO trata sobre startups ni emprendimiento (política, "
    "deportes, farándula, empresas tradicionales, macroeconomía general, etc.)."
)


def classify(titulo, extracto, client=None):
    client = client or anthropic.Anthropic()
    respuesta = client.messages.create(
        model=MODEL,
        max_tokens=10,
        system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"Titular: {titulo}\nExtracto: {extracto}"}],
    )
    texto = respuesta.content[0].text.strip().lower()
    if texto in ("chile", "mundo"):
        return texto
    return None
