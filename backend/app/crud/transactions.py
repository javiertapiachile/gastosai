"""Operaciones CRUD para transacciones, filtradas por usuario."""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional

from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionUpdate, KPISummary


def get_transaction(db: Session, tx_id: int) -> Transaction | None:
    return db.query(Transaction).filter(Transaction.id == tx_id).first()


def get_transactions(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 50,
    categoria_id: Optional[int] = None,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    busqueda: Optional[str] = None,
    solo_cargos: Optional[bool] = None,
    user_id: Optional[int] = None,
) -> tuple[list[Transaction], int]:
    query = db.query(Transaction)

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)
    if categoria_id is not None:
        query = query.filter(Transaction.categoria_id == categoria_id)
    if mes is not None:
        query = query.filter(extract("month", Transaction.fecha) == mes)
    if anio is not None:
        query = query.filter(extract("year", Transaction.fecha) == anio)
    if busqueda:
        termino = f"%{busqueda}%"
        query = query.filter(
            Transaction.descripcion_original.ilike(termino)
            | Transaction.comercio_limpio.ilike(termino)
        )
    if solo_cargos is not None:
        query = query.filter(Transaction.es_cargo == solo_cargos)

    total = query.count()
    items = (
        query.order_by(Transaction.fecha.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    return items, total


def create_transaction(db: Session, tx: TransactionCreate) -> Transaction:
    db_tx = Transaction(**tx.model_dump())
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx


def create_transactions_bulk(db: Session, txs: list[dict]) -> list[Transaction]:
    db_txs = [Transaction(**tx) for tx in txs]
    db.add_all(db_txs)
    db.commit()
    for tx in db_txs:
        db.refresh(tx)
    return db_txs


def update_transaction(db: Session, tx_id: int, data: TransactionUpdate) -> Transaction | None:
    db_tx = get_transaction(db, tx_id)
    if not db_tx:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(db_tx, field, value)
    db.commit()
    db.refresh(db_tx)
    return db_tx


def delete_transaction(db: Session, tx_id: int) -> bool:
    db_tx = get_transaction(db, tx_id)
    if not db_tx:
        return False
    db.delete(db_tx)
    db.commit()
    return True


def get_kpi_summary(
    db: Session,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    user_id: Optional[int] = None,
) -> KPISummary:
    query = db.query(Transaction)
    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)
    if mes is not None:
        query = query.filter(extract("month", Transaction.fecha) == mes)
    if anio is not None:
        query = query.filter(extract("year", Transaction.fecha) == anio)

    todas = query.all()
    total_gastos = sum(t.monto for t in todas if t.es_cargo)
    total_ingresos = sum(t.monto for t in todas if not t.es_cargo)
    total_tx = len(todas)
    clasificadas = sum(1 for t in todas if t.categoria_id is not None)
    pct = (clasificadas / total_tx * 100) if total_tx > 0 else 0.0

    categoria_top = None
    gasto_top = None
    if total_tx > 0:
        resultado = (
            db.query(Category.nombre, func.sum(Transaction.monto).label("total"))
            .join(Transaction, Transaction.categoria_id == Category.id)
            .filter(Transaction.es_cargo == True)
        )
        if user_id:
            resultado = resultado.filter(Transaction.user_id == user_id)
        if mes:
            resultado = resultado.filter(extract("month", Transaction.fecha) == mes)
        if anio:
            resultado = resultado.filter(extract("year", Transaction.fecha) == anio)
        fila = resultado.group_by(Category.nombre).order_by(func.sum(Transaction.monto).desc()).first()
        if fila:
            categoria_top, gasto_top = fila

    return KPISummary(
        total_gastos=round(total_gastos, 2),
        total_ingresos=round(total_ingresos, 2),
        total_transacciones=total_tx,
        transacciones_clasificadas=clasificadas,
        pct_clasificadas=round(pct, 1),
        categoria_top=categoria_top,
        gasto_categoria_top=round(gasto_top, 2) if gasto_top else None,
    )


def get_gastos_por_categoria(
    db: Session,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    user_id: Optional[int] = None,
) -> list[dict]:
    query = (
        db.query(
            Category.nombre, Category.color,
            func.sum(Transaction.monto).label("total"),
            func.count(Transaction.id).label("cantidad"),
        )
        .join(Transaction, Transaction.categoria_id == Category.id)
        .filter(Transaction.es_cargo == True)
    )
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if mes:
        query = query.filter(extract("month", Transaction.fecha) == mes)
    if anio:
        query = query.filter(extract("year", Transaction.fecha) == anio)

    filas = query.group_by(Category.nombre, Category.color).order_by(func.sum(Transaction.monto).desc()).all()
    return [{"nombre": f.nombre, "color": f.color, "total": round(f.total, 2), "cantidad": f.cantidad} for f in filas]


def get_evolucion_mensual(
    db: Session,
    anio: Optional[int] = None,
    user_id: Optional[int] = None,
) -> list[dict]:
    query = (
        db.query(
            extract("year", Transaction.fecha).label("anio"),
            extract("month", Transaction.fecha).label("mes"),
            func.sum(Transaction.monto).label("total"),
        )
        .filter(Transaction.es_cargo == True)
    )
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if anio:
        query = query.filter(extract("year", Transaction.fecha) == anio)

    filas = query.group_by("anio", "mes").order_by("anio", "mes").all()
    meses_es = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    return [
        {"anio": int(f.anio), "mes": int(f.mes), "mes_nombre": meses_es[int(f.mes)-1], "total": round(f.total, 2)}
        for f in filas
    ]
