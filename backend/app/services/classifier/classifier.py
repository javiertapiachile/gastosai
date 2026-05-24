"""
Clasificador principal de transacciones.

Flujo por cada lote de descripciones:
  1. Buscar en caché SQLite → retornar sin llamar al LLM
  2. Las que no están en caché → enviar al LLM en grupos de 20
  3. Guardar resultados en caché
  4. Actualizar la transacción en la DB con categoría + comercio limpio
"""

import json
import re
from typing import Optional
from sqlalchemy.orm import Session

from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import (
    PROMPT_SISTEMA,
    construir_prompt_clasificacion,
    CATEGORIAS_BASE,
)
from app.services.classifier.cache import buscar_en_cache, guardar_en_cache
from app.crud.categories import get_categories
from app.crud.transactions import update_transaction
from app.schemas.transaction import TransactionUpdate
from app.models.transaction import Transaction


# Número máximo de transacciones por llamada al LLM
TAMANO_LOTE_LLM = 20


async def clasificar_transacciones(
    db: Session,
    transacciones: list[Transaction],
) -> dict:
    """
    Clasifica una lista de transacciones usando caché + LLM.

    Returns:
        Dict con estadísticas: total, desde_cache, desde_llm, errores
    """
    stats = {"total": len(transacciones), "desde_cache": 0, "desde_llm": 0, "errores": 0}

    if not transacciones:
        return stats

    # Obtener categorías activas de la DB
    categorias = get_categories(db, solo_activas=True)
    nombres_categorias = [c.nombre for c in categorias] or CATEGORIAS_BASE
    mapa_categorias = {c.nombre.lower(): c.id for c in categorias}

    # Separar las que ya están en caché
    sin_cache: list[Transaction] = []
    for tx in transacciones:
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

    # Clasificar en lotes las que no estaban en caché
    llm = get_llm_provider()

    for i in range(0, len(sin_cache), TAMANO_LOTE_LLM):
        lote = sin_cache[i:i + TAMANO_LOTE_LLM]
        descripciones = [tx.descripcion_original for tx in lote]

        try:
            resultados = await _llamar_llm_lote(llm, descripciones, nombres_categorias)

            for resultado in resultados:
                idx = resultado.get("indice", -1)
                if idx < 0 or idx >= len(lote):
                    continue

                tx = lote[idx]
                categoria = resultado.get("categoria", "Sin categoría")
                comercio = resultado.get("comercio_limpio", tx.descripcion_original)
                confianza = float(resultado.get("confianza", 0.7))

                # Validar que la categoría existe
                if categoria not in nombres_categorias:
                    categoria = "Sin categoría"

                # Guardar en caché
                guardar_en_cache(
                    db,
                    descripcion=tx.descripcion_original,
                    categoria=categoria,
                    comercio_limpio=comercio,
                    confianza=confianza,
                    proveedor=llm.nombre,
                )

                # Aplicar a la transacción
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
            print(f"[clasificador] Error en lote {i//TAMANO_LOTE_LLM + 1}: {e}")
            stats["errores"] += len(lote)

    return stats


def _aplicar_clasificacion(
    db: Session,
    tx: Transaction,
    categoria_nombre: str,
    comercio_limpio: str,
    confianza: float,
    desde_cache: bool,
    mapa_categorias: dict[str, int],
) -> None:
    """Actualiza la transacción en la DB con la clasificación obtenida."""
    categoria_id = mapa_categorias.get(categoria_nombre.lower())

    update_transaction(
        db,
        tx.id,
        TransactionUpdate(categoria_id=categoria_id),
    )

    # Actualizar campos adicionales directamente
    tx.comercio_limpio = comercio_limpio
    tx.confianza_clasificacion = confianza
    tx.clasificado_por_cache = desde_cache
    db.commit()


async def _llamar_llm_lote(
    llm,
    descripciones: list[str],
    categorias: list[str],
) -> list[dict]:
    """Llama al LLM con un lote de descripciones y parsea la respuesta JSON."""
    prompt_usuario = construir_prompt_clasificacion(descripciones, categorias)

    respuesta = await llm.completar(PROMPT_SISTEMA, prompt_usuario)
    return _parsear_respuesta(respuesta)


def _parsear_respuesta(texto: str) -> list[dict]:
    """
    Extrae el JSON de la respuesta del LLM.
    Maneja casos donde el modelo añade markdown o texto extra.
    """
    texto = texto.strip()

    # Remover bloques markdown si los hay
    if "```" in texto:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', texto)
        if match:
            texto = match.group(1).strip()

    # Buscar el primer objeto JSON válido
    inicio = texto.find("{")
    fin = texto.rfind("}") + 1
    if inicio == -1 or fin == 0:
        raise ValueError(f"No se encontró JSON en la respuesta: {texto[:200]}")

    datos = json.loads(texto[inicio:fin])
    return datos.get("clasificaciones", [])


async def verificar_conexion_llm() -> dict:
    """
    Verifica que el LLM configurado responde correctamente.
    Usado por el endpoint de configuración.
    """
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
