"""
Detección automática de columnas usando LLM.
Dado un listado de headers (ej: ["Fecha Transacción", "Glosa", "Cargo", "Abono"]),
el LLM infiere qué columna corresponde a cada campo requerido.

Resultado cacheado en memoria para no repetir llamadas con los mismos headers.
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache

import httpx
from app.config import settings


@dataclass
class MapeoColumnas:
    """
    Mapeo entre los índices de columna del archivo y los campos semánticos.
    None significa que esa columna no fue encontrada.
    """
    col_fecha: Optional[int] = None
    col_descripcion: Optional[int] = None
    col_monto: Optional[int] = None        # Monto único (cargo/abono en misma columna)
    col_cargo: Optional[int] = None        # Columna separada de cargos
    col_abono: Optional[int] = None        # Columna separada de abonos
    col_rut: Optional[int] = None          # RUT del comercio (opcional)

    def es_valido(self) -> bool:
        """El mapeo es válido si tiene fecha, descripción y al menos un tipo de monto."""
        tiene_fecha = self.col_fecha is not None
        tiene_descripcion = self.col_descripcion is not None
        tiene_monto = (
            self.col_monto is not None
            or (self.col_cargo is not None and self.col_abono is not None)
            or self.col_cargo is not None
        )
        return tiene_fecha and tiene_descripcion and tiene_monto

    def to_dict(self) -> dict:
        return {
            "fecha": self.col_fecha,
            "descripcion": self.col_descripcion,
            "monto": self.col_monto,
            "cargo": self.col_cargo,
            "abono": self.col_abono,
            "rut": self.col_rut,
        }


# Cache en memoria: hash(headers) → MapeoColumnas
_cache_mapeos: dict[str, MapeoColumnas] = {}


async def detectar_columnas_llm(headers: list[str]) -> MapeoColumnas:
    """
    Usa el LLM configurado para inferir el rol semántico de cada columna.
    Si los mismos headers ya fueron procesados, retorna el resultado cacheado.
    """
    # Normalizar y hashear para cache
    headers_norm = [h.strip().lower() for h in headers if h.strip()]
    clave_cache = hashlib.md5("|".join(headers_norm).encode()).hexdigest()

    if clave_cache in _cache_mapeos:
        return _cache_mapeos[clave_cache]

    # Intentar detección por heurística primero (más rápido, sin costo de API)
    mapeo_heuristico = _detectar_heuristicamente(headers)
    if mapeo_heuristico.es_valido():
        _cache_mapeos[clave_cache] = mapeo_heuristico
        return mapeo_heuristico

    # Si la heurística no alcanza, llamar al LLM
    try:
        mapeo_llm = await _llamar_llm(headers)
        _cache_mapeos[clave_cache] = mapeo_llm
        return mapeo_llm
    except Exception as e:
        print(f"[column_detector] Error LLM: {e}. Usando heurística parcial.")
        _cache_mapeos[clave_cache] = mapeo_heuristico
        return mapeo_heuristico


def _detectar_heuristicamente(headers: list[str]) -> MapeoColumnas:
    """
    Detección por palabras clave en los encabezados.
    Cubre la mayoría de bancos chilenos y latinoamericanos.
    """
    mapeo = MapeoColumnas()

    PATRONES_FECHA = ["fecha", "date", "día", "dia", "f.transaccion", "f.operacion"]
    PATRONES_DESC = [
        "descripcion", "descripción", "glosa", "detalle", "concepto",
        "comercio", "beneficiario", "referencia", "movimiento", "transaccion",
        "transaction", "detail", "narration"
    ]
    PATRONES_MONTO = ["monto", "importe", "amount", "valor", "total"]
    PATRONES_CARGO = ["cargo", "debito", "débito", "debit", "egreso", "salida", "gasto"]
    PATRONES_ABONO = ["abono", "credito", "crédito", "credit", "ingreso", "entrada", "deposito"]
    PATRONES_RUT = ["rut", "rut comercio", "ruc", "nit", "tax"]

    for i, header in enumerate(headers):
        h = header.lower().strip()

        if any(p in h for p in PATRONES_FECHA) and mapeo.col_fecha is None:
            mapeo.col_fecha = i
        elif any(p in h for p in PATRONES_DESC) and mapeo.col_descripcion is None:
            mapeo.col_descripcion = i
        elif any(p in h for p in PATRONES_CARGO) and mapeo.col_cargo is None:
            mapeo.col_cargo = i
        elif any(p in h for p in PATRONES_ABONO) and mapeo.col_abono is None:
            mapeo.col_abono = i
        elif any(p in h for p in PATRONES_MONTO) and mapeo.col_monto is None:
            mapeo.col_monto = i
        elif any(p in h for p in PATRONES_RUT) and mapeo.col_rut is None:
            mapeo.col_rut = i

    return mapeo


async def _llamar_llm(headers: list[str]) -> MapeoColumnas:
    """
    Llama al LLM para identificar el rol de cada columna.
    Construye un prompt JSON y parsea la respuesta.
    """
    headers_con_indice = {str(i): h for i, h in enumerate(headers)}

    prompt = f"""Analiza estos encabezados de columnas de un extracto bancario y determina qué índice corresponde a cada campo.

Encabezados (índice: nombre):
{json.dumps(headers_con_indice, ensure_ascii=False, indent=2)}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta (usa null si no existe esa columna):
{{
  "col_fecha": <índice entero o null>,
  "col_descripcion": <índice entero o null>,
  "col_monto": <índice entero o null>,
  "col_cargo": <índice entero o null>,
  "col_abono": <índice entero o null>,
  "col_rut": <índice entero o null>
}}

Reglas:
- col_monto: si hay UNA sola columna de monto (puede ser positivo para cargos, negativo para abonos)
- col_cargo y col_abono: si hay DOS columnas separadas para cargos y abonos
- col_descripcion: el nombre o glosa de la transacción (texto descriptivo)
- col_rut: el RUT o identificador del comercio (si existe)
- No uses la misma columna para dos campos distintos"""

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
    texto = mensaje.content[0].text
    return _parsear_respuesta_llm(texto)


async def _llamar_openai(prompt: str) -> MapeoColumnas:
    import openai
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    respuesta = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    texto = respuesta.choices[0].message.content
    return _parsear_respuesta_llm(texto)


async def _llamar_ollama(prompt: str) -> MapeoColumnas:
    async with httpx.AsyncClient(timeout=30) as client:
        respuesta = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
        )
        respuesta.raise_for_status()
        texto = respuesta.json().get("response", "{}")
        return _parsear_respuesta_llm(texto)


def _parsear_respuesta_llm(texto: str) -> MapeoColumnas:
    """Extrae el JSON de la respuesta del LLM y construye el MapeoColumnas."""
    # Limpiar markdown si el LLM lo incluye
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
        col_cargo=parse_int(datos.get("col_cargo")),
        col_abono=parse_int(datos.get("col_abono")),
        col_rut=parse_int(datos.get("col_rut")),
    )
