"""Dobles de prueba compartidos."""
from types import SimpleNamespace


class FakeClient:
    """Imita anthropic.Anthropic(): client.messages.create(...) -> respuesta fija."""

    def __init__(self, texto_respuesta):
        self._texto = texto_respuesta
        self.kwargs = None  # guarda la última llamada para inspección
        self.messages = self

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text=self._texto)])
