"""
Extractor de Hechos (Aprendizaje por Enseñanza)
=================================================
Detecta cuándo el usuario está AFIRMANDO algo (no preguntando) y lo
convierte en un hecho (sujeto, relación, objeto) para el grafo de
conocimiento. Es lo que le permite a VALERIA aprender en la
conversación en vez de depender solo de la base semilla.

Deliberadamente conservador: si hay duda de que sea una pregunta,
NO extrae nada (mejor no aprender que aprender basura).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PALABRAS_INTERROGATIVAS = (
    "que", "qué", "como", "cómo", "cual", "cuál", "cuales", "cuáles",
    "quien", "quién", "donde", "dónde", "cuando", "cuándo", "por que", "por qué",
)

# (patrón, relación) — orden importa: más específico primero
_PATRONES_ENSEÑANZA: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(.+?)\s+es\s+parte\s+de\s+(.+?)[\.\!]?$"), "es_parte_de"),
    (re.compile(r"^(.+?)\s+es\s+(?:un|una)\s+(.+?)[\.\!]?$"), "es_un"),
    (re.compile(r"^(.+?)\s+causa\s+(.+?)[\.\!]?$"), "causa"),
    (re.compile(r"^(.+?)\s+tiene\s+(?:la\s+)?funci[oó]n\s+(?:de\s+)?(.+?)[\.\!]?$"), "tiene_funcion"),
    (re.compile(r"^(.+?)\s+tiene\s+(?:la\s+)?propiedad\s+(?:de\s+)?(.+?)[\.\!]?$"), "tiene_propiedad"),
    (re.compile(r"^(.+?)\s+tiene\s+(.+?)[\.\!]?$"), "tiene"),
    (re.compile(r"^(.+?)\s+es\s+(.+?)[\.\!]?$"), "es"),
]

_PREFIJOS_EXPLICITOS = re.compile(
    r"^(?:recorda|recuerda|aprende|anota|guarda)\s+que\s+", re.IGNORECASE
)

_ARTICULO_INICIAL = re.compile(r"^(?:el|la|los|las|un|una)\s+")


def _sin_articulo(texto: str) -> str:
    """Quita el artículo inicial para que 'el futsal' y 'futsal' sean el
    mismo sujeto (así coincide con cómo se extraen entidades en preguntas)."""
    return _ARTICULO_INICIAL.sub("", texto, count=1).strip()


@dataclass
class HechoExtraido:
    sujeto: str
    relacion: str
    objeto: str
    explicito: bool  # True si el usuario usó "recordá que..." / "aprendé que..."


def extraer_hecho(texto: str) -> HechoExtraido | None:
    if not texto or "?" in texto or "¿" in texto:
        return None

    texto_norm = texto.strip().lower()

    primera_palabra = texto_norm.split(" ", 1)[0] if texto_norm else ""
    if primera_palabra in _PALABRAS_INTERROGATIVAS:
        return None

    explicito = bool(_PREFIJOS_EXPLICITOS.match(texto_norm))
    if explicito:
        texto_norm = _PREFIJOS_EXPLICITOS.sub("", texto_norm)

    for patron, relacion in _PATRONES_ENSEÑANZA:
        m = patron.match(texto_norm)
        if not m:
            continue
        sujeto, objeto = m.group(1).strip(), m.group(2).strip()
        sujeto = _sin_articulo(sujeto)
        if not sujeto or not objeto or len(sujeto) > 60 or len(objeto) > 80:
            continue
        return HechoExtraido(sujeto, relacion, objeto, explicito)

    return None
