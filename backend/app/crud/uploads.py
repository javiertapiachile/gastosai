"""Operaciones CRUD para lotes de carga."""

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.upload import UploadBatch, BatchStatus
from app.schemas.upload import UploadBatchCreate


def create_batch(db: Session, data: UploadBatchCreate) -> UploadBatch:
    batch = UploadBatch(**data.model_dump())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def get_batch(db: Session, batch_id: int) -> UploadBatch | None:
    return db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()


def get_batches(db: Session) -> list[UploadBatch]:
    return db.query(UploadBatch).order_by(UploadBatch.creado_en.desc()).all()


def update_batch_progress(
    db: Session,
    batch_id: int,
    procesadas: int,
    total: int,
    estado: BatchStatus,
    error: str | None = None,
) -> UploadBatch | None:
    batch = get_batch(db, batch_id)
    if not batch:
        return None

    batch.transacciones_procesadas = procesadas
    batch.total_transacciones = total
    batch.progreso = round((procesadas / total * 100) if total > 0 else 0.0, 1)
    batch.estado = estado

    if error:
        batch.mensaje_error = error

    if estado in (BatchStatus.completado, BatchStatus.error):
        batch.completado_en = datetime.now(timezone.utc)

    db.commit()
    db.refresh(batch)
    return batch


def delete_batch(db: Session, batch_id: int) -> bool:
    """
    Elimina un batch y todas sus transacciones en cascada.
    Retorna True si se eliminó, False si no existía.
    """
    from app.models.transaction import Transaction

    batch = get_batch(db, batch_id)
    if not batch:
        return False

    # Eliminar transacciones asociadas primero
    db.query(Transaction).filter(Transaction.batch_id == batch_id).delete()
    db.delete(batch)
    db.commit()
    return True
