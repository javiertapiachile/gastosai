"""Endpoint de salud del sistema."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Verifica que el backend y la base de datos están operativos.
    Usado por Docker para healthcheck.
    """
    # Verificar conexión a DB
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "llm_provider": settings.llm_provider,
        "version": "1.0.0",
    }
