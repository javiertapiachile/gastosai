"""
Utilidades para validación y manejo de archivos subidos.
"""

import os
from pathlib import Path
from app.config import settings


# Extensiones y tipos MIME permitidos
EXTENSIONES_PERMITIDAS = {"csv", "xlsx", "pdf"}

MIME_PERMITIDOS = {
    "text/csv",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/pdf",
}


def validar_extension(nombre_archivo: str) -> str:
    """
    Valida que la extensión del archivo sea permitida.
    Retorna la extensión en minúsculas o lanza ValueError.
    """
    if not nombre_archivo:
        raise ValueError("El archivo no tiene nombre")

    extension = Path(nombre_archivo).suffix.lstrip(".").lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(
            f"Formato '.{extension}' no soportado. "
            f"Use: {', '.join(sorted(EXTENSIONES_PERMITIDAS))}"
        )

    return extension


def validar_tamanio(tamanio_bytes: int) -> None:
    """Lanza ValueError si el archivo supera el límite configurado."""
    max_bytes = settings.max_file_size_bytes
    if tamanio_bytes > max_bytes:
        mb = tamanio_bytes / 1024 / 1024
        max_mb = settings.max_file_size_mb
        raise ValueError(
            f"Archivo demasiado grande: {mb:.1f} MB. Máximo permitido: {max_mb} MB"
        )


def limpiar_nombre(nombre: str) -> str:
    """Sanitiza el nombre del archivo para almacenamiento seguro."""
    # Remover caracteres peligrosos
    chars_peligrosos = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    nombre_limpio = nombre
    for char in chars_peligrosos:
        nombre_limpio = nombre_limpio.replace(char, '_')
    return nombre_limpio[:255]  # Límite de nombre de archivo
