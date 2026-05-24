"""
Factory de proveedores LLM.
Lee la configuración y retorna la instancia correcta.
"""

from functools import lru_cache
from app.services.llm.base import AbstractLLMProvider
from app.config import settings


@lru_cache(maxsize=1)
def get_llm_provider() -> AbstractLLMProvider:
    """
    Retorna el proveedor LLM configurado en .env.
    Se cachea para reutilizar la misma instancia (y su connection pool).
    """
    proveedor = settings.llm_provider.lower()

    if proveedor == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    elif proveedor == "openai":
        from app.services.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif proveedor == "ollama":
        from app.services.llm.ollama_provider import OllamaProvider
        return OllamaProvider()

    else:
        raise ValueError(
            f"Proveedor LLM desconocido: '{proveedor}'. "
            f"Opciones válidas: anthropic, openai, ollama"
        )
