"""Servicio de autenticación local con instalación de reglas al registrar."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.environ.get("JWT_SECRET", "gastosai-local-secret-cambia-esto-en-produccion")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password_plano: str, hashed: str) -> bool:
    return pwd_context.verify(password_plano, hashed)


def crear_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def autenticar_usuario(db: Session, email: str, password: str) -> Optional[User]:
    usuario = db.query(User).filter(User.email == email.lower()).first()
    if not usuario:
        return None
    if not verificar_password(password, usuario.hashed_password):
        return None
    if not usuario.activo:
        return None
    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()
    return usuario


def registrar_usuario(
    db: Session,
    email: str,
    nombre: str,
    password: str,
    es_admin: bool = False,
) -> User:
    existente = db.query(User).filter(User.email == email.lower()).first()
    if existente:
        raise ValueError(f"Ya existe una cuenta con el email {email}")

    usuario = User(
        email=email.lower(),
        nombre=nombre,
        hashed_password=hashear_password(password),
        es_admin=es_admin,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # Instalar reglas de clasificación por defecto
    try:
        from app.services.reglas_updater import instalar_reglas_usuario
        n = instalar_reglas_usuario(db, usuario.id)
        import logging
        logging.getLogger(__name__).info(
            f"[auth] {n} reglas instaladas para usuario {usuario.email}"
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[auth] Error instalando reglas: {e}")

    return usuario


def get_usuario_por_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id, User.activo == True).first()


def contar_usuarios(db: Session) -> int:
    return db.query(User).count()
