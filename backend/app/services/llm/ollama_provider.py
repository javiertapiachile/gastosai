"""Proveedor LLM para Ollama con soporte de formato JSON."""

import httpx
from app.services.llm.base import AbstractLLMProvider
from app.config import settings


class OllamaProvider(AbstractLLMProvider):

    def __init__(self):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._modelo = settings.ollama_model

    @property
    def nombre(self) -> str:
        return f"ollama/{self._modelo}"

    async def completar(self, prompt_sistema: str, prompt_usuario: str) -> str:
        # Timeout largo para PDFs con mucho texto
        async with httpx.AsyncClient(timeout=300) as client:
            respuesta = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._modelo,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user",   "content": prompt_usuario},
                    ],
                    # Pedir formato JSON cuando el prompt lo requiere
                    "options": {
                        "temperature": 0.1,  # Baja temperatura para respuestas más deterministas
                        "num_predict": 4096, # Suficiente para listas largas de transacciones
                    },
                },
            )
            respuesta.raise_for_status()
            return respuesta.json()["message"]["content"]
