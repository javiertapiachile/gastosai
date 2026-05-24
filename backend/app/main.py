"""
GastosAI — Backend principal.
Punto de entrada de FastAPI: CORS, lifespan, routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import Category, Transaction, UploadBatch, ClassificationCache
from app.routers import health, categories, transactions, uploads
from app.routers.config import router as config_router
from app.routers.export import router as export_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 GastosAI backend iniciando...")
    yield
    print("🛑 GastosAI backend detenido")


app = FastAPI(
    title="GastosAI API",
    description="Dashboard local de análisis de gastos personales con clasificación automática por IA",
    version="3.0.0",
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
app.include_router(categories.router,    prefix="/api/v1")
app.include_router(transactions.router,  prefix="/api/v1")
app.include_router(uploads.router,       prefix="/api/v1")
app.include_router(config_router,        prefix="/api/v1")
app.include_router(export_router,        prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": "GastosAI", "version": "3.0.0", "docs": "/docs"}
