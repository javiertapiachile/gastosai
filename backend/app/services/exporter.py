"""
Servicio de exportación de transacciones.
Genera CSV o JSON descargable con todos los campos relevantes.
"""

import csv
import json
import io
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.category import Category
from app.crud.transactions import get_transactions


def exportar_csv(
    db: Session,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    categoria_id: Optional[int] = None,
) -> bytes:
    """
    Genera un archivo CSV con las transacciones filtradas.
    Retorna bytes listos para enviar como respuesta HTTP.
    """
    items, _ = get_transactions(
        db,
        pagina=1,
        por_pagina=100_000,  # Exportar todo
        mes=mes,
        anio=anio,
        categoria_id=categoria_id,
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    # Encabezados
    writer.writerow([
        "Fecha",
        "Descripcion Original",
        "Comercio Limpio",
        "Monto",
        "Tipo",
        "Categoria",
        "Confianza IA",
        "Revisado",
        "RUT Comercio",
    ])

    for tx in items:
        writer.writerow([
            tx.fecha.strftime("%Y-%m-%d") if tx.fecha else "",
            tx.descripcion_original,
            tx.comercio_limpio or "",
            tx.monto,
            "Cargo" if tx.es_cargo else "Abono",
            tx.categoria.nombre if tx.categoria else "Sin categoría",
            f"{tx.confianza_clasificacion:.2f}" if tx.confianza_clasificacion else "",
            "Sí" if tx.revisado_por_usuario else "No",
            tx.rut_comercio or "",
        ])

    return output.getvalue().encode("utf-8-sig")  # UTF-8 con BOM para Excel


def exportar_json(
    db: Session,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    categoria_id: Optional[int] = None,
) -> bytes:
    """
    Genera un archivo JSON con las transacciones filtradas.
    """
    items, total = get_transactions(
        db,
        pagina=1,
        por_pagina=100_000,
        mes=mes,
        anio=anio,
        categoria_id=categoria_id,
    )

    datos = {
        "total": total,
        "exportado_en": date.today().isoformat(),
        "transacciones": [
            {
                "id": tx.id,
                "fecha": tx.fecha.strftime("%Y-%m-%d") if tx.fecha else None,
                "descripcion_original": tx.descripcion_original,
                "comercio_limpio": tx.comercio_limpio,
                "monto": tx.monto,
                "es_cargo": tx.es_cargo,
                "categoria": tx.categoria.nombre if tx.categoria else None,
                "confianza_clasificacion": tx.confianza_clasificacion,
                "revisado_por_usuario": tx.revisado_por_usuario,
                "rut_comercio": tx.rut_comercio,
            }
            for tx in items
        ],
    }

    return json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
