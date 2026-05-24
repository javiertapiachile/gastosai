"""
Endpoint de subida de archivos.
Fase 2: implementación real con parseo multi-formato y background tasks.
"""

import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.schemas.upload import UploadBatchOut, UploadBatchCreate
from app.schemas.transaction import TransactionCreate
from app.crud import uploads as crud_uploads
from app.crud import transactions as crud_tx
from app.models.upload import BatchStatus
from app.services.parser import get_parser
from app.utils.file_utils import validar_extension, validar_tamanio, limpiar_nombre

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/", response_model=list[UploadBatchOut])
async def listar_uploads(db: Session = Depends(get_db)):
    """Lista el historial de archivos importados."""
    return crud_uploads.get_batches(db)


@router.get("/{batch_id}", response_model=UploadBatchOut)
async def obtener_upload(batch_id: int, db: Session = Depends(get_db)):
    batch = crud_uploads.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    return batch


@router.post("/", response_model=UploadBatchOut, status_code=202)
async def subir_archivo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Recibe un archivo bancario, lo registra y lanza el parseo en background.
    Retorna 202 Accepted con el batch_id para hacer polling a /{batch_id}.
    """
    # Validar extensión
    try:
        extension = validar_extension(file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Leer contenido y validar tamaño
    contenido = await file.read()
    try:
        validar_tamanio(len(contenido))
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    # Crear batch en DB
    nombre_limpio = limpiar_nombre(file.filename or "archivo")
    batch = crud_uploads.create_batch(
        db,
        UploadBatchCreate(nombre_archivo=nombre_limpio, tipo_archivo=extension),
    )

    # Lanzar parseo en background (no bloquea la respuesta HTTP)
    background_tasks.add_task(
        _procesar_archivo_background,
        batch_id=batch.id,
        contenido=contenido,
        nombre_archivo=nombre_limpio,
        tipo_archivo=extension,
    )

    return batch


async def _procesar_archivo_background(
    batch_id: int,
    contenido: bytes,
    nombre_archivo: str,
    tipo_archivo: str,
) -> None:
    """
    Tarea background que:
    1. Parsea el archivo
    2. Inserta las transacciones en la DB
    3. Actualiza el estado del batch
    """
    # Crear sesión propia para el background task
    db = SessionLocal()
    try:
        # Marcar como procesando
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.procesando)

        # Parsear archivo
        parser = get_parser(tipo_archivo)
        resultado = await parser.parsear(contenido, nombre_archivo)

        if not resultado.exitoso and resultado.errores:
            crud_uploads.update_batch_progress(
                db, batch_id, 0, 0, BatchStatus.error,
                error="; ".join(resultado.errores)
            )
            return

        total = len(resultado.transacciones)

        # Actualizar total
        crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.procesando)

        # Insertar transacciones en lotes de 50
        LOTE = 50
        insertadas = 0
        for i in range(0, total, LOTE):
            lote = resultado.transacciones[i:i + LOTE]
            datos = [
                {
                    "descripcion_original": tx.descripcion,
                    "monto": tx.monto,
                    "es_cargo": tx.es_cargo,
                    "fecha": tx.fecha,
                    "rut_comercio": tx.rut_comercio,
                    "batch_id": batch_id,
                }
                for tx in lote
            ]
            crud_tx.create_transactions_bulk(db, datos)
            insertadas += len(lote)
            crud_uploads.update_batch_progress(db, batch_id, insertadas, total, BatchStatus.procesando)

        # Completado
        crud_uploads.update_batch_progress(db, batch_id, total, total, BatchStatus.completado)

    except Exception as e:
        crud_uploads.update_batch_progress(
            db, batch_id, 0, 0, BatchStatus.error,
            error=f"Error inesperado: {str(e)}"
        )
    finally:
        db.close()
