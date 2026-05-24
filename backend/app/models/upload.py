"""
Modelo SQLAlchemy para lotes de carga (archivos subidos).
Cada archivo importado genera un UploadBatch con su estado de procesamiento.
"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float
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
    tipo_archivo = Column(String(10), nullable=False)  # csv | xlsx | pdf
    estado = Column(Enum(BatchStatus), default=BatchStatus.pendiente, nullable=False)
    total_transacciones = Column(Integer, default=0)
    transacciones_procesadas = Column(Integer, default=0)
    progreso = Column(Float, default=0.0)  # 0.0 a 100.0
    mensaje_error = Column(String(500), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    completado_en = Column(DateTime(timezone=True), nullable=True)

    # Relación con transacciones
    transacciones = relationship("Transaction", back_populates="batch")

    def __repr__(self) -> str:
        return f"<UploadBatch {self.nombre_archivo} [{self.estado}]>"
