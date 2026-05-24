"""
Clasificador principal optimizado.
Orden de prioridad:
  1. Reglas manuales (sin LLM, instantáneo)
  2. Caché SQLite (sin LLM, instantáneo)
  3. LLM con prompt compacto y lotes de 10 (optimización A+B)
"""

import logging
import traceback
from typing import Callable, Optional
from sqlalchemy.orm import Session

from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import (
    PROMPT_SISTEMA,
    TAMANO_LOTE_OPTIMIZADO,
    CATEGORIAS_BASE,
    construir_prompt_clasificacion,
    parsear_respuesta_compacta,
)
from app.services.classifier.cache import buscar_en_cache, guardar_en_cache
from app.crud.categories import get_categories
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


async def clasificar_transacciones(
    db: Session,
    transacciones: list[Transaction],
    on_progreso: Optional[Callable[[int, int], None]] = None,
) -> dict:
    stats = {
        "total": len(transacciones),
        "desde_reglas": 0,
        "desde_cache": 0,
        "desde_llm": 0,
        "errores": 0,
    }

    if not transacciones:
        return stats

    categorias = get_categories(db, solo_activas=True)
    nombres_categorias = [c.nombre for c in categorias] or CATEGORIAS_BASE
    mapa_categorias = {c.nombre: c.id for c in categorias}
    mapa_id_nombre = {c.id: c.nombre for c in categorias}

    user_id = transacciones[0].user_id if transacciones else None

    # Cargar reglas activas una sola vez
    reglas_activas = []
    if user_id:
        from app.crud.reglas import get_reglas
        reglas_activas = get_reglas(db, user_id, solo_activas=True)

    sin_clasificar: list[Transaction] = []
    clasificadas_total = 0

    for tx in transacciones:
        try:
            # 1. Reglas manuales
            categoria_id = _aplicar_reglas(tx.descripcion_original, reglas_activas)
            if categoria_id is not None:
                categoria_nombre = mapa_id_nombre.get(categoria_id, "Sin categoría")
                _aplicar_clasificacion(
                    db, tx, categoria_nombre,
                    comercio_limpio=_limpiar_nombre(tx.descripcion_original),
                    confianza=1.0, desde_cache=False,
                    mapa_categorias=mapa_categorias,
                    forzar_categoria_id=categoria_id,
                )
                stats["desde_reglas"] += 1
                clasificadas_total += 1
                continue

            # 2. Caché
            entrada = buscar_en_cache(db, tx.descripcion_original)
            if entrada:
                _aplicar_clasificacion(
                    db, tx, entrada.categoria, entrada.comercio_limpio,
                    entrada.confianza, desde_cache=True,
                    mapa_categorias=mapa_categorias,
                )
                stats["desde_cache"] += 1
                clasificadas_total += 1
            else:
                sin_clasificar.append(tx)

        except Exception as e:
            logger.error(f"[clasificador] Error tx.id={tx.id}: {e}")
            stats["errores"] += 1

    if on_progreso and clasificadas_total > 0:
        on_progreso(clasificadas_total, stats["total"])

    if not sin_clasificar:
        logger.info(f"[clasificador] Todo resuelto sin LLM: {stats}")
        return stats

    # 3. LLM para las restantes — lotes de TAMANO_LOTE_OPTIMIZADO
    try:
        llm = get_llm_provider()
    except Exception as e:
        logger.error(f"[clasificador] No se pudo obtener proveedor LLM: {e}")
        stats["errores"] += len(sin_clasificar)
        return stats

    logger.info(
        f"[clasificador] {len(sin_clasificar)} tx van a LLM "
        f"(lotes de {TAMANO_LOTE_OPTIMIZADO})"
    )

    for i in range(0, len(sin_clasificar), TAMANO_LOTE_OPTIMIZADO):
        lote = sin_clasificar[i:i + TAMANO_LOTE_OPTIMIZADO]
        descripciones = [tx.descripcion_original for tx in lote]

        try:
            prompt = construir_prompt_clasificacion(descripciones, nombres_categorias)
            respuesta = await llm.completar(PROMPT_SISTEMA, prompt)

            logger.debug(f"[clasificador] Respuesta LLM lote {i//TAMANO_LOTE_OPTIMIZADO+1}: {repr(respuesta[:200])}")

            resultados = parsear_respuesta_compacta(respuesta, descripciones, nombres_categorias)

            for resultado in resultados:
                idx = resultado.get("indice", -1)
                if idx < 0 or idx >= len(lote):
                    continue

                tx = lote[idx]
                categoria = resultado.get("categoria", "Sin categoría")
                comercio = resultado.get("comercio_limpio") or tx.descripcion_original
                confianza = float(resultado.get("confianza", 0.8))

                try:
                    guardar_en_cache(
                        db, tx.descripcion_original,
                        categoria, comercio, confianza, llm.nombre,
                    )
                    _aplicar_clasificacion(
                        db, tx, categoria, comercio, confianza,
                        desde_cache=False, mapa_categorias=mapa_categorias,
                    )
                    stats["desde_llm"] += 1
                    clasificadas_total += 1
                except Exception as e:
                    logger.error(f"[clasificador] Error guardando tx.id={tx.id}: {e}")
                    stats["errores"] += 1

        except Exception as e:
            logger.error(
                f"[clasificador] Error lote {i//TAMANO_LOTE_OPTIMIZADO+1}: "
                f"{e}\n{traceback.format_exc()}"
            )
            stats["errores"] += len(lote)
            clasificadas_total += len(lote)

        if on_progreso:
            on_progreso(clasificadas_total, stats["total"])

    logger.info(f"[clasificador] Completado: {stats}")
    return stats


def _limpiar_nombre(descripcion: str) -> str:
    """Limpieza básica sin LLM."""
    import re
    texto = re.sub(r'\s*#\d+', '', descripcion)
    texto = re.sub(r'\s+\d{4,}$', '', texto)
    return re.sub(r'\s+', ' ', texto).strip().title()


def _aplicar_reglas(descripcion: str, reglas: list) -> int | None:
    desc_lower = descripcion.lower().strip()
    for regla in reglas:
        patron = regla.patron.lower().strip()
        if regla.tipo_match == "contiene" and patron in desc_lower:
            return regla.categoria_id
        elif regla.tipo_match == "empieza" and desc_lower.startswith(patron):
            return regla.categoria_id
        elif regla.tipo_match == "exacto" and desc_lower == patron:
            return regla.categoria_id
    return None


def _aplicar_clasificacion(
    db: Session,
    tx: Transaction,
    categoria_nombre: str,
    comercio_limpio: str,
    confianza: float,
    desde_cache: bool,
    mapa_categorias: dict,
    forzar_categoria_id: int | None = None,
) -> None:
    import unicodedata

    def norm(s):
        s = s.lower()
        s = unicodedata.normalize("NFD", s)
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

    categoria_id = forzar_categoria_id
    if categoria_id is None:
        categoria_id = mapa_categorias.get(categoria_nombre)
        if categoria_id is None:
            cat_norm = norm(categoria_nombre)
            for nombre, cid in mapa_categorias.items():
                if norm(nombre) == cat_norm:
                    categoria_id = cid
                    break

    tx.categoria_id = categoria_id
    tx.comercio_limpio = comercio_limpio
    tx.confianza_clasificacion = confianza
    tx.clasificado_por_cache = desde_cache
    db.add(tx)
    db.commit()
    db.refresh(tx)


async def verificar_conexion_llm() -> dict:
    try:
        llm = get_llm_provider()
        respuesta = await llm.completar("Responde solo OK.", "OK")
        return {"ok": True, "proveedor": llm.nombre, "respuesta": respuesta.strip()[:50]}
    except Exception as e:
        return {"ok": False, "proveedor": "desconocido", "error": str(e)}
