"""Operaciones CRUD para categorías."""

from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_name(db: Session, nombre: str) -> Category | None:
    return db.query(Category).filter(Category.nombre == nombre).first()


def get_categories(db: Session, solo_activas: bool = False) -> list[Category]:
    query = db.query(Category)
    if solo_activas:
        query = query.filter(Category.activa == True)
    return query.order_by(Category.nombre).all()


def create_category(db: Session, category: CategoryCreate) -> Category:
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category | None:
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    # Solo actualiza los campos enviados
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(db_category, field, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> bool:
    """Elimina categoría solo si no es del sistema."""
    db_category = get_category(db, category_id)
    if not db_category or db_category.es_sistema:
        return False
    db.delete(db_category)
    db.commit()
    return True
