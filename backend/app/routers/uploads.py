"""Endpoints de uploads con guardado en disco, deduplicación y reprocesamiento."""

import os
import hashlib
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

# Directorio donde se guardan los archivos subidos
UPLOADS_DIR = "/app/data/uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _guardar_archivo(contenido: bytes, nombre: str, batch_id: int) -> str:
    """Guarda el archivo en disco y retorna la ruta."""
    ruta = os.path.join(UPLOADS_DIR, f"{batch_id}_{nombre}")
    with open(ruta, "wb") as f:
        f.write(contenido)
    return ruta


def _leer_archivo(ruta: str) -> bytes | None:
    """Lee un archivo desde disco. Retorna None si no existe."""
    try:
        with open(ruta, "rb") as f:
            return f.read()
    except (FileNotFoundError, OSError):
        return None


@router.get("/", response_model=list[UploadBatchOut])
async def listar_uploads(
    pagina: int = 1,
    por_pagina: int = 20,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    from app.models.upload import UploadBatch
    return (
        db.query(UploadBatch)
        .filter(UploadBatch.user_id == usuario.id)
        .order_by(UploadBatch.creado_en.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )


@router.get("/meta")
async def meta_uploads(
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    from app.models.upload import UploadBatch
    total = db.query(UploadBatch).filter(UploadBatch.user_id == usuario.id).count()
    return {"total": total}


@router.get("/bulk/estado", response_model=list[UploadBatchOut])
async def estado_bulk(
    ids: str,  # ids separados por coma: "1,2,3"
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """
    Retorna el estado de múltiples batches en una sola llamada.
    Reemplaza N llamadas individuales durante el polling.
    """
    from app.models.upload import UploadBatch
    try:
        batch_ids = [int(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        return []

    return (
        db.query(UploadBatch)
        .filter(
            UploadBatch.id.in_(batch_ids),
            UploadBatch.user_id == usuario.id,
        )
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

    # Eliminar archivo del disco si existe
    if batch.ruta_archivo:
        try:
            os.remove(batch.ruta_archivo)
        except OSError:
            pass

    crud_uploads.delete_batch(db, batch_id)


@router.post("/{batch_id}/reclasificar", status_code=202)
async def reclasificar_batch(
    batch_id: int,
    background_tasks: BackgroundTasks,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """
    Si el batch tiene transacciones → reclasifica con LLM.
    Si el batch está en error (0 tx) → reprocesa el archivo completo desde disco.
    """
    batch = crud_uploads.get_batch(db, batch_id)
    if not batch or batch.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Batch no encontrado")

    total_tx = db.query(Transaction).filter(Transaction.batch_id == batch_id).count()

    # Caso A: tiene transacciones → solo reclasificar
    if total_tx > 0:
        crud_uploads.update_batch_progress(db, batch_id, 0, total_tx, BatchStatus.clasificando)
        background_tasks.add_task(_reclasificar_background, batch_id=batch_id, user_id=usuario.id)
        return {"mensaje": f"Reclasificación iniciada para {total_tx} transacciones", "batch_id": batch_id}

    # Caso B: sin transacciones → reprocesar desde disco
    if not batch.ruta_archivo:
        raise HTTPException(
            status_code=400,
            detail="No se puede reprocesar: archivo original no disponible. Vuelve a subir el archivo."
        )

    contenido = _leer_archivo(batch.ruta_archivo)
    if contenido is None:
        raise HTTPException(
            status_code=400,
            detail="El archivo original ya no está disponible en disco. Vuelve a subir el archivo."
        )

    crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.procesando)
    background_tasks.add_task(
        _procesar_archivo_background,
        batch_id=batch_id,
        contenido=contenido,
        nombre_archivo=batch.nombre_archivo,
        tipo_archivo=batch.tipo_archivo,
        user_id=usuario.id,
        es_reprocesamiento=True,
    )
    return {"mensaje": "Reprocesando archivo completo", "batch_id": batch_id}


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

    # Calcular hash del contenido para detectar duplicados
    hash_contenido = hashlib.sha256(contenido).hexdigest()

    # Verificar si ya existe un batch con el mismo contenido para este usuario
    from app.models.upload import UploadBatch
    duplicado = (
        db.query(UploadBatch)
        .filter(
            UploadBatch.hash_contenido == hash_contenido,
            UploadBatch.user_id == usuario.id,
            UploadBatch.estado == "completado",
        )
        .first()
    )
    if duplicado:
        raise HTTPException(
            status_code=409,
            detail=f"Este archivo ya fue importado el {duplicado.creado_en.strftime('%d/%m/%Y')} "
                   f"({duplicado.total_transacciones} transacciones). "
                   f"Elimina el batch anterior si deseas reimportarlo."
        )

    batch = crud_uploads.create_batch(
        db, UploadBatchCreate(nombre_archivo=nombre_limpio, tipo_archivo=extension)
    )
    batch.user_id = usuario.id
    batch.hash_contenido = hash_contenido

    # Guardar archivo en disco para posible reprocesamiento
    ruta = _guardar_archivo(contenido, nombre_limpio, batch.id)
    batch.ruta_archivo = ruta
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
        hash_contenido = hashlib.sha256(contenido).hexdigest()

        # Saltar duplicados silenciosamente en lote
        from app.models.upload import UploadBatch as UB
        if db.query(UB).filter(
            UB.hash_contenido == hash_contenido,
            UB.user_id == usuario.id,
            UB.estado == "completado",
        ).first():
            logger.info(f"[lote] Archivo '{nombre_limpio}' ya importado, omitiendo")
            continue

        batch = crud_uploads.create_batch(
            db, UploadBatchCreate(nombre_archivo=nombre_limpio, tipo_archivo=extension)
        )
        batch.user_id = usuario.id
        batch.hash_contenido = hash_contenido
        ruta = _guardar_archivo(contenido, nombre_limpio, batch.id)
        batch.ruta_archivo = ruta
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


# ── Background tasks ─────────────────────────────────────────────────────────

async def _procesar_archivo_background(
    batch_id: int, contenido: bytes, nombre_archivo: str,
    tipo_archivo: str, user_id: int, es_reprocesamiento: bool = False,
) -> None:
    db = SessionLocal()
    try:
        logger.info(f"[batch {batch_id}] {'Reprocesando' if es_reprocesamiento else 'Procesando'} '{nombre_archivo}'")
        crud_uploads.update_batch_progress(db, batch_id, 0, 0, BatchStatus.procesando)

        # Si es reprocesamiento, limpiar transacciones anteriores
        if es_reprocesamiento:
            db.query(Transaction).filter(Transaction.batch_id == batch_id).delete()
            db.commit()

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

    def on_progreso(clasificadas: int, total_tx: int) -> None:
        try:
            crud_uploads.update_batch_progress(db, batch_id, clasificadas, total_tx, BatchStatus.clasificando)
        except Exception as e:
            logger.warning(f"[batch {batch_id}] Error actualizando progreso: {e}")

    try:
        stats = await clasificar_transacciones(db, txs, on_progreso=on_progreso)
        logger.info(f"[batch {batch_id}] Clasificación: {stats}")
    except Exception as e:
        logger.error(f"[batch {batch_id}] Error clasificando: {e}\n{traceback.format_exc()}")

    crud_uploads.update_batch_progress(db, batch_id, total, total, BatchStatus.completado)
