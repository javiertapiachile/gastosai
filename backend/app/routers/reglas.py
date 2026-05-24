"""Endpoints CRUD para reglas de clasificación manual."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.regla import ReglaCreate, ReglaUpdate, ReglaOut
from app.crud import reglas as crud
from app.dependencies import get_usuario_actual

router = APIRouter(prefix="/reglas", tags=["reglas"])


@router.get("/", response_model=list[ReglaOut])
async def listar_reglas(
    solo_activas: bool = False,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return crud.get_reglas(db, usuario.id, solo_activas=solo_activas)


@router.post("/", response_model=ReglaOut, status_code=status.HTTP_201_CREATED)
async def crear_regla(
    data: ReglaCreate,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return crud.create_regla(db, data, usuario.id)


@router.patch("/{regla_id}", response_model=ReglaOut)
async def actualizar_regla(
    regla_id: int,
    data: ReglaUpdate,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    regla = crud.update_regla(db, regla_id, usuario.id, data)
    if not regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return regla


@router.delete("/{regla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_regla(
    regla_id: int,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    if not crud.delete_regla(db, regla_id, usuario.id):
        raise HTTPException(status_code=404, detail="Regla no encontrada")


@router.post("/probar")
async def probar_regla(
    body: dict,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """
    Prueba qué categoría se asignaría a una descripción dada.
    Útil para verificar reglas antes de aplicarlas masivamente.
    """
    descripcion = body.get("descripcion", "")
    categoria_id = crud.aplicar_reglas(db, descripcion, usuario.id)

    if categoria_id:
        from app.crud.categories import get_category
        cat = get_category(db, categoria_id)
        return {
            "descripcion": descripcion,
            "categoria_id": categoria_id,
            "categoria_nombre": cat.nombre if cat else "Desconocida",
            "coincide": True,
        }
    return {"descripcion": descripcion, "coincide": False}


@router.post("/actualizar-default")
async def actualizar_reglas_default(
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """
    Actualiza las reglas del usuario con los últimos patrones default.
    Agrega nuevas reglas sin eliminar las personalizadas.
    """
    from app.services.reglas_updater import actualizar_reglas_usuario
    stats = actualizar_reglas_usuario(db, usuario.id)
    return {
        "mensaje": "Reglas actualizadas correctamente",
        **stats,
    }
