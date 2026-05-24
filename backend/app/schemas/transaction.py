"""Schemas Pydantic para entrada/salida de transacciones."""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from app.schemas.category import CategoryOut


class TransactionBase(BaseModel):
    descripcion_original: str = Field(..., min_length=1, max_length=500)
    monto: float = Field(..., gt=0)
    es_cargo: bool = True
    fecha: date
    rut_comercio: Optional[str] = None


class TransactionCreate(TransactionBase):
    batch_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    categoria_id: Optional[int] = None
    revisado_por_usuario: Optional[bool] = None
    comercio_limpio: Optional[str] = None


class TransactionOut(TransactionBase):
    id: int
    comercio_limpio: Optional[str]
    descripcion_limpia: Optional[str]
    categoria_id: Optional[int]
    categoria: Optional[CategoryOut]
    confianza_clasificacion: Optional[float]
    clasificado_por_cache: bool
    revisado_por_usuario: bool
    batch_id: Optional[int]
    creado_en: datetime

    model_config = {"from_attributes": True}


class TransactionListOut(BaseModel):
    """Respuesta paginada de transacciones."""
    items: list[TransactionOut]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int


class KPISummary(BaseModel):
    """KPIs para el dashboard."""
    total_gastos: float
    total_ingresos: float
    total_transacciones: int
    transacciones_clasificadas: int
    pct_clasificadas: float
    categoria_top: Optional[str]
    gasto_categoria_top: Optional[float]
