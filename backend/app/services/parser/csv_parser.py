"""
Parser para archivos CSV de extractos bancarios.
Detecta automáticamente el separador y el encoding.
"""

import csv
import io
from datetime import date

from app.services.parser.base import AbstractParser, ResultadoParseo, TransaccionRaw
from app.services.parser.column_detector import detectar_columnas_llm, MapeoColumnas


class CSVParser(AbstractParser):
    """
    Parsea extractos bancarios en formato CSV.
    Soporta separadores: coma, punto y coma, tabulador, pipe.
    Soporta encodings: UTF-8, Latin-1, CP1252 (Windows español).
    """

    SEPARADORES_CANDIDATOS = [";", ",", "\t", "|"]
    ENCODINGS_CANDIDATOS = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        resultado = ResultadoParseo()

        # 1. Detectar encoding
        texto = self._decodificar(contenido)
        if texto is None:
            resultado.errores.append("No se pudo decodificar el archivo CSV. Prueba guardarlo en UTF-8.")
            return resultado

        # 2. Detectar separador
        separador = self._detectar_separador(texto)

        # 3. Leer filas
        reader = csv.reader(io.StringIO(texto), delimiter=separador)
        filas = list(reader)

        if len(filas) < 2:
            resultado.errores.append("El archivo CSV está vacío o solo tiene encabezados.")
            return resultado

        headers = [h.strip() for h in filas[0]]
        filas_datos = filas[1:]
        resultado.total_filas = len(filas_datos)

        # 4. Detectar mapeo de columnas con LLM
        mapeo = await detectar_columnas_llm(headers)
        resultado.columnas_detectadas = mapeo.to_dict()

        if not mapeo.es_valido():
            resultado.errores.append(
                f"No se encontraron las columnas requeridas (descripción, monto, fecha). "
                f"Columnas detectadas: {headers}"
            )
            return resultado

        # 5. Parsear cada fila
        for i, fila in enumerate(filas_datos, start=2):
            if not any(celda.strip() for celda in fila):
                resultado.filas_omitidas += 1
                continue

            try:
                tx = self._parsear_fila(fila, mapeo, i)
                resultado.transacciones.append(tx)
            except Exception as e:
                resultado.advertencias.append(f"Fila {i}: {e}")
                resultado.filas_omitidas += 1

        return resultado

    def _decodificar(self, contenido: bytes) -> str | None:
        for encoding in self.ENCODINGS_CANDIDATOS:
            try:
                return contenido.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return None

    def _detectar_separador(self, texto: str) -> str:
        """Elige el separador que produce más columnas consistentes en las primeras filas."""
        primeras_lineas = texto.split("\n")[:5]
        mejor = ","
        max_cols = 0

        for sep in self.SEPARADORES_CANDIDATOS:
            conteos = [len(linea.split(sep)) for linea in primeras_lineas if linea.strip()]
            if conteos and min(conteos) == max(conteos) and max(conteos) > max_cols:
                max_cols = max(conteos)
                mejor = sep

        return mejor

    def _parsear_fila(self, fila: list[str], mapeo: MapeoColumnas, num_fila: int) -> TransaccionRaw:
        """Extrae y convierte los campos de una fila usando el mapeo de columnas."""
        def celda(idx: int | None) -> str:
            if idx is None or idx >= len(fila):
                return ""
            return fila[idx].strip()

        descripcion = celda(mapeo.col_descripcion)
        if not descripcion:
            raise ValueError("Descripción vacía")

        fecha_raw = celda(mapeo.col_fecha)
        fecha = self._normalizar_fecha(fecha_raw)

        # Manejar columnas separadas de cargo/abono vs monto único
        if mapeo.col_cargo is not None and mapeo.col_abono is not None:
            cargo_str = celda(mapeo.col_cargo)
            abono_str = celda(mapeo.col_abono)

            if cargo_str and cargo_str not in ("0", "0.0", "0,0", "-"):
                monto, _ = self._normalizar_monto(cargo_str)
                es_cargo = True
            elif abono_str and abono_str not in ("0", "0.0", "0,0", "-"):
                monto, _ = self._normalizar_monto(abono_str)
                es_cargo = False
            else:
                raise ValueError("Fila sin monto válido en cargo ni abono")
        else:
            monto_raw = celda(mapeo.col_monto)
            if not monto_raw:
                raise ValueError("Monto vacío")
            monto, es_cargo = self._normalizar_monto(monto_raw)

        rut = celda(mapeo.col_rut) if mapeo.col_rut is not None else None

        return TransaccionRaw(
            descripcion=descripcion,
            monto=monto,
            es_cargo=es_cargo,
            fecha=fecha,
            rut_comercio=rut or None,
            fila_original=num_fila,
        )
