"""
Caché de clasificaciones en SQLite.
Evita llamar al LLM dos veces para la misma descripción de comercio.

Estrategia de normalización:
  "COPEC RUTA5 #2341" → "copec ruta" (sin números, sin referencias)
  "COPEC RUTA5 #9871" → "copec ruta" (mismo hash → mismo resultado)
"""

import re
import hashlib
from sqlalchemy.orm import Session
from app.models.cache import ClassificationCache


def _normalizar(descripcion: str) -> str:
    """
    Normaliza una descripción para maximizar los hits de caché.
    Elimina: números de referencia, IDs de sucursal, fechas embebidas.
    """
    texto = descripcion.lower().strip()

    # Remover números de referencia (# seguido de dígitos)
    texto = re.sub(r'#\s*\d+', '', texto)

    # Remover secuencias largas de dígitos (más de 3 dígitos seguidos)
    texto = re.sub(r'\b\d{4,}\b', '', texto)

    # Remover caracteres especiales excepto letras, espacios y *
    texto = re.sub(r'[^a-záéíóúñü\s*]', ' ', texto)

    # Normalizar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Tomar solo las primeras 3 palabras (la raíz del nombre del comercio)
    palabras = texto.split()[:3]
    return " ".join(palabras)


def _hash_descripcion(descripcion_normalizada: str) -> str:
    return hashlib.sha256(descripcion_normalizada.encode()).hexdigest()


def buscar_en_cache(db: Session, descripcion: str) -> ClassificationCache | None:
    """
    Busca la clasificación de una descripción en el caché.
    Retorna None si no existe.
    """
    normalizada = _normalizar(descripcion)
    hash_key = _hash_descripcion(normalizada)

    return (
        db.query(ClassificationCache)
        .filter(ClassificationCache.hash_descripcion == hash_key)
        .first()
    )


def guardar_en_cache(
    db: Session,
    descripcion: str,
    categoria: str,
    comercio_limpio: str,
    confianza: float,
    proveedor: str,
) -> ClassificationCache:
    """
    Guarda o actualiza una clasificación en el caché.
    Si ya existe el hash, actualiza el resultado (el nuevo puede ser mejor).
    """
    normalizada = _normalizar(descripcion)
    hash_key = _hash_descripcion(normalizada)

    existente = (
        db.query(ClassificationCache)
        .filter(ClassificationCache.hash_descripcion == hash_key)
        .first()
    )

    if existente:
        existente.categoria = categoria
        existente.comercio_limpio = comercio_limpio
        existente.confianza = confianza
        existente.proveedor_llm = proveedor
        existente.usos = existente.usos + 1
        db.commit()
        db.refresh(existente)
        return existente

    nueva = ClassificationCache(
        hash_descripcion=hash_key,
        descripcion_normalizada=normalizada,
        categoria=categoria,
        comercio_limpio=comercio_limpio,
        confianza=confianza,
        proveedor_llm=proveedor,
        usos=1,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def contar_entradas_cache(db: Session) -> int:
    """Retorna el número total de entradas en el caché."""
    return db.query(ClassificationCache).count()
