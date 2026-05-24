"""
Modelo para reglas de clasificación manual.
Permite definir reglas tipo "si descripción contiene X → categoría Y".
Las reglas tienen prioridad sobre la clasificación del LLM.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ClasificacionRegla(Base):
    __tablename__ = "clasificacion_reglas"

    id = Column(Integer, primary_key=True, index=True)

    # Condición: patrón de texto a buscar en la descripción original
    patron = Column(String(200), nullable=False)

    # Tipo de coincidencia
    # "contiene"   → descripcion.lower() contiene patron.lower()
    # "empieza"    → descripcion.lower().startswith(patron.lower())
    # "exacto"     → descripcion.lower() == patron.lower()
    tipo_match = Column(String(20), nullable=False, default="contiene")

    # Resultado: categoría a asignar
    categoria_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    categoria = relationship("Category")

    # Metadata
    descripcion_regla = Column(String(200), nullable=True)  # Descripción humana opcional
    activa = Column(Boolean, default=True, nullable=False)
    prioridad = Column(Integer, default=0, nullable=False)  # Mayor = más prioritaria
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Regla '{self.patron}' → cat_id={self.categoria_id}>"
