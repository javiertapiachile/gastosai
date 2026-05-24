"""
Interfaz abstracta que todos los proveedores LLM deben implementar.
La lógica de clasificación no sabe qué proveedor está usando.
"""

from abc import ABC, abstractmethod


class AbstractLLMProvider(ABC):
    """
    Contrato mínimo para cualquier proveedor LLM.
    Solo expone el método que necesita el clasificador.
    """

    @abstractmethod
    async def completar(self, prompt_sistema: str, prompt_usuario: str) -> str:
        """
        Envía un prompt al LLM y retorna el texto de respuesta.

        Args:
            prompt_sistema: Instrucciones de rol y comportamiento
            prompt_usuario:  El mensaje concreto a procesar

        Returns:
            Texto de respuesta del modelo (sin parsear)
        """
        ...

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Identificador legible del proveedor, ej: 'anthropic/claude-3-5-haiku'"""
        ...
