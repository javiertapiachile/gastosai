"""
Endpoints de exportación de transacciones.
Genera archivos descargables en CSV o JSON.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.services.exporter import exportar_csv, exportar_json

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
async def descargar_csv(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Descarga todas las transacciones (con filtros opcionales) en formato CSV.
    Compatible con Excel (UTF-8 con BOM, separador punto y coma).
    """
    contenido = exportar_csv(db, mes=mes, anio=anio, categoria_id=categoria_id)

    # Nombre del archivo con fecha
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
    db: Session = Depends(get_db),
):
    """
    Descarga todas las transacciones en formato JSON estructurado.
    Útil para importar en otras herramientas o hacer análisis.
    """
    contenido = exportar_json(db, mes=mes, anio=anio, categoria_id=categoria_id)

    sufijo = f"_{anio}" if anio else ""
    sufijo += f"_{mes:02d}" if mes else ""
    nombre = f"gastosai_transacciones{sufijo}_{date.today().isoformat()}.json"

    return Response(
        content=contenido,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
