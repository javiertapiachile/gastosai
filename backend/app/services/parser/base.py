"""
Clase base abstracta para parsers de archivos bancarios.
Cada formato (CSV, XLSX, PDF) implementa esta interfaz.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class TransaccionRaw:
    """
    Transacción tal como viene del archivo, antes de cualquier enriquecimiento.
    Los campos opcionales se completan si el extracto los trae.
    """
    descripcion: str
    monto: float
    es_cargo: bool
    fecha: date
    rut_comercio: Optional[str] = None
    fila_original: Optional[int] = None  # Para debug/trazabilidad


@dataclass
class ResultadoParseo:
    """Resultado completo del parseo de un archivo."""
    transacciones: list[TransaccionRaw] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    columnas_detectadas: dict = field(default_factory=dict)  # nombre_columna → índice/header
    total_filas: int = 0
    filas_omitidas: int = 0

    @property
    def exitoso(self) -> bool:
        return len(self.transacciones) > 0 and len(self.errores) == 0


class AbstractParser(ABC):
    """
    Interfaz que todos los parsers deben implementar.
    El método principal es `parsear` que recibe bytes del archivo.
    """

    @abstractmethod
    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        """
        Parsea el contenido del archivo y retorna las transacciones encontradas.

        Args:
            contenido: Bytes del archivo tal como llegó del cliente
            nombre_archivo: Nombre original del archivo (para inferir formato)

        Returns:
            ResultadoParseo con transacciones y metadata del proceso
        """
        ...

    def _normalizar_monto(self, valor: str | float | int) -> tuple[float, bool]:
        """
        Convierte un valor a monto float e infiere si es cargo o abono.
        Maneja formatos como: "1.234,56", "$1234.56", "-500", "500 CR"

        Returns:
            (monto_absoluto, es_cargo)
        """
        if isinstance(valor, (int, float)):
            return abs(float(valor)), float(valor) < 0

        texto = str(valor).strip()

        # Detectar abono explícito
        es_abono = any(ind in texto.upper() for ind in ["CR", "ABONO", "DEPOSITO", "DEP"])

        # Remover símbolos y espacios
        limpio = texto.replace("$", "").replace(" ", "").replace("CR", "").replace("ABONO", "")

        # Manejar formato europeo (1.234,56) vs americano (1,234.56)
        if "," in limpio and "." in limpio:
            if limpio.index(",") > limpio.index("."):
                # Formato europeo: 1.234,56
                limpio = limpio.replace(".", "").replace(",", ".")
            else:
                # Formato americano: 1,234.56
                limpio = limpio.replace(",", "")
        elif "," in limpio:
            # Solo coma: puede ser decimal o miles
            partes = limpio.split(",")
            if len(partes) == 2 and len(partes[1]) <= 2:
                limpio = limpio.replace(",", ".")  # Decimal
            else:
                limpio = limpio.replace(",", "")   # Miles

        try:
            monto = abs(float(limpio))
            es_cargo = not es_abono and float(limpio) >= 0
            return monto, es_cargo
        except ValueError:
            raise ValueError(f"No se puede convertir '{valor}' a monto numérico")

    def _normalizar_fecha(self, valor: str | date) -> date:
        """
        Convierte distintos formatos de fecha a date.
        Soporta: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY, etc.
        """
        from datetime import datetime

        if isinstance(valor, date):
            return valor

        texto = str(valor).strip()

        formatos = [
            "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y",
            "%d/%m/%y", "%Y/%m/%d", "%d.%m.%Y", "%Y%m%d",
        ]

        for fmt in formatos:
            try:
                return datetime.strptime(texto, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Formato de fecha no reconocido: '{valor}'")
