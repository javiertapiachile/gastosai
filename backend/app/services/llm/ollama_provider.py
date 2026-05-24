"""Proveedor LLM para Ollama (modelos locales sin costo de API)."""

import httpx
from app.services.llm.base import AbstractLLMProvider
from app.config import settings


class OllamaProvider(AbstractLLMProvider):
    """
    Conecta con Ollama corriendo en el host.
    Soporta cualquier modelo descargado: llama3, mistral, gemma2, etc.
    """

    def __init__(self):
        self._base_url = settings.ollama_base_url
        self._modelo = settings.ollama_model

    @property
    def nombre(self) -> str:
        return f"ollama/{self._modelo}"

    async def completar(self, prompt_sistema: str, prompt_usuario: str) -> str:
        prompt_completo = f"{prompt_sistema}\n\n{prompt_usuario}"

        async with httpx.AsyncClient(timeout=60) as client:
            respuesta = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._modelo,
                    "prompt": prompt_completo,
                    "stream": False,
                },
            )
            respuesta.raise_for_status()
            return respuesta.json().get("response", "")
