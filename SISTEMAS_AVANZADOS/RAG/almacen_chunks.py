"""Almacén persistente de chunks (JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT = _ROOT / "DATA" / "MEMORY" / "rag" / "chunks.json"


class AlmacenChunks:
    def __init__(self, ruta: Path | str | None = None) -> None:
        self.ruta = Path(ruta) if ruta else _DEFAULT
        self.chunks: list[dict[str, Any]] = []
        self.cargar()

    def cargar(self) -> int:
        if not self.ruta.exists():
            return 0
        try:
            data = json.loads(self.ruta.read_text(encoding="utf-8"))
            self.chunks = list(data.get("chunks", []))
            return len(self.chunks)
        except (json.JSONDecodeError, OSError):
            return 0

    def guardar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        payload = {"chunks": self.chunks}
        tmp = self.ruta.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.ruta)

    def agregar(self, nuevos: list[dict[str, Any]], dedup: bool = True) -> int:
        ids = {c.get("id") for c in self.chunks} if dedup else set()
        n = 0
        for c in nuevos:
            if dedup and c.get("id") in ids:
                continue
            self.chunks.append(c)
            ids.add(c.get("id"))
            n += 1
        if n:
            self.guardar()
        return n

    def total(self) -> int:
        return len(self.chunks)
