"""Endpoints de configuración — lectura y actualización en caliente del proveedor LLM."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal, Optional

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.services.classifier import verificar_conexion_llm, contar_entradas_cache
from app.dependencies import get_usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


class ConfigUpdate(BaseModel):
    llm_provider: Optional[Literal["anthropic", "openai", "ollama"]] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None


@router.get("/")
async def obtener_config(usuario: User = Depends(get_usuario_actual)) -> dict:
    return {
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "max_file_size_mb": settings.max_file_size_mb,
        "anthropic_configurado": bool(settings.anthropic_api_key),
        "openai_configurado": bool(settings.openai_api_key),
    }


@router.patch("/")
async def actualizar_config(
    data: ConfigUpdate,
    usuario: User = Depends(get_usuario_actual),
) -> dict:
    """
    Actualiza la configuración LLM en caliente sin reiniciar Docker.
    Los cambios persisten en memoria hasta el próximo reinicio del contenedor.
    Para persistencia permanente, actualiza el .env.
    """
    from app.services.llm import factory as llm_factory

    cambios = []

    if data.llm_provider is not None:
        settings.llm_provider = data.llm_provider
        cambios.append(f"llm_provider={data.llm_provider}")

    if data.anthropic_api_key is not None:
        settings.anthropic_api_key = data.anthropic_api_key
        cambios.append("anthropic_api_key actualizada")

    if data.openai_api_key is not None:
        settings.openai_api_key = data.openai_api_key
        cambios.append("openai_api_key actualizada")

    if data.ollama_base_url is not None:
        settings.ollama_base_url = data.ollama_base_url
        cambios.append(f"ollama_base_url={data.ollama_base_url}")

    if data.ollama_model is not None:
        settings.ollama_model = data.ollama_model
        cambios.append(f"ollama_model={data.ollama_model}")

    # Resetear instancia cacheada del proveedor para usar la nueva config
    llm_factory._instancia = None

    logger.info(f"[config] Actualizado por {usuario.email}: {', '.join(cambios)}")

    return {
        "ok": True,
        "mensaje": "Configuración actualizada. Prueba la conexión para verificar.",
        "cambios": cambios,
    }


@router.get("/llm/test")
async def probar_llm(usuario: User = Depends(get_usuario_actual)) -> dict:
    return await verificar_conexion_llm()


@router.get("/stats")
async def estadisticas_sistema(
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> dict:
    from app.models.transaction import Transaction
    from app.models.upload import UploadBatch

    total_tx = db.query(Transaction).filter(Transaction.user_id == usuario.id).count()
    total_batches = db.query(UploadBatch).filter(UploadBatch.user_id == usuario.id).count()
    entradas_cache = contar_entradas_cache(db)

    return {
        "total_transacciones": total_tx,
        "total_importaciones": total_batches,
        "entradas_cache_llm": entradas_cache,
        "proveedor_llm": settings.llm_provider,
    }
