"""
Curiosidad perceptual
=====================
Interés por estímulos nuevos o contrastes (en texto: entidades nuevas,
intenciones poco vistas).
"""

from __future__ import annotations

from collections import Counter
from typing import Any


class CuriosidadPerceptual:
    def __init__(self) -> None:
        self.entidades_vistas: Counter[str] = Counter()
        self.intenciones_vistas: Counter[str] = Counter()

    def observar(self, entidad: str | None, intencion: str | None) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        if entidad:
            self.entidades_vistas[entidad] += 1
            if self.entidades_vistas[entidad] == 1:
                out.append(
                    {
                        "tipo": "perceptual",
                        "pregunta": f"Es la primera vez que aparece «{entidad}». ¿Qué es exactamente?",
                        "origen": "novedad_entidad",
                    }
                )
        if intencion:
            self.intenciones_vistas[intencion] += 1
        return out

    def estado(self) -> dict[str, Any]:
        return {
            "entidades_distintas": len(self.entidades_vistas),
            "top_entidades": self.entidades_vistas.most_common(5),
            "intenciones": dict(self.intenciones_vistas),
        }
