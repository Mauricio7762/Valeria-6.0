"""
Plasticidad estructural
=======================
Refuerza conexiones usadas (sube confianza) y registra uso de aristas.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class PlasticidadEstructural:
    def __init__(self) -> None:
        self.uso_arista: dict[tuple[str, str, str], int] = defaultdict(int)
        self.refuerzos = 0

    def registrar_uso(self, sujeto: str, relacion: str, objeto: str) -> None:
        key = (sujeto, relacion, objeto)
        self.uso_arista[key] += 1

    def reforzar_hechos_usados(self, grafo: Any, factor: float = 0.03) -> int:
        """Aumenta ligeramente la confianza de hechos muy usados (si el grafo lo permite)."""
        reforzados = 0
        # Hecho es frozen dataclass — recreamos vía agregar no sirve; mutamos lista interna si existe
        hechos = getattr(grafo, "_hechos", None)
        if hechos is None:
            return 0
        nuevos = []
        cambiado = False
        from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import Hecho

        for h in hechos:
            key = (h.sujeto, h.relacion, h.objeto)
            hits = self.uso_arista.get(key, 0)
            if hits >= 2 and h.confianza < 0.99:
                nueva_conf = min(0.99, h.confianza + factor * min(hits, 5))
                if nueva_conf > h.confianza:
                    h = Hecho(h.sujeto, h.relacion, h.objeto, nueva_conf, h.origen)
                    reforzados += 1
                    cambiado = True
                    self.refuerzos += 1
            nuevos.append(h)
        if cambiado:
            grafo._hechos = nuevos
            # reconstruir índices
            grafo._por_sujeto = {}
            grafo._por_relacion = {}
            for h in nuevos:
                grafo._por_sujeto.setdefault(h.sujeto, []).append(h)
                grafo._por_relacion.setdefault(h.relacion, []).append(h)
        return reforzados

    def estado(self) -> dict[str, Any]:
        top = sorted(self.uso_arista.items(), key=lambda x: -x[1])[:5]
        return {
            "aristas_rastreado": len(self.uso_arista),
            "refuerzos": self.refuerzos,
            "top_uso": [{"arista": k, "hits": v} for k, v in top],
        }
