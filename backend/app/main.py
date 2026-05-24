"""GastosAI — Backend principal con autenticación JWT."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import Category, Transaction, UploadBatch, ClassificationCache, User
from app.routers import health, categories, transactions, uploads
from app.routers.auth import router as auth_router
from app.routers.config import router as config_router
from app.routers.export import router as export_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 GastosAI backend iniciando...")
    logger.info(f"   Proveedor LLM: {settings.llm_provider}")
    yield
    logger.info("🛑 GastosAI backend detenido")


app = FastAPI(
    title="GastosAI API",
    version="4.0.0",
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
app.include_router(auth_router,          prefix="/api/v1")
app.include_router(categories.router,    prefix="/api/v1")
app.include_router(transactions.router,  prefix="/api/v1")
app.include_router(uploads.router,       prefix="/api/v1")
app.include_router(config_router,        prefix="/api/v1")
app.include_router(export_router,        prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": "GastosAI", "version": "4.0.0", "docs": "/docs"}
