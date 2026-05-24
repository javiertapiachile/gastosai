"""
Proveedor LLM para Ollama (modelos locales sin costo de API).
Usa /api/chat que es compatible con todos los modelos modernos de Ollama.
"""

import httpx
from app.services.llm.base import AbstractLLMProvider
from app.config import settings


class OllamaProvider(AbstractLLMProvider):
    """
    Conecta con Ollama corriendo en el host.
    Soporta cualquier modelo: gemma4, llama3, mistral, etc.
    Usa el endpoint /api/chat (compatible con Ollama >= 0.1.14).
    """

    def __init__(self):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._modelo = settings.ollama_model

    @property
    def nombre(self) -> str:
        return f"ollama/{self._modelo}"

    async def completar(self, prompt_sistema: str, prompt_usuario: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            respuesta = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._modelo,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user",   "content": prompt_usuario},
                    ],
                },
            )
            respuesta.raise_for_status()
            return respuesta.json()["message"]["content"]
