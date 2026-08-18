"""
Extrae texto de PDF y lo parte en chunks.

Orden de extractores:
  1. opendataloader-pdf (si está instalado + Java) — mejor layout/tablas
  2. pypdf / PyPDF2 — liviano, siempre que esté instalado

No es obligatorio instalar OpenDataLoader; VALERIA sigue funcionando solo con pypdf.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any


def _limpiar(texto: str) -> str:
    texto = re.sub(r"[ \t]+", " ", texto or "")
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


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
        return ""
    partes: list[str] = []
    for page in reader.pages:
        try:
            partes.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(partes)


def _extraer_opendataloader(datos: bytes, nombre: str = "doc.pdf") -> str:
    """
    Usa el paquete opendataloader-pdf (requiere Java 11+ en el PATH).
    Escribe bytes a un temp file porque la API trabaja con rutas.
    """
    try:
        import opendataloader_pdf
    except ImportError:
        return ""

    suffix = Path(nombre).suffix if Path(nombre).suffix else ".pdf"
    try:
        with tempfile.TemporaryDirectory(prefix="valeria_odl_") as tmp:
            tmp_path = Path(tmp)
            pdf_path = tmp_path / f"input{suffix}"
            pdf_path.write_bytes(datos)
            out_dir = tmp_path / "out"
            out_dir.mkdir()
            # API típica: convert(input_path=..., output_dir=..., format=...)
            try:
                opendataloader_pdf.convert(
                    input_path=str(pdf_path),
                    output_dir=str(out_dir),
                    format="text",
                )
            except TypeError:
                # firmas alternativas según versión
                try:
                    opendataloader_pdf.convert(
                        [str(pdf_path)],
                        str(out_dir),
                        format="text",
                    )
                except Exception:
                    return ""
            except Exception:
                return ""

            # Buscar salida .txt / .md / .text
            candidatos = (
                list(out_dir.rglob("*.txt"))
                + list(out_dir.rglob("*.md"))
                + list(out_dir.rglob("*.text"))
                + list(out_dir.rglob("*.markdown"))
            )
            if not candidatos:
                # a veces el nombre base del pdf
                candidatos = [p for p in out_dir.rglob("*") if p.is_file()]
            textos: list[str] = []
            for c in sorted(candidatos):
                try:
                    textos.append(c.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    continue
            return "\n\n".join(textos)
    except Exception:
        return ""


def extraer_texto_pdf(datos: bytes, nombre: str = "documento.pdf") -> tuple[str, str]:
    """
    Devuelve (texto, motor) donde motor es
    'opendataloader' | 'pypdf' | 'ninguno'.
    """
    texto = _limpiar(_extraer_opendataloader(datos, nombre=nombre))
    if len(texto) >= 40:
        return texto, "opendataloader"

    texto_py = _limpiar(_extraer_pypdf(datos))
    if texto_py:
        return texto_py, "pypdf"

    # Si ODL devolvió algo muy corto pero pypdf nada, usar ODL igual
    if texto:
        return texto, "opendataloader"

    return "", "ninguno"


class IngestaPDF:
    def __init__(self, max_chars_chunk: int = 800, solape: int = 100) -> None:
        self.max_chars = max_chars_chunk
        self.solape = solape
        self.ultimo_motor: str = "ninguno"

    def extraer_texto(self, datos: bytes, nombre: str = "documento.pdf") -> str:
        texto, motor = extraer_texto_pdf(datos, nombre=nombre)
        self.ultimo_motor = motor
        return texto

    def chunkear(self, texto: str, fuente: str = "pdf") -> list[dict[str, Any]]:
        if not texto:
            return []
        chunks: list[dict[str, Any]] = []
        i = 0
        n = len(texto)
        idx = 0
        while i < n:
            fin = min(i + self.max_chars, n)
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
                        "motor": self.ultimo_motor,
                    }
                )
                idx += 1
            if fin >= n:
                break
            i = max(fin - self.solape, i + 1)
        return chunks

    def ingerir(self, datos: bytes, nombre: str = "documento.pdf") -> list[dict[str, Any]]:
        texto = self.extraer_texto(datos, nombre=nombre)
        return self.chunkear(texto, fuente=nombre)
