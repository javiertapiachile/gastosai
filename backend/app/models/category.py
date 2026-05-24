"""
Modelo SQLAlchemy para categorías de gastos.
Las categorías base se insertan en la migración inicial.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=False, default="#888780")  # Hex color
    icono = Column(String(50), nullable=False, default="ti-tag")  # Clase Tabler icon
    activa = Column(Boolean, default=True, nullable=False)
    es_sistema = Column(Boolean, default=False, nullable=False)  # No borrar
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa
    transacciones = relationship("Transaction", back_populates="categoria")

    def __repr__(self) -> str:
        return f"<Category {self.nombre}>"
