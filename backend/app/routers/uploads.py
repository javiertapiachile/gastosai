"""Endpoints de uploads filtrados por usuario autenticado."""

import logging
import traceback
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.schemas.upload import UploadBatchOut, UploadBatchCreate
from app.crud import uploads as crud_uploads
from app.crud import transactions as crud_tx
from app.models.upload import BatchStatus
from app.models.transaction import Transaction
from app.models.user import User
from app.services.parser import get_parser
from app.services.classifier import clasificar_transacciones
from app.utils.file_utils import validar_extension, validar_tamanio, limpiar_nombre
from app.dependencies import get_usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/", response_model=list[UploadBatchOut])
async def listar_uploads(
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Lista solo los uploads del usuario autenticado."""
    from app.models.upload import UploadBatch
    return (
        db.query(UploadBatch)
        .filter(UploadBatch.user_id == usuario.id)
        .order_by(UploadBatch.creado_en.desc())
        .all()
    )


@router.get("/{batch_id}", response_model=UploadBatchOut)
async def obtener_upload(
    batch_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    batch = crud_uploads.get_batch(db, batch_id)
    if not batch or batch.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    return batch


@router.delete("/{batch_id}", status_code=204)
async def eliminar_upload(
    batch_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    batch = crud_uploads.get_batch(db, batch_id)
    if not batch or batch.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    crud_uploads.delete_batch(db, batch_id)


@router.post("/{batch_id}/reclasificar", status_code=202)
async def reclasificar_batch(
    batch_id: int,
    background_tasks: BackgroundTasks,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    batch = crud_uploads.get_batch(db, batch_id)
    if not batch or batch.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Batch no encontrado")

    total = db.query(Transaction).filter(Transaction.batch_id == batch_id).count()
    if total == 0:
        raise HTTPException(status_code=400, detail="El batch no tiene transacciones")

    crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.clasificando)
    background_tasks.add_task(_reclasificar_background, batch_id=batch_id, user_id=usuario.id)

    return {"mensaje": f"Reclasificación iniciada para {total} transacciones", "batch_id": batch_id}


@router.post("/", response_model=UploadBatchOut, status_code=202)
async def subir_archivo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
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
    # Asignar al usuario
    batch.user_id = usuario.id
    db.commit()

    background_tasks.add_task(
        _procesar_archivo_background,
        batch_id=batch.id,
        contenido=contenido,
        nombre_archivo=nombre_limpio,
        tipo_archivo=extension,
        user_id=usuario.id,
    )
    return batch


@router.post("/lote", response_model=list[UploadBatchOut], status_code=202)
async def subir_archivos_lote(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos")
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Máximo 20 archivos por lote")

    batches_creados = []
    for file in files:
        try:
            extension = validar_extension(file.filename or "")
        except ValueError:
            continue

        contenido = await file.read()
        try:
            validar_tamanio(len(contenido))
        except ValueError:
            continue

        nombre_limpio = limpiar_nombre(file.filename or "archivo")
        batch = crud_uploads.create_batch(
            db, UploadBatchCreate(nombre_archivo=nombre_limpio, tipo_archivo=extension)
        )
        batch.user_id = usuario.id
        db.commit()
        batches_creados.append(batch)

        background_tasks.add_task(
            _procesar_archivo_background,
            batch_id=batch.id,
            contenido=contenido,
            nombre_archivo=nombre_limpio,
            tipo_archivo=extension,
            user_id=usuario.id,
        )

    if not batches_creados:
        raise HTTPException(status_code=400, detail="Ningún archivo válido en el lote")

    return batches_creados


async def _procesar_archivo_background(
    batch_id: int, contenido: bytes, nombre_archivo: str,
    tipo_archivo: str, user_id: int,
) -> None:
    db = SessionLocal()
    try:
        logger.info(f"[batch {batch_id}] Iniciando '{nombre_archivo}' user={user_id}")
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.procesando)

        try:
            parser = get_parser(tipo_archivo)
            resultado = await parser.parsear(contenido, nombre_archivo)
        except Exception as e:
            msg = f"Error parseando: {e}"
            logger.error(f"[batch {batch_id}] {msg}\n{traceback.format_exc()}")
            crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
            return

        if not resultado.transacciones:
            msg = "; ".join(resultado.errores) if resultado.errores else "Sin transacciones válidas"
            crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
            return

        total = len(resultado.transacciones)
        crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.procesando)

        LOTE = 50
        insertadas = 0
        for i in range(0, total, LOTE):
            lote_raw = resultado.transacciones[i:i + LOTE]
            datos = [
                {
                    "descripcion_original": tx.descripcion,
                    "monto": tx.monto,
                    "es_cargo": tx.es_cargo,
                    "fecha": tx.fecha,
                    "rut_comercio": tx.rut_comercio,
                    "batch_id": batch_id,
                    "user_id": user_id,
                }
                for tx in lote_raw
            ]
            crud_tx.create_transactions_bulk(db, datos)
            insertadas += len(lote_raw)
            crud_uploads.update_batch_progress(db, batch_id, insertadas, total, BatchStatus.procesando)

        await _clasificar_batch(db, batch_id, total)

    except Exception as e:
        msg = f"Error inesperado: {str(e)[:400]}"
        logger.error(f"[batch {batch_id}] {msg}\n{traceback.format_exc()}")
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
    finally:
        db.close()


async def _reclasificar_background(batch_id: int, user_id: int) -> None:
    db = SessionLocal()
    try:
        total = db.query(Transaction).filter(Transaction.batch_id == batch_id).count()
        await _clasificar_batch(db, batch_id, total)
    except Exception as e:
        logger.error(f"[reclasificar {batch_id}] {e}\n{traceback.format_exc()}")
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=str(e)[:400])
    finally:
        db.close()


async def _clasificar_batch(db: Session, batch_id: int, total: int) -> None:
    crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.clasificando)
    txs = db.query(Transaction).filter(Transaction.batch_id == batch_id).all()
    try:
        stats = await clasificar_transacciones(db, txs)
        logger.info(f"[batch {batch_id}] Clasificación: {stats}")
    except Exception as e:
        logger.error(f"[batch {batch_id}] Error clasificando: {e}\n{traceback.format_exc()}")
    crud_uploads.update_batch_progress(db, batch_id, total, total, BatchStatus.completado)
