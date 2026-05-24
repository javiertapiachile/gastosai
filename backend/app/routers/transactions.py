"""Endpoints CRUD para transacciones, incluyendo KPIs y gráficos."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionOut,
    TransactionListOut, KPISummary,
)
from app.crud import transactions as crud

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=TransactionListOut)
async def listar_transacciones(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    categoria_id: Optional[int] = None,
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    busqueda: Optional[str] = None,
    solo_cargos: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Retorna transacciones paginadas con filtros opcionales."""
    items, total = crud.get_transactions(
        db,
        pagina=pagina,
        por_pagina=por_pagina,
        categoria_id=categoria_id,
        mes=mes,
        anio=anio,
        busqueda=busqueda,
        solo_cargos=solo_cargos,
    )
    return TransactionListOut(
        items=items,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 0,
    )


@router.get("/kpis", response_model=KPISummary)
async def obtener_kpis(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    """KPIs para el dashboard: totales, clasificación, categoría top."""
    return crud.get_kpi_summary(db, mes=mes, anio=anio)


@router.get("/charts/por-categoria")
async def gastos_por_categoria(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Datos para gráfico de torta: gastos agrupados por categoría."""
    return crud.get_gastos_por_categoria(db, mes=mes, anio=anio)


@router.get("/charts/evolucion-mensual")
async def evolucion_mensual(
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Evolución de gastos mes a mes para gráfico de líneas."""
    return crud.get_evolucion_mensual(db, anio=anio)


@router.get("/{tx_id}", response_model=TransactionOut)
async def obtener_transaccion(tx_id: int, db: Session = Depends(get_db)):
    tx = crud.get_transaction(db, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return tx


@router.post("/", response_model=TransactionOut, status_code=201)
async def crear_transaccion(data: TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(db, data)


@router.patch("/{tx_id}", response_model=TransactionOut)
async def actualizar_transaccion(
    tx_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    tx = crud.update_transaction(db, tx_id, data)
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return tx


@router.delete("/{tx_id}", status_code=204)
async def eliminar_transaccion(tx_id: int, db: Session = Depends(get_db)):
    eliminada = crud.delete_transaction(db, tx_id)
    if not eliminada:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
