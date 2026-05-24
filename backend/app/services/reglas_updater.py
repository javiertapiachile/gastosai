"""
Servicio de actualización de reglas de clasificación.

Responsabilidades:
  1. Instalar reglas default para usuarios nuevos
  2. Actualizar reglas existentes con nuevos patrones (sin borrar personalizaciones)
  3. Tarea programada que corre al arrancar y puede llamarse manualmente
"""

import logging
from sqlalchemy.orm import Session

from app.models.regla import ClasificacionRegla
from app.models.category import Category
from app.services.reglas_default import REGLAS_DEFAULT

logger = logging.getLogger(__name__)


def instalar_reglas_usuario(db: Session, user_id: int) -> int:
    """
    Instala las reglas default para un usuario recién creado.
    Retorna el número de reglas insertadas.
    """
    return _sincronizar_reglas(db, user_id, solo_nuevas=True)


def actualizar_reglas_usuario(db: Session, user_id: int) -> dict:
    """
    Actualiza las reglas de un usuario:
    - Agrega reglas nuevas que no tenga
    - Actualiza la prioridad de reglas existentes si cambió
    - NO elimina reglas personalizadas (las que no están en REGLAS_DEFAULT)
    Retorna stats del proceso.
    """
    return _sincronizar_reglas(db, user_id, solo_nuevas=False)


def _sincronizar_reglas(db: Session, user_id: int, solo_nuevas: bool) -> dict | int:
    """Lógica central de sincronización."""

    # Construir mapa categoria_nombre → categoria_id
    cats = db.query(Category).filter(Category.activa == True).all()
    mapa_cats = {c.nombre: c.id for c in cats}

    # Reglas existentes del usuario (patron → regla)
    reglas_existentes = {
        r.patron.lower(): r
        for r in db.query(ClasificacionRegla).filter(
            ClasificacionRegla.user_id == user_id
        ).all()
    }

    insertadas = 0
    actualizadas = 0
    omitidas = 0

    for regla_def in REGLAS_DEFAULT:
        patron = regla_def["patron"].lower()
        cat_nombre = regla_def["categoria"]
        cat_id = mapa_cats.get(cat_nombre)

        if not cat_id:
            logger.warning(f"[reglas_updater] Categoría no encontrada: '{cat_nombre}'")
            omitidas += 1
            continue

        if patron in reglas_existentes:
            if solo_nuevas:
                continue
            # Actualizar prioridad si cambió (respeta el resto de cambios del usuario)
            regla_existente = reglas_existentes[patron]
            if regla_existente.prioridad != regla_def["prioridad"]:
                regla_existente.prioridad = regla_def["prioridad"]
                actualizadas += 1
        else:
            # Insertar nueva regla
            nueva = ClasificacionRegla(
                patron=patron,
                tipo_match="contiene",
                categoria_id=cat_id,
                descripcion_regla=regla_def.get("descripcion", ""),
                prioridad=regla_def["prioridad"],
                activa=True,
                user_id=user_id,
            )
            db.add(nueva)
            insertadas += 1

    db.commit()

    stats = {"insertadas": insertadas, "actualizadas": actualizadas, "omitidas": omitidas}
    logger.info(f"[reglas_updater] user_id={user_id}: {stats}")

    return insertadas if solo_nuevas else stats


def actualizar_todos_los_usuarios(db: Session) -> dict:
    """
    Actualiza las reglas de TODOS los usuarios del sistema.
    Llamada por la tarea programada.
    """
    from app.models.user import User
    usuarios = db.query(User).filter(User.activo == True).all()

    total = {"usuarios": len(usuarios), "insertadas": 0, "actualizadas": 0}
    for usuario in usuarios:
        stats = actualizar_reglas_usuario(db, usuario.id)
        total["insertadas"] += stats.get("insertadas", 0)
        total["actualizadas"] += stats.get("actualizadas", 0)

    logger.info(f"[reglas_updater] Actualización global: {total}")
    return total
