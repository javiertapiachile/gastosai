"""
Prompts optimizados para clasificación rápida con Ollama/Gemma4.

Optimizaciones aplicadas (Opciones A+B):
  A: Lote reducido a 10 transacciones (menos tokens de salida por llamada)
  B: Formato compacto línea por línea "indice:Categoria" en vez de JSON completo
     → el parser reconstruye la estructura, pero el modelo genera ~80% menos tokens
"""

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

# Tamaño de lote reducido para Ollama — mejora velocidad ~2x
TAMANO_LOTE_OPTIMIZADO = 10

PROMPT_SISTEMA = (
    "Eres un clasificador de transacciones bancarias para Chile. "
    "Responde SOLO con el formato indicado, sin texto adicional."
)


def construir_prompt_clasificacion(
    descripciones: list[str],
    categorias: list[str],
) -> str:
    """
    Prompt ultra-compacto: pide solo 'indice:Categoria' por línea.
    Genera ~80% menos tokens de salida que el formato JSON completo.
    """
    cats = ", ".join(categorias)
    txs = "\n".join(f"{i}:{desc}" for i, desc in enumerate(descripciones))

    return (
        f"Categorías válidas: {cats}\n\n"
        f"Clasifica cada transacción. Responde SOLO con líneas 'numero:Categoria':\n"
        f"{txs}\n\n"
        f"Respuesta (una línea por transacción, exactamente):"
    )


def parsear_respuesta_compacta(
    texto: str,
    descripciones: list[str],
    categorias: list[str],
) -> list[dict]:
    """
    Parsea la respuesta compacta 'indice:Categoria' a la estructura
    que espera el clasificador.

    Formatos aceptados:
      0:Alimentación
      0: Alimentación
      0. Alimentación
      Alimentación  (sin índice — se infiere por posición)
    """
    import re
    import unicodedata

    def norm(s: str) -> str:
        s = s.lower().strip()
        s = unicodedata.normalize("NFD", s)
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

    cats_norm = {norm(c): c for c in categorias}

    def encontrar_categoria(texto_raw: str) -> str:
        t = norm(texto_raw)
        # Match exacto
        if t in cats_norm:
            return cats_norm[t]
        # Match parcial
        for k, v in cats_norm.items():
            if k in t or t in k:
                return v
        return "Sin categoría"

    resultados = []
    lineas = [l.strip() for l in texto.strip().split("\n") if l.strip()]

    # Intentar parsear con índice explícito
    patron = re.compile(r'^(\d+)\s*[:\.\-]\s*(.+)$')

    mapa = {}
    lineas_sin_indice = []

    for linea in lineas:
        m = patron.match(linea)
        if m:
            idx = int(m.group(1))
            cat_raw = m.group(2).strip()
            mapa[idx] = encontrar_categoria(cat_raw)
        else:
            # Sin índice — acumular por posición
            lineas_sin_indice.append(linea)

    if mapa:
        # Usar índices explícitos
        for i in range(len(descripciones)):
            cat = mapa.get(i, "Sin categoría")
            resultados.append({
                "indice": i,
                "categoria": cat,
                "comercio_limpio": _limpiar_comercio(descripciones[i]),
                "confianza": 0.85,
            })
    else:
        # Fallback: asignar por posición
        for i, linea in enumerate(lineas_sin_indice[:len(descripciones)]):
            resultados.append({
                "indice": i,
                "categoria": encontrar_categoria(linea),
                "comercio_limpio": _limpiar_comercio(descripciones[i]),
                "confianza": 0.75,
            })

        # Completar con Sin categoría si faltan
        for i in range(len(resultados), len(descripciones)):
            resultados.append({
                "indice": i,
                "categoria": "Sin categoría",
                "comercio_limpio": _limpiar_comercio(descripciones[i]),
                "confianza": 0.5,
            })

    return resultados


def _limpiar_comercio(descripcion: str) -> str:
    """
    Limpieza básica del nombre de comercio sin LLM.
    Elimina números de referencia, IDs de sucursal, etc.
    """
    import re
    texto = descripcion.strip()
    # Remover patrones comunes: #1234, *1234, números largos al final
    texto = re.sub(r'\s*#\d+', '', texto)
    texto = re.sub(r'\s+\d{4,}$', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    # Capitalizar correctamente
    return texto.strip().title()
