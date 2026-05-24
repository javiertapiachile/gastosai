"""
Factory de proveedores LLM.
Lee la configuración y retorna la instancia correcta.
"""

from app.services.llm.base import AbstractLLMProvider
from app.config import settings

_instancia: AbstractLLMProvider | None = None


def get_llm_provider() -> AbstractLLMProvider:
    """
    Retorna el proveedor LLM configurado en .env.
    Se cachea en memoria para reutilizar la misma instancia.
    """
    global _instancia
    if _instancia is not None:
        return _instancia

    proveedor = settings.llm_provider.lower()

    if proveedor == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider
        _instancia = AnthropicProvider()

    elif proveedor == "openai":
        from app.services.llm.openai_provider import OpenAIProvider
        _instancia = OpenAIProvider()

    elif proveedor == "ollama":
        from app.services.llm.ollama_provider import OllamaProvider
        _instancia = OllamaProvider()

    else:
        raise ValueError(
            f"Proveedor LLM desconocido: '{proveedor}'. "
            f"Opciones válidas: anthropic, openai, ollama"
        )

    return _instancia
