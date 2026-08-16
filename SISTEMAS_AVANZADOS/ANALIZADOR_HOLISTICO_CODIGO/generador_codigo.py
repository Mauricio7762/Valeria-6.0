"""Generador de código — plantillas mínimas para stubs faltantes."""

from __future__ import annotations


class GeneradorCodigo:
    def plantilla_modulo(self, nombre_clase: str, docstring: str = "") -> str:
        doc = docstring or f"Stub generado para {nombre_clase}."
        return (
            f'"""\n{doc}\n"""\n\n'
            f"from __future__ import annotations\n\n"
            f"from typing import Any\n\n\n"
            f"class {nombre_clase}:\n"
            f"    def __init__(self) -> None:\n"
            f"        self.enabled = True\n\n"
            f"    def estado(self) -> dict[str, Any]:\n"
            f"        return {{\"enabled\": self.enabled}}\n"
        )
