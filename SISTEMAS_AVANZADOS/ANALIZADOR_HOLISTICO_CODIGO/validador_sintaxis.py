"""Validador de sintaxis — compile() por archivo."""

from __future__ import annotations

from typing import Any


class ValidadorSintaxis:
    def validar(self, path: str, codigo: str) -> dict[str, Any]:
        try:
            compile(codigo, path, "exec")
            return {"path": path, "ok": True, "error": None}
        except SyntaxError as e:
            return {"path": path, "ok": False, "error": f"{e.msg} (línea {e.lineno})"}
