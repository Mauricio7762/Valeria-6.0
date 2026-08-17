"""Extrae texto de PDF y lo parte en chunks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _extraer_pypdf(datos: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return ""
    import io
    try:
        reader = PdfReader(io.BytesIO(datos))
    except Exception:
        # Archivo corrupto o que no es un PDF real: no romper la ingesta.
        return ""
    partes = []
    for page in reader.pages:
        try:
            partes.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(partes)


class IngestaPDF:
    def __init__(self, max_chars_chunk: int = 800, solape: int = 100) -> None:
        self.max_chars = max_chars_chunk
        self.solape = solape

    def extraer_texto(self, datos: bytes) -> str:
        texto = _extraer_pypdf(datos)
        texto = re.sub(r"[ \t]+", " ", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        return texto.strip()

    def chunkear(self, texto: str, fuente: str = "pdf") -> list[dict[str, Any]]:
        if not texto:
            return []
        chunks: list[dict[str, Any]] = []
        i = 0
        n = len(texto)
        idx = 0
        while i < n:
            fin = min(i + self.max_chars, n)
            # cortar en espacio si se puede
            if fin < n:
                corte = texto.rfind(" ", i, fin)
                if corte > i + self.max_chars // 2:
                    fin = corte
            frag = texto[i:fin].strip()
            if frag:
                chunks.append(
                    {
                        "id": f"{fuente}:{idx}",
                        "texto": frag,
                        "fuente": fuente,
                        "offset": i,
                    }
                )
                idx += 1
            if fin >= n:
                break
            i = max(fin - self.solape, i + 1)
        return chunks

    def ingerir(self, datos: bytes, nombre: str = "documento.pdf") -> list[dict[str, Any]]:
        texto = self.extraer_texto(datos)
        return self.chunkear(texto, fuente=nombre)
