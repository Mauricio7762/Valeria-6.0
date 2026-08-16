"""
Coordinador de neurogénesis
===========================
Un solo punto de entrada para crecimiento, plasticidad, poda y métricas.
"""

from __future__ import annotations

from typing import Any

from .crecimiento_dinamico import CrecimientoDinamico
from .homeostasis_red import HomeostasisRed
from .optimizacion_topologica import OptimizacionTopologica
from .plasticidad_estructural import PlasticidadEstructural
from .podado_sinaptico import PodadoSinaptico


class CoordinadorNeurogenesis:
    def __init__(self) -> None:
        self.crecimiento = CrecimientoDinamico()
        self.plasticidad = PlasticidadEstructural()
        self.poda = PodadoSinaptico()
        self.homeostasis = HomeostasisRed()
        self.topologia = OptimizacionTopologica()
        self.ciclos = 0

    def on_razonamiento(self, grafo: Any, razon: dict[str, Any]) -> None:
        """Llamar tras cada respuesta de razonamiento."""
        est = razon.get("estrategia")
        conf = float(razon.get("confianza") or 0)
        # Registrar uso a partir de pasos si hay hechos en conclusión simple
        conclusion = str(razon.get("conclusion") or "")
        if est == "aprendizaje":
            # el hecho ya está en el grafo; contamos crecimiento simbólico
            self.crecimiento.crecer_desde_aprendizaje("usuario", "enseño", "hecho")
        elif est == "deductiva" and conf >= 0.55:
            # intentar materializar cadenas cortas no aplica sin parseo fino;
            # plasticidad se alimenta cuando el motor expone hechos_usados — opcional
            pass

    def registrar_hecho_usado(self, sujeto: str, relacion: str, objeto: str) -> None:
        self.plasticidad.registrar_uso(sujeto, relacion, objeto)

    def ciclo_mantenimiento(self, grafo: Any, microglia: Any = None) -> dict[str, Any]:
        """Plasticidad + homeostasis + poda si hace falta."""
        self.ciclos += 1
        reforzados = self.plasticidad.reforzar_hechos_usados(grafo)
        total = grafo.total_hechos() if hasattr(grafo, "total_hechos") else 0
        home = self.homeostasis.evaluar(total)
        podados = 0
        if home.get("necesita_poda") or (self.ciclos % 15 == 0 and total > 30):
            podados = self.poda.podar(
                grafo,
                uso_arista=dict(self.plasticidad.uso_arista),
                microglia=microglia,
            )
        topo = self.topologia.analizar(grafo)
        return {
            "reforzados": reforzados,
            "podados": podados,
            "homeostasis": home,
            "topologia": topo,
        }

    def estado(self) -> dict[str, Any]:
        return {
            "ciclos": self.ciclos,
            "crecimiento": self.crecimiento.estado(),
            "plasticidad": self.plasticidad.estado(),
            "poda": self.poda.estado(),
            "homeostasis": {
                "max_hechos": self.homeostasis.max_hechos,
                "alertas": self.homeostasis.alertas,
            },
        }
