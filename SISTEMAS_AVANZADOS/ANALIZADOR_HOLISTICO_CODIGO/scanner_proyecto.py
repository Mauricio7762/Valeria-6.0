"""Scanner de proyecto — inventaria archivos Python y tamaños."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ScannerProyecto:
    def __init__(self, raiz: Path | str) -> None:
        self.raiz = Path(raiz).resolve()

    def escanear(self, max_files: int = 200) -> list[dict[str, Any]]:
        archivos: list[dict[str, Any]] = []
        ignore = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}
        for path in sorted(self.raiz.rglob("*.py")):
            if any(part in ignore for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(self.raiz))
            archivos.append(
                {
                    "path": rel,
                    "lineas": text.count("\n") + 1,
                    "bytes": len(text.encode("utf-8")),
                    "texto": text,
                }
            )
            if len(archivos) >= max_files:
                break
        return archivos

    def resumen(self, archivos: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "archivos": len(archivos),
            "lineas_totales": sum(a["lineas"] for a in archivos),
            "bytes_totales": sum(a["bytes"] for a in archivos),
            "top_grandes": sorted(archivos, key=lambda a: -a["lineas"])[:8],
        }
