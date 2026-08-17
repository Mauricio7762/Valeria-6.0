"""Recuperación por solapamiento de palabras (sin embeddings obligatorios)."""

from __future__ import annotations

import re
from typing import Any

from .almacen_chunks import AlmacenChunks

_STOP = {
    "el", "la", "los", "las", "de", "del", "un", "una", "y", "o", "a", "en",
    "que", "es", "por", "para", "con", "se", "su", "al", "lo", "como",
}


def _tokens(texto: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-záéíóúñü0-9]+", (texto or "").lower())
        if len(t) > 2 and t not in _STOP
    }


class RetrieverRAG:
    def __init__(self, almacen: AlmacenChunks | None = None) -> None:
        self.almacen = almacen or AlmacenChunks()

    def buscar(self, consulta: str, top_k: int = 4) -> list[dict[str, Any]]:
        q = _tokens(consulta)
        if not q or not self.almacen.chunks:
            return []
        puntuados: list[tuple[float, dict]] = []
        for c in self.almacen.chunks:
            ct = _tokens(c.get("texto", ""))
            if not ct:
                continue
            inter = len(q & ct)
            if inter == 0:
                continue
            score = inter / (len(q) ** 0.5)
            puntuados.append((score, c))
        puntuados.sort(key=lambda x: -x[0])
        out = []
        for score, c in puntuados[:top_k]:
            item = dict(c)
            item["score"] = round(score, 3)
            out.append(item)
        return out

    def contexto_para_prompt(self, consulta: str, top_k: int = 4) -> str:
        hits = self.buscar(consulta, top_k=top_k)
        if not hits:
            return ""
        partes = ["[Contexto de documentos]"]
        for h in hits:
            partes.append(f"- ({h.get('fuente')}) {h.get('texto', '')[:500]}")
        return "\n".join(partes)
