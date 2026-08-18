"""Recuperación por solapamiento de palabras (sin embeddings obligatorios)."""

from __future__ import annotations

import re
from typing import Any

from .almacen_chunks import AlmacenChunks

_STOP = {
    "el", "la", "los", "las", "de", "del", "un", "una", "y", "o", "a", "en",
    "que", "es", "por", "para", "con", "se", "su", "al", "lo", "como", "del",
    "una", "unos", "sobre", "este", "esta", "estos", "estas", "the", "and",
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

    def buscar(self, consulta: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.almacen.chunks:
            return []

        q = _tokens(consulta)
        # Preguntas genéricas sobre el doc → devolver primeros chunks
        genericas = {
            "documento", "pdf", "archivo", "texto", "contenido", "dice",
            "resume", "resumen", "habla", "trata", "tema",
        }
        if not q or q <= genericas:
            out = []
            for c in self.almacen.chunks[:top_k]:
                item = dict(c)
                item["score"] = 0.1
                out.append(item)
            return out

        puntuados: list[tuple[float, dict]] = []
        for c in self.almacen.chunks:
            ct = _tokens(c.get("texto", ""))
            if not ct:
                continue
            inter = q & ct
            # también prefijos (aprend / aprendizaje)
            extra = 0
            for qt in q:
                if any(ctok.startswith(qt[:4]) or qt.startswith(ctok[:4]) for ctok in ct if len(qt) >= 4):
                    extra += 0.25
            score = len(inter) + extra
            if score <= 0:
                continue
            puntuados.append((score, c))

        if not puntuados:
            # fallback: primeros chunks del almacén
            for c in self.almacen.chunks[:top_k]:
                item = dict(c)
                item["score"] = 0.05
                out_fb = item
                puntuados.append((0.05, c))

        puntuados.sort(key=lambda x: -x[0])
        out = []
        for score, c in puntuados[:top_k]:
            item = dict(c)
            item["score"] = round(float(score), 3)
            out.append(item)
        return out

    def contexto_para_prompt(self, consulta: str, top_k: int = 5) -> str:
        hits = self.buscar(consulta, top_k=top_k)
        if not hits:
            return ""
        partes = ["[Contexto de documentos]"]
        for h in hits:
            partes.append(f"- ({h.get('fuente')}) {h.get('texto', '')[:600]}")
        return "\n".join(partes)
