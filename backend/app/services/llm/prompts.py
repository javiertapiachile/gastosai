"""
Prompts para clasificación de transacciones bancarias.
Diseñados para maximizar precisión y consistencia entre distintos LLMs.
"""

# Categorías base del sistema — deben coincidir con la migración 001
CATEGORIAS_BASE = [
    "Alimentación",
    "Transporte",
    "Compras",
    "Entretenimiento",
    "Salud",
    "Servicios",
    "Educación",
    "Viajes",
    "Hogar",
    "Sin categoría",
]


PROMPT_SISTEMA = """Eres un asistente experto en finanzas personales para el mercado latinoamericano.
Tu tarea es clasificar transacciones bancarias en categorías predefinidas.

Reglas estrictas:
1. Responde ÚNICAMENTE con JSON válido, sin texto adicional ni markdown
2. Usa EXACTAMENTE los nombres de categoría proporcionados, sin variaciones
3. Si no puedes determinar la categoría con certeza, usa "Sin categoría"
4. Las abreviaciones de comercios son comunes: MCD=McDonald's, AMZN=Amazon, COPEC=estación de servicio
5. Nombres con asterisco son pagos por app: RAPPI*MCDONALDS = McDonald's vía Rappi (categoría: Alimentación)
6. Suscripciones digitales (Netflix, Spotify, Disney+) = Entretenimiento
7. Farmacias, clínicas, laboratorios = Salud
8. Supermercados, restaurantes, delivery = Alimentación
9. Peajes, estaciones de servicio, Uber, taxi = Transporte
10. Transferencias y pagos entre personas: usa contexto para inferir o "Sin categoría\""""


def construir_prompt_clasificacion(
    descripciones: list[str],
    categorias: list[str],
) -> str:
    """
    Construye el prompt de usuario para clasificar un lote de transacciones.

    Args:
        descripciones: Lista de descripciones originales del extracto
        categorias: Lista de nombres de categorías disponibles

    Returns:
        Prompt listo para enviar al LLM
    """
    lista_cats = "\n".join(f"- {c}" for c in categorias)
    lista_tx = "\n".join(
        f'{i}: "{desc}"' for i, desc in enumerate(descripciones)
    )

    return f"""Clasifica estas transacciones bancarias en las siguientes categorías:

CATEGORÍAS DISPONIBLES:
{lista_cats}

TRANSACCIONES A CLASIFICAR:
{lista_tx}

Responde con un JSON con esta estructura exacta:
{{
  "clasificaciones": [
    {{
      "indice": 0,
      "categoria": "nombre exacto de la categoría",
      "comercio_limpio": "nombre legible del comercio (sin códigos ni números de referencia)",
      "confianza": 0.95
    }}
  ]
}}

- "confianza" es un número entre 0.0 y 1.0
- "comercio_limpio" debe ser el nombre real del comercio, ej: "McDonald's" en vez de "MCD #3421"
- Incluye TODOS los índices del 0 al {len(descripciones) - 1}"""


def construir_prompt_verificacion(api_key: str, proveedor: str) -> str:
    """Prompt simple para verificar que la API key funciona."""
    return f"Responde solo 'OK' para confirmar que el proveedor {proveedor} está operativo."
