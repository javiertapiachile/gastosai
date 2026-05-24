"""Endpoints de configuración del sistema — requieren autenticación."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.services.classifier import verificar_conexion_llm, contar_entradas_cache
from app.dependencies import get_usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


@router.get("/")
async def obtener_config(
    usuario: User = Depends(get_usuario_actual),
) -> dict:
    """Retorna la configuración actual del sistema."""
    return {
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "max_file_size_mb": settings.max_file_size_mb,
        "anthropic_configurado": bool(settings.anthropic_api_key),
        "openai_configurado": bool(settings.openai_api_key),
    }


@router.get("/llm/test")
async def probar_llm(
    usuario: User = Depends(get_usuario_actual),
) -> dict:
    """Verifica que el proveedor LLM configurado responde."""
    return await verificar_conexion_llm()


@router.get("/stats")
async def estadisticas_sistema(
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> dict:
    """Estadísticas del sistema para el usuario autenticado."""
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
