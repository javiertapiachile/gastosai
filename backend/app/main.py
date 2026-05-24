"""
GastosAI — Backend principal.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import Category, Transaction, UploadBatch, ClassificationCache
from app.routers import health, categories, transactions, uploads
from app.routers.config import router as config_router
from app.routers.export import router as export_router

# Configurar logging para ver errores del clasificador en los logs de Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 GastosAI backend iniciando...")
    logger.info(f"   Proveedor LLM: {settings.llm_provider}")
    logger.info(f"   Anthropic key configurada: {bool(settings.anthropic_api_key)}")
    yield
    logger.info("🛑 GastosAI backend detenido")


app = FastAPI(
    title="GastosAI API",
    version="3.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(categories.router,   prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(uploads.router,      prefix="/api/v1")
app.include_router(config_router,       prefix="/api/v1")
app.include_router(export_router,       prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": "GastosAI", "version": "3.1.0", "docs": "/docs"}
