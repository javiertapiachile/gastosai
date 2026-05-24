"""
Modelo para el caché de clasificaciones LLM.
Almacena resultados por hash de descripción normalizada,
evitando llamadas repetidas al LLM para el mismo comercio.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ClassificationCache(Base):
    __tablename__ = "classification_cache"

    id = Column(Integer, primary_key=True, index=True)

    # Clave de búsqueda: hash SHA-256 de la descripción normalizada
    hash_descripcion = Column(String(64), unique=True, nullable=False, index=True)

    # Descripción normalizada para debugging y auditoría
    descripcion_normalizada = Column(String(200), nullable=False)

    # Resultado de la clasificación
    categoria = Column(String(100), nullable=False)
    comercio_limpio = Column(String(200), nullable=False)
    confianza = Column(Float, nullable=False, default=0.8)

    # Metadata
    proveedor_llm = Column(String(100), nullable=False)
    usos = Column(Integer, default=1, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Cache '{self.descripcion_normalizada}' -> {self.categoria} (usado {self.usos}x)>"
