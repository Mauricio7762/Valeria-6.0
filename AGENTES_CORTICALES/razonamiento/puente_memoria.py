"""
Puente Memoria episódica ↔ Grafo semántico
==========================================
- Busca en episodios hechos enseñables (extractor)
- Sugiere promover afirmaciones repetidas al grafo
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .extractor_hechos import extraer_hecho, HechoExtraido


def hechos_desde_episodios(episodios: list[dict[str, Any]]) -> list[HechoExtraido]:
    """Extrae hechos de contenidos episódicos que sean afirmaciones."""
    out: list[HechoExtraido] = []
    for ep in episodios:
        texto = str(ep.get("contenido") or "")
        h = extraer_hecho(texto)
        if h:
            out.append(h)
    return out


def sugerir_promocion(
    episodios: list[dict[str, Any]], min_repeticiones: int = 2
) -> list[tuple[HechoExtraido, int]]:
    """
    Hechos que aparecen varias veces en la episódica (candidatos a semántica).
    """
    contador: Counter[tuple[str, str, str]] = Counter()
    ejemplos: dict[tuple[str, str, str], HechoExtraido] = {}
    for h in hechos_desde_episodios(episodios):
        key = (h.sujeto, h.relacion, h.objeto)
        contador[key] += 1
        ejemplos[key] = h
    return [
        (ejemplos[k], n)
        for k, n in contador.most_common()
        if n >= min_repeticiones
    ]
