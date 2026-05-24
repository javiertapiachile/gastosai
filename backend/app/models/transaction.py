"""Modelo SQLAlchemy para transacciones bancarias."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Datos originales del extracto
    descripcion_original = Column(String(500), nullable=False)
    monto = Column(Float, nullable=False)
    es_cargo = Column(Boolean, default=True, nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    rut_comercio = Column(String(20), nullable=True)

    # Datos enriquecidos por IA
    comercio_limpio = Column(String(200), nullable=True)
    descripcion_limpia = Column(String(200), nullable=True)

    # Clasificación
    categoria_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    categoria = relationship("Category", back_populates="transacciones")
    confianza_clasificacion = Column(Float, nullable=True)
    clasificado_por_cache = Column(Boolean, default=False)
    revisado_por_usuario = Column(Boolean, default=False)

    # Lote de origen
    batch_id = Column(Integer, ForeignKey("upload_batches.id"), nullable=True, index=True)
    batch = relationship("UploadBatch", back_populates="transacciones")

    # Usuario propietario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    usuario = relationship("User", back_populates="transacciones")

    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Transaction {self.descripcion_original[:30]} ${self.monto}>"
