"""Schemas Pydantic para reglas de clasificación manual."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional
from app.schemas.category import CategoryOut


class ReglaCreate(BaseModel):
    patron: str = Field(..., min_length=2, max_length=200)
    tipo_match: Literal["contiene", "empieza", "exacto"] = "contiene"
    categoria_id: int
    descripcion_regla: Optional[str] = Field(None, max_length=200)
    prioridad: int = Field(default=0, ge=0, le=100)


class ReglaUpdate(BaseModel):
    patron: Optional[str] = Field(None, min_length=2, max_length=200)
    tipo_match: Optional[Literal["contiene", "empieza", "exacto"]] = None
    categoria_id: Optional[int] = None
    descripcion_regla: Optional[str] = None
    activa: Optional[bool] = None
    prioridad: Optional[int] = Field(None, ge=0, le=100)


class ReglaOut(BaseModel):
    id: int
    patron: str
    tipo_match: str
    categoria_id: int
    categoria: Optional[CategoryOut]
    descripcion_regla: Optional[str]
    activa: bool
    prioridad: int
    creado_en: datetime

    model_config = {"from_attributes": True}
