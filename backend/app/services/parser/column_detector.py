"""
Detección automática de columnas usando heurística + LLM.
"""

import json
import hashlib
from dataclasses import dataclass
from typing import Optional

import httpx
from app.config import settings


@dataclass
class MapeoColumnas:
    col_fecha: Optional[int] = None
    col_descripcion: Optional[int] = None
    col_monto: Optional[int] = None        # Monto único con signo real
    col_cargo: Optional[int] = None        # Columna separada de cargos
    col_abono: Optional[int] = None        # Columna separada de abonos
    col_rut: Optional[int] = None
    col_monto_con_signo: Optional[int] = None  # Columna con valor firmado (ej: VALOR CUOTA)

    def es_valido(self) -> bool:
        tiene_fecha = self.col_fecha is not None
        tiene_descripcion = self.col_descripcion is not None
        tiene_monto = (
            self.col_monto is not None
            or self.col_monto_con_signo is not None
            or (self.col_cargo is not None)
        )
        return tiene_fecha and tiene_descripcion and tiene_monto

    def to_dict(self) -> dict:
        return {
            "fecha": self.col_fecha,
            "descripcion": self.col_descripcion,
            "monto": self.col_monto,
            "monto_con_signo": self.col_monto_con_signo,
            "cargo": self.col_cargo,
            "abono": self.col_abono,
            "rut": self.col_rut,
        }


_cache_mapeos: dict[str, MapeoColumnas] = {}


async def detectar_columnas_llm(headers: list[str]) -> MapeoColumnas:
    headers_norm = [h.strip().lower() for h in headers if h.strip()]
    clave_cache = hashlib.md5("|".join(headers_norm).encode()).hexdigest()

    if clave_cache in _cache_mapeos:
        return _cache_mapeos[clave_cache]

    mapeo = _detectar_heuristicamente(headers)
    if mapeo.es_valido():
        _cache_mapeos[clave_cache] = mapeo
        return mapeo

    try:
        mapeo_llm = await _llamar_llm(headers)
        _cache_mapeos[clave_cache] = mapeo_llm
        return mapeo_llm
    except Exception as e:
        print(f"[column_detector] Error LLM: {e}. Usando heurística parcial.")
        _cache_mapeos[clave_cache] = mapeo
        return mapeo


def _detectar_heuristicamente(headers: list[str]) -> MapeoColumnas:
    mapeo = MapeoColumnas()

    PATRONES_FECHA = ["fecha", "date", "día", "dia", "f.transaccion", "f.operacion", "fec"]
    PATRONES_DESC = [
        "descripcion", "descripción", "glosa", "detalle", "concepto",
        "comercio", "beneficiario", "referencia", "movimiento", "transaccion",
        "transaction", "detail", "narration", "nombre"
    ]
    # Columnas con signo real (prioridad alta — tienen el valor firmado)
    PATRONES_MONTO_SIGNO = [
        "valor cuota", "valor_cuota", "importe", "amount", "valor",
        "monto neto", "monto_neto", "total"
    ]
    # Columnas de monto sin signo (prioridad baja)
    PATRONES_MONTO = ["monto", "cargo"]
    PATRONES_CARGO = ["debito", "débito", "debit", "egreso", "salida", "gasto"]
    PATRONES_ABONO = ["abono", "credito", "crédito", "credit", "ingreso", "entrada", "deposito", "haber"]
    PATRONES_RUT = ["rut", "ruc", "nit", "tax"]

    for i, header in enumerate(headers):
        h = header.lower().strip()

        if any(p in h for p in PATRONES_FECHA) and mapeo.col_fecha is None:
            mapeo.col_fecha = i
        elif any(p in h for p in PATRONES_DESC) and mapeo.col_descripcion is None:
            mapeo.col_descripcion = i
        elif any(h == p or p in h for p in PATRONES_MONTO_SIGNO) and mapeo.col_monto_con_signo is None:
            # Este tiene el signo real — toma precedencia sobre col_monto
            mapeo.col_monto_con_signo = i
        elif any(p in h for p in PATRONES_ABONO) and mapeo.col_abono is None:
            mapeo.col_abono = i
        elif any(p in h for p in PATRONES_CARGO) and mapeo.col_cargo is None:
            mapeo.col_cargo = i
        elif any(p in h for p in PATRONES_MONTO) and mapeo.col_monto is None:
            mapeo.col_monto = i
        elif any(p in h for p in PATRONES_RUT) and mapeo.col_rut is None:
            mapeo.col_rut = i

    return mapeo


async def _llamar_llm(headers: list[str]) -> MapeoColumnas:
    headers_con_indice = {str(i): h for i, h in enumerate(headers)}

    prompt = f"""Analiza estos encabezados de columnas de un extracto bancario e identifica qué índice corresponde a cada campo.

Encabezados (índice: nombre):
{json.dumps(headers_con_indice, ensure_ascii=False, indent=2)}

Responde ÚNICAMENTE con JSON válido:
{{
  "col_fecha": <índice entero o null>,
  "col_descripcion": <índice entero o null>,
  "col_monto": <índice entero o null>,
  "col_monto_con_signo": <índice entero o null>,
  "col_cargo": <índice entero o null>,
  "col_abono": <índice entero o null>,
  "col_rut": <índice entero o null>
}}

Reglas:
- col_monto_con_signo: columna que tiene el valor CON SIGNO real (negativo=devolución/abono). Ej: "VALOR CUOTA", "Importe", "Amount"
- col_monto: columna con valor SIEMPRE POSITIVO (valor absoluto). Ej: "MONTO", "Cargo"
- col_cargo y col_abono: si hay columnas SEPARADAS para cada tipo
- col_descripcion: nombre o glosa de la transacción
- Prioriza col_monto_con_signo sobre col_monto cuando ambas existen"""

    if settings.llm_provider == "anthropic":
        return await _llamar_anthropic(prompt)
    elif settings.llm_provider == "openai":
        return await _llamar_openai(prompt)
    else:
        return await _llamar_ollama(prompt)


async def _llamar_anthropic(prompt: str) -> MapeoColumnas:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    mensaje = await client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parsear_respuesta_llm(mensaje.content[0].text)


async def _llamar_openai(prompt: str) -> MapeoColumnas:
    import openai
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    respuesta = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return _parsear_respuesta_llm(respuesta.choices[0].message.content)


async def _llamar_ollama(prompt: str) -> MapeoColumnas:
    async with httpx.AsyncClient(timeout=60) as client:
        respuesta = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        respuesta.raise_for_status()
        texto = respuesta.json()["message"]["content"]
        return _parsear_respuesta_llm(texto)


def _parsear_respuesta_llm(texto: str) -> MapeoColumnas:
    texto = texto.strip()
    if "```" in texto:
        inicio = texto.find("{")
        fin = texto.rfind("}") + 1
        texto = texto[inicio:fin]

    datos = json.loads(texto)

    def parse_int(val) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    return MapeoColumnas(
        col_fecha=parse_int(datos.get("col_fecha")),
        col_descripcion=parse_int(datos.get("col_descripcion")),
        col_monto=parse_int(datos.get("col_monto")),
        col_monto_con_signo=parse_int(datos.get("col_monto_con_signo")),
        col_cargo=parse_int(datos.get("col_cargo")),
        col_abono=parse_int(datos.get("col_abono")),
        col_rut=parse_int(datos.get("col_rut")),
    )
