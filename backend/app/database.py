"""
Configuración de SQLAlchemy: engine, sesión y clase base para modelos.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLite necesita check_same_thread=False para funcionar con FastAPI
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,  # Cambiar a True para ver queries SQL en desarrollo
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI para inyectar sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
