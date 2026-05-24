"""
Endpoint de subida de archivos.
Fase 3: integra clasificador LLM después del parseo.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.schemas.upload import UploadBatchOut, UploadBatchCreate
from app.crud import uploads as crud_uploads
from app.crud import transactions as crud_tx
from app.models.upload import BatchStatus
from app.services.parser import get_parser
from app.services.classifier import clasificar_transacciones
from app.utils.file_utils import validar_extension, validar_tamanio, limpiar_nombre

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/", response_model=list[UploadBatchOut])
async def listar_uploads(db: Session = Depends(get_db)):
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
    Recibe archivo bancario → parsea → clasifica con LLM.
    Retorna 202 Accepted con batch_id para polling.
    """
    try:
        extension = validar_extension(file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    contenido = await file.read()
    try:
        validar_tamanio(len(contenido))
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    nombre_limpio = limpiar_nombre(file.filename or "archivo")
    batch = crud_uploads.create_batch(
        db,
        UploadBatchCreate(nombre_archivo=nombre_limpio, tipo_archivo=extension),
    )

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
    Background task completo:
    1. Parsear archivo → transacciones raw
    2. Insertar transacciones en DB
    3. Clasificar con LLM (caché + API)
    4. Actualizar estado del batch
    """
    db = SessionLocal()
    try:
        # Fase A: parseo
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.procesando)

        parser = get_parser(tipo_archivo)
        resultado = await parser.parsear(contenido, nombre_archivo)

        if not resultado.exitoso and resultado.errores:
            crud_uploads.update_batch_progress(
                db, batch_id, 0, 0, BatchStatus.error,
                error="; ".join(resultado.errores)
            )
            return

        total = len(resultado.transacciones)
        crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.procesando)

        # Insertar en lotes de 50
        LOTE = 50
        ids_insertados = []
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
            txs_db = crud_tx.create_transactions_bulk(db, datos)
            ids_insertados.extend([t.id for t in txs_db])
            crud_uploads.update_batch_progress(
                db, batch_id, len(ids_insertados), total, BatchStatus.procesando
            )

        # Fase B: clasificación LLM
        crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.clasificando)

        # Cargar transacciones recién insertadas para clasificar
        from app.models.transaction import Transaction
        txs_para_clasificar = (
            db.query(Transaction)
            .filter(Transaction.batch_id == batch_id)
            .all()
        )

        stats = await clasificar_transacciones(db, txs_para_clasificar)
        print(f"[batch {batch_id}] Clasificación: {stats}")

        crud_uploads.update_batch_progress(db, batch_id, total, total, BatchStatus.completado)

    except Exception as e:
        print(f"[batch {batch_id}] Error inesperado: {e}")
        crud_uploads.update_batch_progress(
            db, batch_id, 0, 0, BatchStatus.error,
            error=f"Error inesperado: {str(e)[:400]}"
        )
    finally:
        db.close()
