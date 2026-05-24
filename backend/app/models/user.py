"""
Modelo de usuario para autenticación local.
Las contraseñas se guardan hasheadas con bcrypt, nunca en texto plano.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    es_admin = Column(Boolean, default=False, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    transacciones = relationship("Transaction", back_populates="usuario")
    batches = relationship("UploadBatch", back_populates="usuario")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
