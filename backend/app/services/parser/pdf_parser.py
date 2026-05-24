"""
Parser para extractos bancarios en PDF.
Usa pdfplumber para extraer tablas y texto, luego aplica
detección de columnas con LLM igual que los otros parsers.
"""

import io
import re
import pdfplumber

from app.services.parser.base import AbstractParser, ResultadoParseo, TransaccionRaw
from app.services.parser.column_detector import detectar_columnas_llm, MapeoColumnas


class PDFParser(AbstractParser):
    """
    Parsea extractos bancarios en PDF.
    Estrategia: primero intenta extraer tablas estructuradas;
    si no hay tablas, cae a extracción de texto línea por línea.
    """

    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        resultado = ResultadoParseo()

        try:
            pdf = pdfplumber.open(io.BytesIO(contenido))
        except Exception as e:
            resultado.errores.append(f"No se pudo abrir el PDF: {e}")
            return resultado

        # Intentar extracción por tablas primero
        filas_totales, headers = self._extraer_tablas(pdf)

        # Si no hay tablas estructuradas, caer a texto
        if not filas_totales or not headers:
            filas_totales, headers = self._extraer_texto(pdf)

        pdf.close()

        if not filas_totales:
            resultado.errores.append(
                "No se encontraron datos tabulares en el PDF. "
                "Verifica que el PDF no sea una imagen escaneada."
            )
            return resultado

        resultado.total_filas = len(filas_totales)

        # Detectar mapeo con LLM
        mapeo = await detectar_columnas_llm(headers)
        resultado.columnas_detectadas = mapeo.to_dict()

        if not mapeo.es_valido():
            resultado.errores.append(
                f"No se pudieron identificar las columnas requeridas. "
                f"Encabezados encontrados: {headers}"
            )
            return resultado

        # Parsear filas
        for i, fila in enumerate(filas_totales, start=1):
            if not any(c for c in fila if c):
                resultado.filas_omitidas += 1
                continue
            try:
                tx = self._parsear_fila(fila, mapeo, i)
                resultado.transacciones.append(tx)
            except Exception as e:
                resultado.advertencias.append(f"Fila {i}: {e}")
                resultado.filas_omitidas += 1

        return resultado

    def _extraer_tablas(self, pdf) -> tuple[list[list[str]], list[str]]:
        """Extrae tablas estructuradas de todas las páginas."""
        todas_filas = []
        headers: list[str] = []

        for pagina in pdf.pages:
            tablas = pagina.extract_tables()
            for tabla in tablas:
                if not tabla:
                    continue
                # Primera tabla con encabezados detectables
                if not headers and len(tabla) > 1:
                    headers = [str(c or "").strip() for c in tabla[0]]
                    filas = tabla[1:]
                else:
                    filas = tabla

                for fila in filas:
                    todas_filas.append([str(c or "").strip() for c in fila])

        return todas_filas, headers

    def _extraer_texto(self, pdf) -> tuple[list[list[str]], list[str]]:
        """
        Extrae texto línea por línea cuando no hay tablas.
        Intenta identificar filas de transacciones por patrones de fecha y monto.
        """
        todas_lineas = []

        patron_fecha = re.compile(
            r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{2}[/\-\.]\d{2})\b'
        )
        patron_monto = re.compile(r'\b[\d.,]{3,}\b')

        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            for linea in texto.split("\n"):
                linea = linea.strip()
                if not linea:
                    continue
                # Solo incluir líneas que parezcan transacciones
                tiene_fecha = bool(patron_fecha.search(linea))
                tiene_monto = bool(patron_monto.search(linea))
                if tiene_fecha and tiene_monto:
                    # Dividir por múltiples espacios como separador
                    partes = re.split(r'\s{2,}', linea)
                    todas_lineas.append(partes)

        if not todas_lineas:
            return [], []

        # Crear headers genéricos basados en número de columnas más común
        max_cols = max(len(f) for f in todas_lineas)
        headers_genericos = [f"Columna_{i+1}" for i in range(max_cols)]

        # Normalizar filas al mismo número de columnas
        filas_normalizadas = []
        for fila in todas_lineas:
            if len(fila) < max_cols:
                fila = fila + [""] * (max_cols - len(fila))
            filas_normalizadas.append(fila[:max_cols])

        return filas_normalizadas, headers_genericos

    def _parsear_fila(self, fila: list[str], mapeo: MapeoColumnas, num_fila: int) -> TransaccionRaw:
        def celda(idx: int | None) -> str:
            if idx is None or idx >= len(fila):
                return ""
            return fila[idx].strip()

        descripcion = celda(mapeo.col_descripcion)
        if not descripcion:
            raise ValueError("Descripción vacía")

        fecha = self._normalizar_fecha(celda(mapeo.col_fecha))

        if mapeo.col_cargo is not None and mapeo.col_abono is not None:
            cargo_str = celda(mapeo.col_cargo)
            abono_str = celda(mapeo.col_abono)
            if cargo_str and cargo_str not in ("0", "0.0", "-", ""):
                monto, _ = self._normalizar_monto(cargo_str)
                es_cargo = True
            elif abono_str and abono_str not in ("0", "0.0", "-", ""):
                monto, _ = self._normalizar_monto(abono_str)
                es_cargo = False
            else:
                raise ValueError("Sin monto válido")
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
