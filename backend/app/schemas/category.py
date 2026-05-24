"""Schemas Pydantic para entrada/salida de categorías."""

from pydantic import BaseModel, Field
from datetime import datetime


class CategoryBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#888780", pattern=r"^#[0-9A-Fa-f]{6}$")
    icono: str = Field(default="ti-tag", max_length=50)
    activa: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icono: str | None = None
    activa: bool | None = None


class CategoryOut(CategoryBase):
    id: int
    es_sistema: bool
    creado_en: datetime

    model_config = {"from_attributes": True}
