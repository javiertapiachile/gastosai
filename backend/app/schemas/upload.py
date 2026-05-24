"""Schemas Pydantic para lotes de carga."""

from pydantic import BaseModel
from datetime import datetime
from app.models.upload import BatchStatus


class UploadBatchOut(BaseModel):
    id: int
    nombre_archivo: str
    tipo_archivo: str
    estado: BatchStatus
    total_transacciones: int
    transacciones_procesadas: int
    progreso: float
    mensaje_error: str | None
    creado_en: datetime
    completado_en: datetime | None

    model_config = {"from_attributes": True}


class UploadBatchCreate(BaseModel):
    nombre_archivo: str
    tipo_archivo: str
