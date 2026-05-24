"""Proveedor LLM para OpenAI."""

import openai
from app.services.llm.base import AbstractLLMProvider
from app.config import settings


class OpenAIProvider(AbstractLLMProvider):
    """
    Usa gpt-4o-mini: económico y rápido para clasificación de transacciones.
    """

    MODELO = "gpt-4o-mini"

    def __init__(self):
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def nombre(self) -> str:
        return f"openai/{self.MODELO}"

    async def completar(self, prompt_sistema: str, prompt_usuario: str) -> str:
        respuesta = await self._client.chat.completions.create(
            model=self.MODELO,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
        )
        return respuesta.choices[0].message.content
