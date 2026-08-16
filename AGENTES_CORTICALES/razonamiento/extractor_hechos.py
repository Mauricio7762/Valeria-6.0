"""
Extractor de Hechos (Aprendizaje por Enseñanza)
=================================================
Detecta afirmaciones del usuario y las convierte en hechos
(sujeto, relación, objeto) para el grafo de conocimiento.
Conservador: si parece pregunta, no extrae nada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PALABRAS_INTERROGATIVAS = (
    "que", "qué", "como", "cómo", "cual", "cuál", "cuales", "cuáles",
    "quien", "quién", "donde", "dónde", "cuando", "cuándo",
    "por",  # "por que" / "por qué" se cubre con la primera palabra "por"
)

# (patrón, relación) — más específico primero
# Nota: "del" / "de la" / "de los" / "de las" son contracciones de "de + artículo"
_PATRONES_ENSEÑANZA: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"^(.+?)\s+es\s+parte\s+(?:del|de\s+la|de\s+los|de\s+las|de)\s+(.+?)[\.\!]?$",
            re.IGNORECASE,
        ),
        "es_parte_de",
    ),
    (
        re.compile(r"^(.+?)\s+es\s+(?:un|una)\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "es_un",
    ),
    (
        re.compile(r"^(.+?)\s+causa\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "causa",
    ),
    (
        re.compile(
            r"^(.+?)\s+tiene\s+(?:la\s+)?funci[oó]n\s+(?:de\s+)?(.+?)[\.\!]?$",
            re.IGNORECASE,
        ),
        "tiene_funcion",
    ),
    (
        re.compile(
            r"^(.+?)\s+tiene\s+(?:la\s+)?propiedad\s+(?:de\s+)?(.+?)[\.\!]?$",
            re.IGNORECASE,
        ),
        "tiene_propiedad",
    ),
    (
        re.compile(r"^(.+?)\s+tiene\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "tiene",
    ),
    (
        re.compile(r"^(.+?)\s+es\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "es",
    ),
]

_PREFIJOS_EXPLICITOS = re.compile(
    r"^(?:recorda|recuerda|aprende|anota|guarda)\s+que\s+",
    re.IGNORECASE,
)

_ARTICULO_INICIAL = re.compile(r"^(?:el|la|los|las|un|una)\s+", re.IGNORECASE)

# Frases interrogativas multi-palabra al inicio (sin signo de pregunta)
_INICIO_INTERROGATIVO = re.compile(
    r"^(?:por\s+qu[eé]|a\s+qu[eé]|de\s+qu[eé]|en\s+qu[eé])\b",
    re.IGNORECASE,
)


def _sin_articulo(texto: str) -> str:
    return _ARTICULO_INICIAL.sub("", texto, count=1).strip()


@dataclass
class HechoExtraido:
    sujeto: str
    relacion: str
    objeto: str
    explicito: bool  # True si usó "recordá que..." / "aprendé que..."


def extraer_hecho(texto: str) -> HechoExtraido | None:
    if not texto or "?" in texto or "¿" in texto:
        return None

    texto_norm = texto.strip().lower()

    if _INICIO_INTERROGATIVO.match(texto_norm):
        return None

    primera_palabra = texto_norm.split(" ", 1)[0] if texto_norm else ""
    if primera_palabra in _PALABRAS_INTERROGATIVAS:
        return None

    explicito = bool(_PREFIJOS_EXPLICITOS.match(texto_norm))
    if explicito:
        texto_norm = _PREFIJOS_EXPLICITOS.sub("", texto_norm).strip()

    for patron, relacion in _PATRONES_ENSEÑANZA:
        m = patron.match(texto_norm)
        if not m:
            continue
        sujeto = _sin_articulo(m.group(1).strip())
        objeto = _sin_articulo(m.group(2).strip())
        if not sujeto or not objeto:
            return None
        # Evitar basura demasiado corta o idéntica
        if sujeto == objeto or len(sujeto) < 2 or len(objeto) < 2:
            return None
        return HechoExtraido(
            sujeto=sujeto,
            relacion=relacion,
            objeto=objeto,
            explicito=explicito,
        )

    return None
