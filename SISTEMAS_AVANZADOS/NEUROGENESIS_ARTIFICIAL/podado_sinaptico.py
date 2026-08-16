"""
Podado sináptico
================
Elimina o debilita hechos de baja utilidad (baja confianza + origen inferido
+ poco uso). Diseñado para cooperar con Microglía (conteo de podas).
"""

from __future__ import annotations

from typing import Any


class PodadoSinaptico:
    def __init__(self, umbral_confianza: float = 0.35, min_hechos_para_podar: int = 25) -> None:
        self.umbral = umbral_confianza
        self.min_hechos = min_hechos_para_podar
        self.podados = 0
        self.historial: list[str] = []

    def podar(self, grafo: Any, uso_arista: dict | None = None, microglia: Any = None) -> int:
        hechos = getattr(grafo, "_hechos", None)
        if hechos is None or len(hechos) < self.min_hechos:
            return 0

        uso_arista = uso_arista or {}
        mantener = []
        eliminados = 0
        for h in hechos:
            key = (h.sujeto, h.relacion, h.objeto)
            hits = uso_arista.get(key, 0)
            # No podar semilla (base) ni aprendizajes recientes del usuario con buena conf
            if h.origen == "base":
                mantener.append(h)
                continue
            if h.origen == "usuario" and h.confianza >= 0.7:
                mantener.append(h)
                continue
            if h.origen == "inferido" and h.confianza < self.umbral and hits == 0:
                eliminados += 1
                self.historial.append(f"{h.sujeto}-{h.relacion}-{h.objeto}")
                continue
            if h.confianza < self.umbral * 0.8 and hits == 0 and h.origen != "usuario":
                eliminados += 1
                self.historial.append(f"{h.sujeto}-{h.relacion}-{h.objeto}")
                continue
            mantener.append(h)

        if eliminados:
            grafo._hechos = mantener
            grafo._por_sujeto = {}
            grafo._por_relacion = {}
            for h in mantener:
                grafo._por_sujeto.setdefault(h.sujeto, []).append(h)
                grafo._por_relacion.setdefault(h.relacion, []).append(h)
            self.podados += eliminados
            if microglia is not None and hasattr(microglia, "pruned_routes"):
                microglia.pruned_routes += eliminados
            if len(self.historial) > 30:
                self.historial = self.historial[-30:]
        return eliminados

    def estado(self) -> dict[str, Any]:
        return {"podados": self.podados, "ultimos": self.historial[-5:]}
