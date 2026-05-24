"""
Parser para archivos Excel (.xlsx) de extractos bancarios.
"""

import io
from datetime import date, datetime
from openpyxl import load_workbook

from app.services.parser.base import AbstractParser, ResultadoParseo, TransaccionRaw
from app.services.parser.column_detector import detectar_columnas_llm, MapeoColumnas


class XLSXParser(AbstractParser):

    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        resultado = ResultadoParseo()

        try:
            wb = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
        except Exception as e:
            resultado.errores.append(f"No se pudo abrir el archivo Excel: {e}")
            return resultado

        hoja = self._seleccionar_hoja(wb)
        if hoja is None:
            resultado.errores.append("No se encontró ninguna hoja con datos.")
            return resultado

        todas_las_filas = []
        for fila in hoja.iter_rows(values_only=True):
            todas_las_filas.append([self._celda_a_str(c) for c in fila])

        if len(todas_las_filas) < 2:
            resultado.errores.append("La hoja Excel no tiene suficientes filas.")
            return resultado

        idx_header = self._encontrar_header(todas_las_filas)
        headers = todas_las_filas[idx_header]
        filas_datos = todas_las_filas[idx_header + 1:]
        resultado.total_filas = len(filas_datos)

        mapeo = await detectar_columnas_llm(headers)
        resultado.columnas_detectadas = mapeo.to_dict()

        if not mapeo.es_valido():
            resultado.errores.append(
                f"No se encontraron columnas requeridas. Encabezados: {headers}"
            )
            return resultado

        for i, fila in enumerate(filas_datos, start=idx_header + 2):
            if not any(c for c in fila if c):
                resultado.filas_omitidas += 1
                continue
            try:
                tx = self._parsear_fila(fila, mapeo, i)
                resultado.transacciones.append(tx)
            except Exception as e:
                resultado.advertencias.append(f"Fila {i}: {e}")
                resultado.filas_omitidas += 1

        wb.close()
        return resultado

    def _seleccionar_hoja(self, wb):
        if wb.active and wb.active.max_row and wb.active.max_row > 1:
            return wb.active
        mejor = None
        max_filas = 0
        for nombre in wb.sheetnames:
            hoja = wb[nombre]
            if hoja.max_row and hoja.max_row > max_filas:
                max_filas = hoja.max_row
                mejor = hoja
        return mejor

    def _encontrar_header(self, filas: list[list[str]]) -> int:
        for i, fila in enumerate(filas[:20]):
            celdas_con_texto = sum(1 for c in fila if c and c.strip())
            if celdas_con_texto >= 3:
                return i
        return 0

    def _celda_a_str(self, valor) -> str:
        if valor is None:
            return ""
        if isinstance(valor, (datetime, date)):
            return valor.strftime("%Y-%m-%d")
        if isinstance(valor, float):
            # Preservar signo para valores negativos
            if valor == int(valor):
                return str(int(valor))
            return str(round(valor, 2))
        return str(valor).strip()

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
