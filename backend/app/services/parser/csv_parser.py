"""
Parser para archivos CSV de extractos bancarios.
"""

import csv
import io

from app.services.parser.base import AbstractParser, ResultadoParseo, TransaccionRaw
from app.services.parser.column_detector import detectar_columnas_llm, MapeoColumnas


class CSVParser(AbstractParser):

    SEPARADORES_CANDIDATOS = [";", ",", "\t", "|"]
    ENCODINGS_CANDIDATOS = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        resultado = ResultadoParseo()

        texto = self._decodificar(contenido)
        if texto is None:
            resultado.errores.append("No se pudo decodificar el CSV. Prueba guardarlo en UTF-8.")
            return resultado

        separador = self._detectar_separador(texto)
        reader = csv.reader(io.StringIO(texto), delimiter=separador)
        filas = list(reader)

        if len(filas) < 2:
            resultado.errores.append("El CSV está vacío o solo tiene encabezados.")
            return resultado

        headers = [h.strip() for h in filas[0]]
        filas_datos = filas[1:]
        resultado.total_filas = len(filas_datos)

        mapeo = await detectar_columnas_llm(headers)
        resultado.columnas_detectadas = mapeo.to_dict()

        if not mapeo.es_valido():
            resultado.errores.append(
                f"No se encontraron columnas requeridas. Columnas: {headers}"
            )
            return resultado

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
        def celda(idx):
            if idx is None or idx >= len(fila):
                return ""
            return fila[idx].strip()

        descripcion = celda(mapeo.col_descripcion)
        if not descripcion:
            raise ValueError("Descripción vacía")

        fecha = self._normalizar_fecha(celda(mapeo.col_fecha))

        # Usar el método unificado que prioriza col_monto_con_signo
        monto, es_cargo = self._resolver_monto_y_tipo(fila, mapeo)

        rut = celda(mapeo.col_rut) if mapeo.col_rut is not None else None

        return TransaccionRaw(
            descripcion=descripcion,
            monto=monto,
            es_cargo=es_cargo,
            fecha=fecha,
            rut_comercio=rut or None,
            fila_original=num_fila,
        )
