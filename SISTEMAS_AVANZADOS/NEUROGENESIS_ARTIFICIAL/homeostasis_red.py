"""
Homeostasis de la red de conocimiento
=====================================
Mantiene el grafo en un rango saludable de hechos y detecta sobrecarga.
"""

from __future__ import annotations

from typing import Any


class HomeostasisRed:
    def __init__(self, max_hechos: int = 500, min_hechos: int = 5) -> None:
        self.max_hechos = max_hechos
        self.min_hechos = min_hechos
        self.alertas = 0

    def evaluar(self, total_hechos: int) -> dict[str, Any]:
        estado = "ok"
        if total_hechos >= self.max_hechos:
            estado = "sobrecrecimiento"
            self.alertas += 1
        elif total_hechos < self.min_hechos:
            estado = "subdesarrollo"
        return {
            "estado": estado,
            "total_hechos": total_hechos,
            "max": self.max_hechos,
            "alertas": self.alertas,
            "necesita_poda": estado == "sobrecrecimiento",
        }
