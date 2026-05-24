"""
Endpoints de configuración: estado del sistema, verificación LLM, stats del caché.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.services.classifier import verificar_conexion_llm, contar_entradas_cache

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/")
async def obtener_config() -> dict:
    """Retorna la configuración actual del sistema (sin exponer claves)."""
    return {
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "max_file_size_mb": settings.max_file_size_mb,
        # Mostrar solo si hay clave configurada, no el valor
        "anthropic_configurado": bool(settings.anthropic_api_key),
        "openai_configurado": bool(settings.openai_api_key),
    }


@router.get("/llm/test")
async def probar_llm() -> dict:
    """
    Verifica que el proveedor LLM configurado responde correctamente.
    Útil para validar la API key desde la UI de configuración.
    """
    return await verificar_conexion_llm()


@router.get("/stats")
async def estadisticas_sistema(db: Session = Depends(get_db)) -> dict:
    """Estadísticas del sistema: tamaño del caché, transacciones, etc."""
    from app.crud.transactions import get_kpi_summary
    from app.models.transaction import Transaction
    from app.models.upload import UploadBatch

    total_tx = db.query(Transaction).count()
    total_batches = db.query(UploadBatch).count()
    entradas_cache = contar_entradas_cache(db)

    return {
        "total_transacciones": total_tx,
        "total_importaciones": total_batches,
        "entradas_cache_llm": entradas_cache,
        "proveedor_llm": settings.llm_provider,
    }
