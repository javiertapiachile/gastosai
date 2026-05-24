"""Modelo SQLAlchemy para lotes de carga."""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class BatchStatus(str, enum.Enum):
    pendiente = "pendiente"
    procesando = "procesando"
    clasificando = "clasificando"
    completado = "completado"
    error = "error"


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    tipo_archivo = Column(String(10), nullable=False)
    ruta_archivo = Column(String(500), nullable=True)
    hash_contenido = Column(String(64), nullable=True, index=True)  # SHA-256 para deduplicación
    estado = Column(Enum(BatchStatus), default=BatchStatus.pendiente, nullable=False)
    total_transacciones = Column(Integer, default=0)
    transacciones_procesadas = Column(Integer, default=0)
    progreso = Column(Float, default=0.0)
    mensaje_error = Column(String(500), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    completado_en = Column(DateTime(timezone=True), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    usuario = relationship("User", back_populates="batches")
    transacciones = relationship("Transaction", back_populates="batch")

    def __repr__(self) -> str:
        return f"<UploadBatch {self.nombre_archivo} [{self.estado}]>"
