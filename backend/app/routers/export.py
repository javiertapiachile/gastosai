"""Endpoints de exportación filtrados por usuario."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.user import User
from app.services.exporter import exportar_csv, exportar_json
from app.dependencies import get_usuario_actual

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
async def descargar_csv(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    categoria_id: Optional[int] = None,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    contenido = exportar_csv(db, mes=mes, anio=anio, categoria_id=categoria_id, user_id=usuario.id)
    sufijo = f"_{anio}" if anio else ""
    sufijo += f"_{mes:02d}" if mes else ""
    nombre = f"gastosai_transacciones{sufijo}_{date.today().isoformat()}.csv"
    return Response(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/json")
async def descargar_json(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    categoria_id: Optional[int] = None,
    usuario: User = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    contenido = exportar_json(db, mes=mes, anio=anio, categoria_id=categoria_id, user_id=usuario.id)
    sufijo = f"_{anio}" if anio else ""
    sufijo += f"_{mes:02d}" if mes else ""
    nombre = f"gastosai_transacciones{sufijo}_{date.today().isoformat()}.json"
    return Response(
        content=contenido,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
