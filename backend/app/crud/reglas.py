"""Operaciones CRUD para reglas de clasificación manual."""

from sqlalchemy.orm import Session
from app.models.regla import ClasificacionRegla
from app.schemas.regla import ReglaCreate, ReglaUpdate


def get_reglas(db: Session, user_id: int, solo_activas: bool = False) -> list[ClasificacionRegla]:
    query = db.query(ClasificacionRegla).filter(ClasificacionRegla.user_id == user_id)
    if solo_activas:
        query = query.filter(ClasificacionRegla.activa == True)
    return query.order_by(ClasificacionRegla.prioridad.desc(), ClasificacionRegla.id).all()


def get_regla(db: Session, regla_id: int, user_id: int) -> ClasificacionRegla | None:
    return (
        db.query(ClasificacionRegla)
        .filter(ClasificacionRegla.id == regla_id, ClasificacionRegla.user_id == user_id)
        .first()
    )


def create_regla(db: Session, data: ReglaCreate, user_id: int) -> ClasificacionRegla:
    regla = ClasificacionRegla(**data.model_dump(), user_id=user_id)
    db.add(regla)
    db.commit()
    db.refresh(regla)
    return regla


def update_regla(db: Session, regla_id: int, user_id: int, data: ReglaUpdate) -> ClasificacionRegla | None:
    regla = get_regla(db, regla_id, user_id)
    if not regla:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(regla, field, value)
    db.commit()
    db.refresh(regla)
    return regla


def delete_regla(db: Session, regla_id: int, user_id: int) -> bool:
    regla = get_regla(db, regla_id, user_id)
    if not regla:
        return False
    db.delete(regla)
    db.commit()
    return True


def aplicar_reglas(
    db: Session,
    descripcion: str,
    user_id: int,
) -> int | None:
    """
    Aplica las reglas activas del usuario a una descripción.
    Retorna el categoria_id de la primera regla que coincida, o None.
    Las reglas se evalúan en orden de prioridad descendente.
    """
    reglas = get_reglas(db, user_id, solo_activas=True)
    desc_lower = descripcion.lower().strip()

    for regla in reglas:
        patron = regla.patron.lower().strip()
        coincide = False

        if regla.tipo_match == "contiene":
            coincide = patron in desc_lower
        elif regla.tipo_match == "empieza":
            coincide = desc_lower.startswith(patron)
        elif regla.tipo_match == "exacto":
            coincide = desc_lower == patron

        if coincide:
            return regla.categoria_id

    return None
