"""Endpoints CRUD de transacciones filtradas por usuario."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
import math

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionUpdate, TransactionOut, TransactionListOut, KPISummary,
)
from app.crud import transactions as crud
from app.dependencies import get_usuario_actual

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _query_usuario(db: Session, user_id: int):
    """Query base filtrada por usuario."""
    return db.query(Transaction).filter(Transaction.user_id == user_id)


@router.get("/", response_model=TransactionListOut)
async def listar_transacciones(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    categoria_id: Optional[int] = None,
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    busqueda: Optional[str] = None,
    solo_cargos: Optional[bool] = None,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    items, total = crud.get_transactions(
        db, pagina=pagina, por_pagina=por_pagina,
        categoria_id=categoria_id, mes=mes, anio=anio,
        busqueda=busqueda, solo_cargos=solo_cargos,
        user_id=usuario.id,
    )
    return TransactionListOut(
        items=items, total=total, pagina=pagina, por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 0,
    )


@router.get("/kpis", response_model=KPISummary)
async def obtener_kpis(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return crud.get_kpi_summary(db, mes=mes, anio=anio, user_id=usuario.id)


@router.get("/charts/por-categoria")
async def gastos_por_categoria(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> list[dict]:
    return crud.get_gastos_por_categoria(db, mes=mes, anio=anio, user_id=usuario.id)


@router.get("/charts/evolucion-mensual")
async def evolucion_mensual(
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> list[dict]:
    return crud.get_evolucion_mensual(db, anio=anio, user_id=usuario.id)


@router.get("/{tx_id}", response_model=TransactionOut)
async def obtener_transaccion(
    tx_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    tx = crud.get_transaction(db, tx_id)
    if not tx or tx.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return tx


@router.patch("/{tx_id}", response_model=TransactionOut)
async def actualizar_transaccion(
    tx_id: int,
    data: TransactionUpdate,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    tx = crud.get_transaction(db, tx_id)
    if not tx or tx.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return crud.update_transaction(db, tx_id, data)


@router.delete("/{tx_id}", status_code=204)
async def eliminar_transaccion(
    tx_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    tx = crud.get_transaction(db, tx_id)
    if not tx or tx.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    crud.delete_transaction(db, tx_id)
