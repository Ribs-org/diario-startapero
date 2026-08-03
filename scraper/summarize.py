"""Genera titular y resumen propios con Claude."""
import json
import re

import anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_CHARS = 6000

SYSTEM = (
    "Eres periodista de Copper Valley Diario, un diario en español sobre "
    "startups y emprendimiento. A partir del texto entregado escribe:\n"
    "- Un titular propio, informativo y sobrio (sin clickbait).\n"
    "- Un resumen propio de 2 a 3 párrafos en español, fiel al texto. No "
    "inventes datos ni cifras que no estén en el texto.\n"
    'Responde SOLO con JSON válido, sin texto adicional: '
    '{"titulo": "...", "resumen": "..."}'
)


def summarize(titulo_original, texto, fuente, client=None):
    client = client or anthropic.Anthropic()
    contenido = (f"Fuente: {fuente}\n"
                 f"Titular original: {titulo_original}\n\n"
                 f"Texto:\n{texto[:MAX_CHARS]}")
    respuesta = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": contenido}],
    )
    bruto = respuesta.content[0].text.strip()
    bruto = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", bruto)
    try:
        datos = json.loads(bruto)
    except json.JSONDecodeError:
        return None
    if not datos.get("titulo") or not datos.get("resumen"):
        return None
    return {"titulo": datos["titulo"], "resumen": datos["resumen"]}
