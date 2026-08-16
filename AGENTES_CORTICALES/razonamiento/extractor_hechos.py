"""
Extractor de Hechos (Aprendizaje por Enseñanza)
===============================================
Detecta afirmaciones y las convierte en (sujeto, relación, objeto).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PALABRAS_INTERROGATIVAS = (
    "que", "qué", "como", "cómo", "cual", "cuál", "cuales", "cuáles",
    "quien", "quién", "donde", "dónde", "cuando", "cuándo", "por",
)

_PATRONES_ENSEÑANZA: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"^(.+?)\s+es\s+parte\s+(?:del|de\s+la|de\s+los|de\s+las|de)\s+(.+?)[\.\!]?$",
            re.IGNORECASE,
        ),
        "es_parte_de",
    ),
    (
        re.compile(
            r"^(.+?)\s+(?:pertenece|pertenecen)\s+a\s+(.+?)[\.\!]?$",
            re.IGNORECASE,
        ),
        "es_parte_de",
    ),
    (
        re.compile(r"^(.+?)\s+es\s+(?:un|una)\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "es_un",
    ),
    (
        re.compile(r"^(.+?)\s+significa\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "significa",
    ),
    (
        re.compile(r"^(.+?)\s+causa\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "causa",
    ),
    (
        re.compile(r"^(.+?)\s+(?:provoca|genera|produce)\s+(.+?)[\.\!]?$", re.IGNORECASE),
        "causa",
    ),
    (
        re.compile(
            r"^(.+?)\s+(?:sirve\s+para|se\s+usa\s+para|permite)\s+(.+?)[\.\!]?$",
            re.IGNORECASE,
        ),
        "tiene_funcion",
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
_INICIO_INTERROGATIVO = re.compile(
    r"^(?:por\s+qu[eé]|a\s+qu[eé]|de\s+qu[eé]|en\s+qu[eé]|para\s+qu[eé])\b",
    re.IGNORECASE,
)


def _sin_articulo(texto: str) -> str:
    return _ARTICULO_INICIAL.sub("", texto, count=1).strip()


@dataclass
class HechoExtraido:
    sujeto: str
    relacion: str
    objeto: str
    explicito: bool


def extraer_hecho(texto: str) -> HechoExtraido | None:
    if not texto or "?" in texto or "¿" in texto:
        return None

    texto_norm = texto.strip().lower()
    if _INICIO_INTERROGATIVO.match(texto_norm):
        return None

    primera = texto_norm.split(" ", 1)[0] if texto_norm else ""
    if primera in _PALABRAS_INTERROGATIVAS:
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
        if not sujeto or not objeto or sujeto == objeto:
            return None
        if len(sujeto) < 2 or len(objeto) < 2:
            return None
        return HechoExtraido(sujeto=sujeto, relacion=relacion, objeto=objeto, explicito=explicito)

    return None
