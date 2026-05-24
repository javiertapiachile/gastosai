"""
Dependencias de FastAPI para autenticación.
Inyectables en cualquier endpoint que requiera usuario autenticado.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth.auth_service import verificar_token, get_usuario_por_id

# Esquema Bearer — lee el token del header Authorization: Bearer <token>
bearer_scheme = HTTPBearer(auto_error=False)


def get_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependencia que extrae y valida el JWT del header Authorization.
    Lanza 401 si el token es inválido o el usuario no existe.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verificar_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub", 0))
    usuario = get_usuario_por_id(db, user_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return usuario


def get_usuario_admin(usuario: User = Depends(get_usuario_actual)) -> User:
    """Dependencia adicional que además verifica que el usuario sea admin."""
    if not usuario.es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return usuario
