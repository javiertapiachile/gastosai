"""
Endpoint de subida de archivos.
Fase A: logging mejorado + manejo correcto de errores en background task.
"""

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
from app.services.parser import get_parser
from app.services.classifier import clasificar_transacciones
from app.utils.file_utils import validar_extension, validar_tamanio, limpiar_nombre

logger = logging.getLogger(__name__)

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


@router.post("/reclasificar/{batch_id}", status_code=202)
async def reclasificar_batch(
    batch_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Endpoint de diagnóstico y recuperación: relanza la clasificación LLM
    sobre un batch ya importado. Útil cuando la clasificación falló silenciosamente.
    """
    batch = crud_uploads.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch no encontrado")

    txs = db.query(Transaction).filter(Transaction.batch_id == batch_id).all()
    if not txs:
        raise HTTPException(status_code=400, detail="El batch no tiene transacciones")

    background_tasks.add_task(_reclasificar_background, batch_id=batch_id)
    return {"mensaje": f"Reclasificación iniciada para {len(txs)} transacciones", "batch_id": batch_id}


@router.post("/", response_model=UploadBatchOut, status_code=202)
async def subir_archivo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
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
    Background task con manejo de errores completo y logging detallado.
    BUGFIX 1: errores ya no se pierden silenciosamente.
    """
    db = SessionLocal()
    try:
        logger.info(f"[batch {batch_id}] Iniciando procesamiento de '{nombre_archivo}'")
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.procesando)

        # Fase 1: Parseo
        try:
            parser = get_parser(tipo_archivo)
            resultado = await parser.parsear(contenido, nombre_archivo)
        except Exception as e:
            msg = f"Error parseando archivo: {e}"
            logger.error(f"[batch {batch_id}] {msg}\n{traceback.format_exc()}")
            crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
            return

        if resultado.errores:
            msg = "; ".join(resultado.errores)
            logger.error(f"[batch {batch_id}] Errores de parseo: {msg}")
            if not resultado.transacciones:
                crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
                return

        if not resultado.transacciones:
            msg = "El archivo no contiene transacciones válidas"
            logger.warning(f"[batch {batch_id}] {msg}")
            crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
            return

        total = len(resultado.transacciones)
        logger.info(f"[batch {batch_id}] Parseadas {total} transacciones")
        crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.procesando)

        # Fase 2: Inserción en DB
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
                }
                for tx in lote_raw
            ]
            try:
                crud_tx.create_transactions_bulk(db, datos)
                insertadas += len(lote_raw)
                crud_uploads.update_batch_progress(db, batch_id, insertadas, total, BatchStatus.procesando)
            except Exception as e:
                logger.error(f"[batch {batch_id}] Error insertando lote {i//LOTE}: {e}\n{traceback.format_exc()}")

        logger.info(f"[batch {batch_id}] {insertadas}/{total} transacciones insertadas")

        # Fase 3: Clasificación LLM
        crud_uploads.update_batch_progress(db, batch_id, 0, total, BatchStatus.clasificando)

        txs_para_clasificar = (
            db.query(Transaction)
            .filter(Transaction.batch_id == batch_id)
            .all()
        )

        logger.info(f"[batch {batch_id}] Clasificando {len(txs_para_clasificar)} transacciones con LLM")

        try:
            stats = await clasificar_transacciones(db, txs_para_clasificar)
            logger.info(f"[batch {batch_id}] Clasificación completada: {stats}")
        except Exception as e:
            # La clasificación puede fallar sin invalidar el import
            logger.error(f"[batch {batch_id}] Error en clasificación: {e}\n{traceback.format_exc()}")

        crud_uploads.update_batch_progress(db, batch_id, total, total, BatchStatus.completado)
        logger.info(f"[batch {batch_id}] Procesamiento completado exitosamente")

    except Exception as e:
        msg = f"Error inesperado: {str(e)[:400]}"
        logger.error(f"[batch {batch_id}] {msg}\n{traceback.format_exc()}")
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.error, error=msg)
    finally:
        db.close()


async def _reclasificar_background(batch_id: int) -> None:
    """Reclasifica todas las transacciones de un batch existente."""
    db = SessionLocal()
    try:
        txs = db.query(Transaction).filter(Transaction.batch_id == batch_id).all()
        logger.info(f"[reclasificar batch {batch_id}] {len(txs)} transacciones")
        stats = await clasificar_transacciones(db, txs)
        logger.info(f"[reclasificar batch {batch_id}] {stats}")
    except Exception as e:
        logger.error(f"[reclasificar batch {batch_id}] Error: {e}\n{traceback.format_exc()}")
    finally:
        db.close()
