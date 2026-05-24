"""Schemas Pydantic para autenticación y gestión de usuarios."""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    nombre: str
    es_admin: bool
    activo: bool
    creado_en: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UserOut


class ChangePassword(BaseModel):
    password_actual: str
    password_nuevo: str = Field(..., min_length=6, max_length=100)
