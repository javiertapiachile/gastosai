"""
Endpoint de subida de archivos.
En Fase 1 solo registra el batch; el parser real se implementa en Fase 2.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.upload import UploadBatchOut, UploadBatchCreate
from app.crud import uploads as crud

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/", response_model=list[UploadBatchOut])
async def listar_uploads(db: Session = Depends(get_db)):
    """Lista el historial de archivos importados."""
    return crud.get_batches(db)


@router.get("/{batch_id}", response_model=UploadBatchOut)
async def obtener_upload(batch_id: int, db: Session = Depends(get_db)):
    batch = crud.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    return batch


@router.post("/", response_model=UploadBatchOut, status_code=202)
async def subir_archivo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Recibe un archivo y crea un batch.
    El procesamiento real (parse + clasificación) se implementa en Fase 2.
    Retorna 202 Accepted con el batch_id para hacer polling.
    """
    # Validar extensión
    extension = file.filename.split(".")[-1].lower() if file.filename else ""
    if extension not in ("csv", "xlsx", "pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: .{extension}. Use csv, xlsx o pdf."
        )

    batch = crud.create_batch(
        db,
        UploadBatchCreate(
            nombre_archivo=file.filename or "sin_nombre",
            tipo_archivo=extension,
        )
    )
    return batch
