"""Fachada: ingerir PDF y recuperar contexto."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .almacen_chunks import AlmacenChunks
from .ingesta_pdf import IngestaPDF
from .retriever import RetrieverRAG


class OrquestadorRAG:
    def __init__(self, ruta_almacen: Path | str | None = None) -> None:
        self.ingesta = IngestaPDF()
        self.almacen = AlmacenChunks(ruta_almacen)
        self.retriever = RetrieverRAG(self.almacen)

    def ingerir_pdf(self, datos: bytes, nombre: str) -> dict[str, Any]:
        chunks = self.ingesta.ingerir(datos, nombre=nombre)
        n = self.almacen.agregar(chunks)
        return {
            "ok": True,
            "archivo": nombre,
            "chunks_nuevos": n,
            "chunks_totales": self.almacen.total(),
            "chars_texto": sum(len(c.get("texto", "")) for c in chunks),
            "motor": getattr(self.ingesta, "ultimo_motor", "desconocido"),
        }

    def recuperar(self, consulta: str, top_k: int = 4) -> dict[str, Any]:
        hits = self.retriever.buscar(consulta, top_k=top_k)
        return {
            "hits": hits,
            "contexto": self.retriever.contexto_para_prompt(consulta, top_k=top_k),
        }
