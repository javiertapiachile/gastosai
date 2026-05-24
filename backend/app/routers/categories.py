"""Endpoints CRUD para categorías — requieren autenticación."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.crud import categories as crud
from app.dependencies import get_usuario_actual

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryOut])
async def listar_categorias(
    solo_activas: bool = False,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return crud.get_categories(db, solo_activas=solo_activas)


@router.get("/{category_id}", response_model=CategoryOut)
async def obtener_categoria(
    category_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    cat = crud.get_category(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    data: CategoryCreate,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    if crud.get_category_by_name(db, data.nombre):
        raise HTTPException(status_code=409, detail=f"Ya existe la categoría '{data.nombre}'")
    return crud.create_category(db, data)


@router.patch("/{category_id}", response_model=CategoryOut)
async def actualizar_categoria(
    category_id: int,
    data: CategoryUpdate,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    cat = crud.update_category(db, category_id, data)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_categoria(
    category_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    eliminada = crud.delete_category(db, category_id)
    if not eliminada:
        raise HTTPException(status_code=400, detail="No se puede eliminar: no encontrada o es del sistema")
