"""
Clasificador principal de transacciones.

Bugs corregidos en Fase A:
  - Bug 3: _aplicar_clasificacion usaba update_transaction() + setattr() en conflicto
  - Bug 4: mapa_categorias usaba .lower() pero lookup no coincidía con tildes
  - Bug 1: errores ahora se loguean con traceback completo
"""

import json
import re
import logging
import traceback
from sqlalchemy.orm import Session

from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import (
    PROMPT_SISTEMA,
    construir_prompt_clasificacion,
    CATEGORIAS_BASE,
)
from app.services.classifier.cache import buscar_en_cache, guardar_en_cache
from app.crud.categories import get_categories
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

TAMANO_LOTE_LLM = 20


async def clasificar_transacciones(
    db: Session,
    transacciones: list[Transaction],
) -> dict:
    """
    Clasifica transacciones usando caché + LLM.
    Retorna estadísticas del proceso.
    """
    stats = {"total": len(transacciones), "desde_cache": 0, "desde_llm": 0, "errores": 0}

    if not transacciones:
        return stats

    categorias = get_categories(db, solo_activas=True)
    nombres_categorias = [c.nombre for c in categorias] or CATEGORIAS_BASE

    # BUGFIX 4: usar el nombre exacto (con tildes y mayúsculas) como clave
    # En vez de .lower() que pierde las tildes y genera mismatches
    mapa_categorias = {c.nombre: c.id for c in categorias}

    sin_cache: list[Transaction] = []

    for tx in transacciones:
        try:
            entrada_cache = buscar_en_cache(db, tx.descripcion_original)
            if entrada_cache:
                _aplicar_clasificacion(
                    db, tx,
                    categoria_nombre=entrada_cache.categoria,
                    comercio_limpio=entrada_cache.comercio_limpio,
                    confianza=entrada_cache.confianza,
                    desde_cache=True,
                    mapa_categorias=mapa_categorias,
                )
                stats["desde_cache"] += 1
            else:
                sin_cache.append(tx)
        except Exception as e:
            logger.error(f"[clasificador] Error buscando caché tx.id={tx.id}: {e}")
            stats["errores"] += 1

    # Clasificar en lotes con LLM
    try:
        llm = get_llm_provider()
    except Exception as e:
        logger.error(f"[clasificador] No se pudo obtener proveedor LLM: {e}")
        stats["errores"] += len(sin_cache)
        return stats

    for i in range(0, len(sin_cache), TAMANO_LOTE_LLM):
        lote = sin_cache[i:i + TAMANO_LOTE_LLM]
        descripciones = [tx.descripcion_original for tx in lote]

        try:
            resultados = await _llamar_llm_lote(llm, descripciones, nombres_categorias)

            # Construir mapa indice → resultado
            mapa_resultados = {r.get("indice"): r for r in resultados if "indice" in r}

            for idx, tx in enumerate(lote):
                resultado = mapa_resultados.get(idx)
                if not resultado:
                    logger.warning(f"[clasificador] Sin resultado LLM para índice {idx} (tx.id={tx.id})")
                    stats["errores"] += 1
                    continue

                categoria = resultado.get("categoria", "Sin categoría")
                comercio = resultado.get("comercio_limpio") or tx.descripcion_original
                confianza = float(resultado.get("confianza", 0.7))

                # Validar que la categoría existe exactamente
                if categoria not in nombres_categorias:
                    # Intentar match case-insensitive como fallback
                    categoria = _buscar_categoria_flexible(categoria, nombres_categorias)

                try:
                    guardar_en_cache(
                        db,
                        descripcion=tx.descripcion_original,
                        categoria=categoria,
                        comercio_limpio=comercio,
                        confianza=confianza,
                        proveedor=llm.nombre,
                    )
                    _aplicar_clasificacion(
                        db, tx,
                        categoria_nombre=categoria,
                        comercio_limpio=comercio,
                        confianza=confianza,
                        desde_cache=False,
                        mapa_categorias=mapa_categorias,
                    )
                    stats["desde_llm"] += 1
                except Exception as e:
                    logger.error(f"[clasificador] Error guardando tx.id={tx.id}: {e}\n{traceback.format_exc()}")
                    stats["errores"] += 1

        except Exception as e:
            logger.error(f"[clasificador] Error en lote {i//TAMANO_LOTE_LLM + 1}: {e}\n{traceback.format_exc()}")
            stats["errores"] += len(lote)

    logger.info(f"[clasificador] Completado: {stats}")
    return stats


def _buscar_categoria_flexible(categoria_llm: str, nombres: list[str]) -> str:
    """
    Busca una categoría ignorando mayúsculas/tildes.
    Retorna 'Sin categoría' si no hay match.
    """
    import unicodedata

    def normalizar(s: str) -> str:
        s = s.lower()
        s = unicodedata.normalize("NFD", s)
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

    cat_norm = normalizar(categoria_llm)
    for nombre in nombres:
        if normalizar(nombre) == cat_norm:
            return nombre

    return "Sin categoría"


def _aplicar_clasificacion(
    db: Session,
    tx: Transaction,
    categoria_nombre: str,
    comercio_limpio: str,
    confianza: float,
    desde_cache: bool,
    mapa_categorias: dict[str, int],
) -> None:
    """
    Actualiza la transacción directamente con setattr + un solo commit.
    BUGFIX 3: eliminado update_transaction() que generaba doble commit en conflicto.
    """
    categoria_id = mapa_categorias.get(categoria_nombre)

    # Si no hay match exacto, intentar con el nombre limpio
    if categoria_id is None and categoria_nombre != "Sin categoría":
        categoria_nombre_fallback = _buscar_categoria_flexible(categoria_nombre, list(mapa_categorias.keys()))
        categoria_id = mapa_categorias.get(categoria_nombre_fallback)

    # Actualizar todos los campos en un solo paso
    tx.categoria_id = categoria_id
    tx.comercio_limpio = comercio_limpio
    tx.confianza_clasificacion = confianza
    tx.clasificado_por_cache = desde_cache

    # Un solo commit para todos los cambios
    db.add(tx)
    db.commit()
    db.refresh(tx)


async def _llamar_llm_lote(llm, descripciones: list[str], categorias: list[str]) -> list[dict]:
    prompt_usuario = construir_prompt_clasificacion(descripciones, categorias)
    respuesta = await llm.completar(PROMPT_SISTEMA, prompt_usuario)
    return _parsear_respuesta(respuesta)


def _parsear_respuesta(texto: str) -> list[dict]:
    texto = texto.strip()

    if "```" in texto:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', texto)
        if match:
            texto = match.group(1).strip()

    inicio = texto.find("{")
    fin = texto.rfind("}") + 1
    if inicio == -1 or fin == 0:
        raise ValueError(f"No se encontró JSON en la respuesta: {texto[:300]}")

    datos = json.loads(texto[inicio:fin])
    return datos.get("clasificaciones", [])


async def verificar_conexion_llm() -> dict:
    try:
        llm = get_llm_provider()
        respuesta = await llm.completar(
            "Eres un asistente útil.",
            "Responde solo 'OK' para confirmar que estás operativo.",
        )
        return {
            "ok": True,
            "proveedor": llm.nombre,
            "respuesta": respuesta.strip()[:50],
        }
    except Exception as e:
        return {
            "ok": False,
            "proveedor": "desconocido",
            "error": str(e),
        }
