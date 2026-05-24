"""
Endpoints de autenticación: registro, login, perfil, cambio de contraseña.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenOut, ChangePassword
from app.services.auth.auth_service import (
    autenticar_usuario, registrar_usuario,
    crear_token, hashear_password, verificar_password, contar_usuarios,
)
from app.dependencies import get_usuario_actual
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registro", response_model=TokenOut, status_code=201)
async def registro(data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario y retorna el token JWT.
    El primer usuario registrado se convierte automáticamente en admin.
    """
    es_admin = contar_usuarios(db) == 0  # Primer usuario = admin

    try:
        usuario = registrar_usuario(
            db,
            email=data.email,
            nombre=data.nombre,
            password=data.password,
            es_admin=es_admin,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    token = crear_token(usuario.id, usuario.email)
    logger.info(f"[auth] Nuevo usuario registrado: {usuario.email} (admin={es_admin})")

    return TokenOut(access_token=token, usuario=UserOut.model_validate(usuario))


@router.post("/login", response_model=TokenOut)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Autentica un usuario y retorna el token JWT."""
    usuario = autenticar_usuario(db, data.email, data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    token = crear_token(usuario.id, usuario.email)
    logger.info(f"[auth] Login exitoso: {usuario.email}")

    return TokenOut(access_token=token, usuario=UserOut.model_validate(usuario))


@router.get("/me", response_model=UserOut)
async def perfil(usuario: User = Depends(get_usuario_actual)):
    """Retorna el perfil del usuario autenticado."""
    return usuario


@router.patch("/password")
async def cambiar_password(
    data: ChangePassword,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Cambia la contraseña del usuario autenticado."""
    if not verificar_password(data.password_actual, usuario.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    usuario.hashed_password = hashear_password(data.password_nuevo)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


@router.get("/usuarios", response_model=list[UserOut])
async def listar_usuarios(
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Lista todos los usuarios (solo admin)."""
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo administradores")
    return db.query(User).order_by(User.creado_en).all()
