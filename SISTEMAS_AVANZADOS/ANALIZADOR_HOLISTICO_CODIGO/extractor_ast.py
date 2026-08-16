"""Extractor AST — clases, funciones, imports por archivo."""

from __future__ import annotations

import ast
from typing import Any


class ExtractorAST:
    def extraer(self, codigo: str, path: str = "") -> dict[str, Any]:
        try:
            tree = ast.parse(codigo)
        except SyntaxError as e:
            return {
                "path": path,
                "error_sintaxis": str(e),
                "clases": [],
                "funciones": [],
                "imports": [],
                "async_funcs": 0,
            }

        clases: list[str] = []
        funciones: list[str] = []
        imports: list[str] = []
        async_funcs = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                clases.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                funciones.append(node.name)
                async_funcs += 1
            elif isinstance(node, ast.FunctionDef):
                funciones.append(node.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    imports.append(a.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for a in node.names:
                    imports.append(f"{mod}.{a.name}" if mod else a.name)

        return {
            "path": path,
            "clases": clases,
            "funciones": funciones,
            "imports": imports,
            "async_funcs": async_funcs,
            "error_sintaxis": None,
        }
