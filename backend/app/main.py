"""
GastosAI — Backend principal.
Punto de entrada de FastAPI con configuración de CORS, lifespan y routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Category, Transaction, UploadBatch  # Importar para crear tablas
from app.routers import health, categories, transactions, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ejecuta lógica de arranque (antes de yield) y cierre (después de yield)."""
    # Las migraciones las maneja alembic; aquí solo verificamos conexión
    print("🚀 GastosAI backend iniciando...")
    yield
    print("🛑 GastosAI backend detenido")


app = FastAPI(
    title="GastosAI API",
    description="Dashboard local de análisis de gastos personales con clasificación automática por IA",
    version="1.0.0",
    lifespan=lifespan,
)

# Configurar CORS para que el frontend pueda comunicarse con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health.router)
app.include_router(categories.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": "GastosAI",
        "version": "1.0.0",
        "docs": "/docs",
    }
