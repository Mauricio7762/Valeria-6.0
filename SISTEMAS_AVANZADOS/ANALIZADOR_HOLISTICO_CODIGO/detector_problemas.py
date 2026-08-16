"""Detector de problemas — sintaxis, archivos enormes, TODOs, passes, excepto desnudos."""

from __future__ import annotations

import re
from typing import Any


class DetectorProblemas:
    def detectar(self, archivos: list[dict[str, Any]], extracciones: list[dict[str, Any]]) -> list[dict[str, str]]:
        problemas: list[dict[str, str]] = []

        for ex in extracciones:
            if ex.get("error_sintaxis"):
                problemas.append(
                    {
                        "severidad": "alta",
                        "tipo": "sintaxis",
                        "path": ex.get("path", ""),
                        "detalle": ex["error_sintaxis"],
                    }
                )

        for a in archivos:
            path = a["path"]
            text = a.get("texto", "")
            if a["lineas"] > 400:
                problemas.append(
                    {
                        "severidad": "media",
                        "tipo": "archivo_grande",
                        "path": path,
                        "detalle": f"{a['lineas']} líneas — conviene dividir",
                    }
                )
            todos = len(re.findall(r"\bTODO\b|\bFIXME\b", text))
            if todos:
                problemas.append(
                    {
                        "severidad": "baja",
                        "tipo": "todo_fixme",
                        "path": path,
                        "detalle": f"{todos} marcadores TODO/FIXME",
                    }
                )
            # except: desnudo
            if re.search(r"except\s*:", text):
                problemas.append(
                    {
                        "severidad": "media",
                        "tipo": "except_desnudo",
                        "path": path,
                        "detalle": "Hay un `except:` sin tipo — puede ocultar errores",
                    }
                )
            # muchos pass
            passes = len(re.findall(r"^\s*pass\s*$", text, re.M))
            if passes >= 5:
                problemas.append(
                    {
                        "severidad": "baja",
                        "tipo": "stubs",
                        "path": path,
                        "detalle": f"{passes} `pass` — posibles stubs sin implementar",
                    }
                )

        return problemas
