"""
Configuración central de GastosAI.
Lee variables de entorno (o el archivo .env en desarrollo).
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal


class Settings(BaseSettings):
    # Base de datos
    database_url: str = "sqlite:////app/data/gastosai.db"

    # Proveedor LLM
    llm_provider: Literal["anthropic", "openai", "ollama"] = "anthropic"

    # Claves de API
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Ollama
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3"

    # Archivos
    max_file_size_mb: int = 50

    # CORS
    cors_origins: str = "http://localhost:5173"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
