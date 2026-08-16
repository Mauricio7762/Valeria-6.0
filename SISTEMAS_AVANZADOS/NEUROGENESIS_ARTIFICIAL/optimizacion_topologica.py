"""
Optimización topológica
=======================
Métricas simples del grafo: densidad, sujetos huérfanos, relaciones dominantes.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


class OptimizacionTopologica:
    def analizar(self, grafo: Any) -> dict[str, Any]:
        hechos = list(getattr(grafo, "_hechos", []) or [])
        if not hechos:
            return {"hechos": 0, "densidad_relativa": 0.0}

        sujetos = {h.sujeto for h in hechos}
        objetos = {h.objeto for h in hechos}
        nodos = sujetos | objetos
        rels = Counter(h.relacion for h in hechos)

        # sujetos que no aparecen como objeto de nadie (hojas inversas / raíces)
        solo_sujeto = sujetos - objetos
        solo_objeto = objetos - sujetos

        n = len(nodos) or 1
        # densidad proxy: hechos / nodos
        densidad = len(hechos) / n

        return {
            "hechos": len(hechos),
            "nodos": len(nodos),
            "densidad_relativa": round(densidad, 3),
            "relaciones_top": rels.most_common(5),
            "nodos_solo_sujeto": len(solo_sujeto),
            "nodos_solo_objeto": len(solo_objeto),
        }
