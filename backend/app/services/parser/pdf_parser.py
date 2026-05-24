"""
Parser para extractos bancarios en PDF.

Estrategia en 3 capas:
  1. pdfplumber con tablas estructuradas
  2. LLM sobre texto crudo con extracción robusta de JSON
  3. Error informativo para PDFs escaneados
"""

import io
import re
import json
import logging
from datetime import date

import pdfplumber

from app.services.parser.base import AbstractParser, ResultadoParseo, TransaccionRaw
from app.services.parser.column_detector import detectar_columnas_llm

logger = logging.getLogger(__name__)

MAX_TEXTO_LLM = 10000


class PDFParser(AbstractParser):

    async def parsear(self, contenido: bytes, nombre_archivo: str) -> ResultadoParseo:
        resultado = ResultadoParseo()

        try:
            pdf = pdfplumber.open(io.BytesIO(contenido))
        except Exception as e:
            resultado.errores.append(f"No se pudo abrir el PDF: {e}")
            return resultado

        logger.info(f"[pdf_parser] '{nombre_archivo}' — {len(pdf.pages)} páginas")

        # Estrategia 1: tablas estructuradas
        filas, headers = self._extraer_tablas(pdf)
        if filas and headers and len(filas) >= 2:
            logger.info(f"[pdf_parser] Estrategia 1 (tablas): {len(filas)} filas")
            pdf.close()
            return await self._procesar_con_mapeo(filas, headers, resultado)

        # Estrategia 2: texto crudo → LLM
        texto_crudo = self._extraer_texto_crudo(pdf)
        pdf.close()

        if not texto_crudo or len(texto_crudo.strip()) < 50:
            resultado.errores.append(
                "El PDF no contiene texto legible. "
                "Puede ser un PDF escaneado. "
                "Por favor exporta el estado de cuenta como CSV o XLSX."
            )
            return resultado

        logger.info(f"[pdf_parser] Estrategia 2 (LLM): {len(texto_crudo)} caracteres")
        return await self._extraer_con_llm(texto_crudo, resultado)

    # ── Estrategia 1: tablas pdfplumber ──────────────────────────────────────

    def _extraer_tablas(self, pdf) -> tuple[list[list[str]], list[str]]:
        configs = [
            {"vertical_strategy": "lines_strict", "horizontal_strategy": "lines_strict"},
            {"vertical_strategy": "text", "horizontal_strategy": "text",
             "min_words_vertical": 3, "min_words_horizontal": 1},
        ]
        for config in configs:
            filas, headers = self._extraer_tablas_con_config(pdf, config)
            if filas and headers:
                return filas, headers
        return [], []

    def _extraer_tablas_con_config(self, pdf, config: dict) -> tuple[list[list[str]], list[str]]:
        todas_filas: list[list[str]] = []
        headers: list[str] = []

        for pagina in pdf.pages:
            try:
                tablas = pagina.extract_tables(config)
                for tabla in (tablas or []):
                    if not tabla or len(tabla) < 2:
                        continue
                    filas_limpias = [
                        [str(c or "").strip() for c in fila]
                        for fila in tabla
                        if any(c for c in fila if c)
                    ]
                    if not filas_limpias:
                        continue
                    primera = filas_limpias[0]
                    if not headers and self._parece_header(primera):
                        headers = primera
                        todas_filas.extend(filas_limpias[1:])
                    else:
                        todas_filas.extend(filas_limpias)
            except Exception:
                continue

        return todas_filas, headers

    def _parece_header(self, fila: list[str]) -> bool:
        palabras = {"fecha","descripcion","descripción","glosa","monto","cargo",
                    "abono","valor","detalle","concepto","date","amount","balance","saldo"}
        texto = " ".join(fila).lower()
        return any(p in texto for p in palabras)

    async def _procesar_con_mapeo(
        self, filas: list[list[str]], headers: list[str], resultado: ResultadoParseo,
    ) -> ResultadoParseo:
        resultado.total_filas = len(filas)
        mapeo = await detectar_columnas_llm(headers)
        resultado.columnas_detectadas = mapeo.to_dict()

        if not mapeo.es_valido():
            logger.warning(f"[pdf_parser] Mapeo inválido: {headers}")
            return resultado

        for i, fila in enumerate(filas, start=1):
            if not any(c for c in fila if c):
                resultado.filas_omitidas += 1
                continue
            try:
                def celda(idx):
                    if idx is None or idx >= len(fila): return ""
                    return fila[idx].strip()

                descripcion = celda(mapeo.col_descripcion)
                if not descripcion:
                    resultado.filas_omitidas += 1
                    continue

                fecha = self._normalizar_fecha(celda(mapeo.col_fecha))
                monto, es_cargo = self._resolver_monto_y_tipo(fila, mapeo)
                rut = celda(mapeo.col_rut) if mapeo.col_rut is not None else None

                resultado.transacciones.append(TransaccionRaw(
                    descripcion=descripcion, monto=monto, es_cargo=es_cargo,
                    fecha=fecha, rut_comercio=rut or None, fila_original=i,
                ))
            except Exception as e:
                resultado.advertencias.append(f"Fila {i}: {e}")
                resultado.filas_omitidas += 1

        return resultado

    # ── Estrategia 2: LLM sobre texto crudo ──────────────────────────────────

    def _extraer_texto_crudo(self, pdf) -> str:
        paginas = []
        for i, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text(layout=True) or pagina.extract_text() or ""
            if texto.strip():
                paginas.append(f"--- PÁGINA {i} ---\n{texto}")
        return "\n\n".join(paginas)

    async def _extraer_con_llm(
        self, texto_crudo: str, resultado: ResultadoParseo,
    ) -> ResultadoParseo:
        if len(texto_crudo) > MAX_TEXTO_LLM:
            logger.warning(f"[pdf_parser] Texto truncado a {MAX_TEXTO_LLM} chars")
            texto_crudo = texto_crudo[:MAX_TEXTO_LLM]

        try:
            from app.services.llm.factory import get_llm_provider
            llm = get_llm_provider()
            respuesta = await llm.completar(
                self._prompt_sistema(),
                self._prompt_usuario(texto_crudo),
            )
            logger.info(f"[pdf_parser] Respuesta LLM ({len(respuesta)} chars): {repr(respuesta[:200])}")

            datos = self._extraer_json_robusto(respuesta)
            if datos is None:
                # Segundo intento con prompt más directo
                logger.warning("[pdf_parser] Primer intento falló, reintentando con prompt simplificado")
                respuesta2 = await llm.completar(
                    "Responde solo con JSON, sin explicaciones.",
                    self._prompt_simple(texto_crudo),
                )
                logger.info(f"[pdf_parser] Respuesta reintento: {repr(respuesta2[:200])}")
                datos = self._extraer_json_robusto(respuesta2)

            if datos is None:
                resultado.errores.append(
                    "El modelo LLM no respondió en formato JSON. "
                    "Intenta con un modelo diferente o exporta el PDF como CSV."
                )
                return resultado

            for adv in datos.get("advertencias", []):
                resultado.advertencias.append(f"LLM: {adv}")

            txs_raw = datos.get("transacciones", [])
            resultado.total_filas = len(txs_raw)
            resultado.columnas_detectadas = {"estrategia": "llm_texto_crudo"}

            for i, tx_dict in enumerate(txs_raw, start=1):
                try:
                    tx = self._dict_a_transaccion(tx_dict, i)
                    resultado.transacciones.append(tx)
                except Exception as e:
                    resultado.advertencias.append(f"Tx {i}: {e}")
                    resultado.filas_omitidas += 1

            logger.info(f"[pdf_parser] {len(resultado.transacciones)} transacciones extraídas")

        except Exception as e:
            logger.error(f"[pdf_parser] Error LLM: {e}")
            resultado.errores.append(
                f"Error al procesar PDF con IA: {str(e)[:200]}. "
                "Exporta el estado de cuenta como CSV o XLSX para mejor compatibilidad."
            )

        return resultado

    def _prompt_sistema(self) -> str:
        return (
            "Eres un extractor de datos bancarios. "
            "Tu única tarea es leer extractos y devolver un JSON. "
            "NUNCA incluyas explicaciones, saludos ni texto fuera del JSON. "
            "Responde SOLO con el objeto JSON, empezando con { y terminando con }."
        )

    def _prompt_usuario(self, texto: str) -> str:
        return f"""Lee este extracto bancario y extrae todas las transacciones.

EXTRACTO:
{texto}

RESPONDE EXACTAMENTE ASÍ (solo JSON, sin texto antes ni después):
{{"transacciones":[{{"fecha":"2025-11-01","descripcion":"NOMBRE COMERCIO","monto":12345.00,"es_cargo":true}}],"advertencias":[]}}

Reglas:
- fecha en formato YYYY-MM-DD
- monto siempre positivo
- es_cargo true=compra/gasto, false=abono/depósito/pago recibido
- NO incluir totales ni saldos"""

    def _prompt_simple(self, texto: str) -> str:
        """Prompt más directo para segundo intento."""
        # Tomar solo las primeras líneas con fechas y montos
        lineas_relevantes = []
        patron = re.compile(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}')
        for linea in texto.split('\n'):
            if patron.search(linea) and len(linea.strip()) > 10:
                lineas_relevantes.append(linea.strip())

        muestra = '\n'.join(lineas_relevantes[:30])

        return f"""Convierte estas líneas de un extracto bancario a JSON.
Cada línea es una transacción con fecha, descripción y monto.

{muestra}

JSON de respuesta (SOLO el JSON):
{{"transacciones":[{{"fecha":"YYYY-MM-DD","descripcion":"texto","monto":0.0,"es_cargo":true}}]}}"""

    def _extraer_json_robusto(self, texto: str) -> dict | None:
        """
        Extrae JSON de la respuesta del LLM de forma agresiva.
        Maneja: markdown, texto antes/después, arrays sueltos, etc.
        """
        if not texto or not texto.strip():
            return None

        texto = texto.strip()

        # 1. Remover bloques markdown ```json ... ```
        if "```" in texto:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', texto)
            if match:
                texto = match.group(1).strip()

        # 2. Buscar objeto JSON completo { ... }
        # Usar búsqueda balanceada de llaves
        inicio = texto.find("{")
        if inicio >= 0:
            json_candidato = self._extraer_objeto_balanceado(texto, inicio)
            if json_candidato:
                try:
                    datos = json.loads(json_candidato)
                    # Validar que tiene la estructura esperada
                    if "transacciones" in datos:
                        return datos
                    # Si tiene lista directa de objetos con fecha/monto, envolverla
                    if isinstance(datos, list):
                        return {"transacciones": datos, "advertencias": []}
                except json.JSONDecodeError:
                    # Intentar reparar JSON común con trailing commas
                    json_reparado = self._reparar_json(json_candidato)
                    try:
                        datos = json.loads(json_reparado)
                        if "transacciones" in datos:
                            return datos
                    except Exception:
                        pass

        # 3. Intentar construir desde líneas con patrón de transacción
        txs = self._extraer_desde_texto_plano(texto)
        if txs:
            logger.info(f"[pdf_parser] JSON extraído desde texto plano: {len(txs)} tx")
            return {"transacciones": txs, "advertencias": ["Extraído desde texto sin estructura JSON"]}

        return None

    def _extraer_objeto_balanceado(self, texto: str, inicio: int) -> str | None:
        """Extrae un objeto JSON balanceando llaves."""
        profundidad = 0
        en_string = False
        escape = False

        for i, ch in enumerate(texto[inicio:], start=inicio):
            if escape:
                escape = False
                continue
            if ch == '\\' and en_string:
                escape = True
                continue
            if ch == '"':
                en_string = not en_string
                continue
            if en_string:
                continue
            if ch == '{':
                profundidad += 1
            elif ch == '}':
                profundidad -= 1
                if profundidad == 0:
                    return texto[inicio:i+1]

        return None

    def _reparar_json(self, texto: str) -> str:
        """Repara problemas comunes de JSON generado por LLMs."""
        # Trailing commas antes de } o ]
        texto = re.sub(r',\s*}', '}', texto)
        texto = re.sub(r',\s*]', ']', texto)
        # Comillas simples → dobles
        texto = re.sub(r"'([^']*)':", r'"\1":', texto)
        return texto

    def _extraer_desde_texto_plano(self, texto: str) -> list[dict]:
        """
        Último recurso: extrae transacciones buscando patrones fecha+monto en el texto.
        """
        patron_fecha = re.compile(
            r'(\d{4}-\d{2}-\d{2}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})'
        )
        patron_monto = re.compile(r'[\$]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)')

        txs = []
        for linea in texto.split('\n'):
            linea = linea.strip()
            if not linea:
                continue

            fecha_match = patron_fecha.search(linea)
            monto_match = patron_monto.search(linea)

            if not fecha_match or not monto_match:
                continue

            try:
                fecha_str = fecha_match.group(1)
                fecha = self._normalizar_fecha(fecha_str)

                monto_str = monto_match.group(1).replace('.', '').replace(',', '.')
                monto = abs(float(monto_str))
                if monto <= 0:
                    continue

                # Descripción: texto entre fecha y monto
                desc = linea[fecha_match.end():monto_match.start()].strip()
                if not desc:
                    desc = linea[:fecha_match.start()].strip() or linea

                desc = re.sub(r'\s+', ' ', desc).strip()
                if len(desc) < 2:
                    continue

                txs.append({
                    "fecha": fecha.strftime("%Y-%m-%d"),
                    "descripcion": desc[:200],
                    "monto": monto,
                    "es_cargo": True,
                })
            except Exception:
                continue

        return txs

    def _dict_a_transaccion(self, d: dict, num_fila: int) -> TransaccionRaw:
        descripcion = str(d.get("descripcion", "")).strip()
        if not descripcion:
            raise ValueError("Descripción vacía")

        try:
            fecha = self._normalizar_fecha(str(d.get("fecha", "")))
        except Exception:
            fecha = date.today()
            logger.warning(f"[pdf_parser] Fecha inválida '{d.get('fecha')}', usando hoy")

        try:
            monto_raw = str(d.get("monto", 0)).replace(",", "").replace("$", "").strip()
            monto = abs(float(monto_raw))
        except (ValueError, TypeError):
            raise ValueError(f"Monto inválido: {d.get('monto')}")

        if monto <= 0:
            raise ValueError(f"Monto cero: {d.get('monto')}")

        return TransaccionRaw(
            descripcion=descripcion,
            monto=monto,
            es_cargo=bool(d.get("es_cargo", True)),
            fecha=fecha,
            fila_original=num_fila,
        )
