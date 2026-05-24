"""
Clase base abstracta para parsers de archivos bancarios.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class TransaccionRaw:
    descripcion: str
    monto: float
    es_cargo: bool
    fecha: date
    rut_comercio: Optional[str] = None
    fila_original: Optional[int] = None


@dataclass
class ResultadoParseo:
    transacciones: list[TransaccionRaw] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    columnas_detectadas: dict = field(default_factory=dict)
    total_filas: int = 0
    filas_omitidas: int = 0

    @property
    def exitoso(self) -> bool:
        return len(self.transacciones) > 0 and len(self.errores) == 0


class AbstractParser(ABC):

    @abstractmethod
    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        ...

    def _normalizar_monto(self, valor: str | float | int) -> tuple[float, bool]:
        """
        Convierte valor a (monto_absoluto, es_cargo).
        Cuando se llama desde _parsear_fila con col_monto_con_signo,
        el signo del valor determina si es cargo o abono.
        """
        if isinstance(valor, (int, float)):
            monto = float(valor)
            return abs(monto), monto >= 0  # negativo = abono

        texto = str(valor).strip()
        es_abono = any(ind in texto.upper() for ind in ["CR", "ABONO", "DEPOSITO", "DEP"])

        limpio = texto.replace("$", "").replace(" ", "").replace("CR", "").replace("ABONO", "")

        if "," in limpio and "." in limpio:
            if limpio.index(",") > limpio.index("."):
                limpio = limpio.replace(".", "").replace(",", ".")
            else:
                limpio = limpio.replace(",", "")
        elif "," in limpio:
            partes = limpio.split(",")
            if len(partes) == 2 and len(partes[1]) <= 2:
                limpio = limpio.replace(",", ".")
            else:
                limpio = limpio.replace(",", "")

        try:
            monto_float = float(limpio)
            if es_abono:
                return abs(monto_float), False
            # Si el valor tiene signo propio (negativo), es abono
            return abs(monto_float), monto_float >= 0
        except ValueError:
            raise ValueError(f"No se puede convertir '{valor}' a monto numérico")

    def _resolver_monto_y_tipo(
        self,
        fila: list[str],
        mapeo,
    ) -> tuple[float, bool]:
        """
        Resuelve monto y tipo (cargo/abono) considerando:
        1. col_monto_con_signo: columna con valor firmado (negativo=abono)
        2. col_cargo + col_abono: columnas separadas
        3. col_monto: columna única (siempre positiva, asume cargo)
        """
        def celda(idx):
            if idx is None or idx >= len(fila):
                return ""
            return str(fila[idx]).strip()

        # Prioridad 1: columna con signo real (VALOR CUOTA, Importe, etc.)
        if mapeo.col_monto_con_signo is not None:
            val = celda(mapeo.col_monto_con_signo)
            if val and val not in ("0", "0.0", "-", ""):
                try:
                    monto_float = self._parse_numero(val)
                    return abs(monto_float), monto_float >= 0
                except ValueError:
                    pass

        # Prioridad 2: columnas separadas cargo/abono
        if mapeo.col_cargo is not None and mapeo.col_abono is not None:
            cargo_str = celda(mapeo.col_cargo)
            abono_str = celda(mapeo.col_abono)
            if cargo_str and cargo_str not in ("0", "0.0", "-", ""):
                monto, _ = self._normalizar_monto(cargo_str)
                return monto, True
            elif abono_str and abono_str not in ("0", "0.0", "-", ""):
                monto, _ = self._normalizar_monto(abono_str)
                return monto, False

        # Prioridad 3: solo cargo
        if mapeo.col_cargo is not None:
            val = celda(mapeo.col_cargo)
            if val and val not in ("0", "0.0", "-", ""):
                monto, _ = self._normalizar_monto(val)
                return monto, True

        # Prioridad 4: monto único (siempre positivo, asume cargo)
        if mapeo.col_monto is not None:
            val = celda(mapeo.col_monto)
            if val and val not in ("0", "0.0", "-", ""):
                monto, _ = self._normalizar_monto(val)
                return monto, True

        raise ValueError("Sin monto válido en ninguna columna")

    def _parse_numero(self, texto: str) -> float:
        """Convierte texto a float preservando el signo."""
        limpio = texto.replace("$", "").replace(" ", "")

        if "," in limpio and "." in limpio:
            if limpio.index(",") > limpio.index("."):
                limpio = limpio.replace(".", "").replace(",", ".")
            else:
                limpio = limpio.replace(",", "")
        elif "," in limpio:
            partes = limpio.split(",")
            if len(partes) == 2 and len(partes[1]) <= 2:
                limpio = limpio.replace(",", ".")
            else:
                limpio = limpio.replace(",", "")

        return float(limpio)

    def _normalizar_fecha(self, valor) -> date:
        from datetime import datetime

        if isinstance(valor, date) and not isinstance(valor, datetime):
            return valor
        if isinstance(valor, datetime):
            return valor.date()

        texto = str(valor).strip()

        # Número serial de Excel (días desde 1900-01-01)
        if texto.isdigit() and len(texto) == 5:
            from datetime import timedelta
            base = date(1899, 12, 30)
            return base + timedelta(days=int(texto))

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
