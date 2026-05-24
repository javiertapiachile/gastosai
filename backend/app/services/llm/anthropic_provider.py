"""Proveedor LLM para Anthropic Claude."""

import anthropic
from app.services.llm.base import AbstractLLMProvider
from app.config import settings


class AnthropicProvider(AbstractLLMProvider):
    """
    Usa claude-3-5-haiku-latest: el modelo más rápido y económico de Anthropic,
    ideal para clasificación masiva de transacciones.
    """

    MODELO = "claude-3-5-haiku-latest"

    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @property
    def nombre(self) -> str:
        return f"anthropic/{self.MODELO}"

    async def completar(self, prompt_sistema: str, prompt_usuario: str) -> str:
        mensaje = await self._client.messages.create(
            model=self.MODELO,
            max_tokens=1024,
            system=prompt_sistema,
            messages=[{"role": "user", "content": prompt_usuario}],
        )
        return mensaje.content[0].text
