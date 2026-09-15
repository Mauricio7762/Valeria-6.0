"""PDF → texto → aprender_texto → grafo."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def extraer_texto_pdf(ruta: str | Path) -> str:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe: {ruta}")
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ImportError("Instalá pypdf: pip install pypdf") from e

    reader = PdfReader(str(ruta))
    partes: list[str] = []
    for page in reader.pages:
        t = (page.extract_text() or "").strip()
        if t:
            partes.append(t)
    return "\n\n".join(partes)


def aprender_pdf(
    ruta: str | Path,
    grafo: Any,
    max_chars: int = 12000,
    usar_llm: bool = True,
) -> dict:
    from .aprender_texto import aprender_texto

    texto = extraer_texto_pdf(ruta)
    if not texto.strip():
        return {
            "texto_len": 0,
            "hechos": [],
            "mensaje": "El PDF no tiene texto extraíble (¿está escaneado?).",
        }
    if len(texto) > max_chars:
        texto = texto[:max_chars]

    hechos = aprender_texto(texto, grafo, usar_llm=usar_llm)
    return {
        "texto_len": len(texto),
        "hechos": hechos,
        "mensaje": (
            f"Leí {len(texto)} caracteres de {Path(ruta).name}. "
            f"Guardé {len(hechos)} hecho(s)."
        ),
    }
