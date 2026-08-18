"""
Promueve conocimiento desde fragmentos RAG (PDF) hacia el grafo.

Usa el extractor de hechos existente sobre oraciones candidatas de cada chunk.
"""

from __future__ import annotations

import re
from typing import Any

from AGENTES_CORTICALES.razonamiento.extractor_hechos import extraer_hecho


def _oraciones(texto: str) -> list[str]:
    t = re.sub(r"\s+", " ", (texto or "").strip())
    if not t:
        return []
    parts = re.split(r"(?<=[\.\!\?])\s+", t)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def promover_chunks_a_grafo(
    grafo: Any,
    chunks: list[dict],
    *,
    max_hechos: int = 40,
    origen: str = "rag",
) -> dict[str, Any]:
    """
    Intenta extraer hechos de los textos de chunks y agregarlos al grafo.
    Devuelve estadísticas.
    """
    agregados = 0
    intentos = 0
    ejemplos: list[str] = []
    vistos: set[tuple[str, str, str]] = set()

    for ch in chunks:
        if agregados >= max_hechos:
            break
        texto = ch.get("texto") or ""
        for ora in _oraciones(texto):
            if agregados >= max_hechos:
                break
            # Evitar interrogativas
            if "?" in ora or "¿" in ora:
                continue
            intentos += 1
            h = extraer_hecho(ora)
            if not h:
                continue
            key = (h.sujeto.lower(), h.relacion, h.objeto.lower())
            if key in vistos:
                continue
            vistos.add(key)
            antes = grafo.total_hechos() if hasattr(grafo, "total_hechos") else None
            grafo.agregar_hecho(
                h.sujeto,
                h.relacion,
                h.objeto,
                confianza=0.7,
                origen=origen,
            )
            despues = grafo.total_hechos() if hasattr(grafo, "total_hechos") else None
            if antes is None or (despues is not None and despues > antes):
                agregados += 1
                if len(ejemplos) < 5:
                    ejemplos.append(f"{h.sujeto} —{h.relacion}→ {h.objeto}")

    return {
        "intentos": intentos,
        "agregados": agregados,
        "ejemplos": ejemplos,
    }
