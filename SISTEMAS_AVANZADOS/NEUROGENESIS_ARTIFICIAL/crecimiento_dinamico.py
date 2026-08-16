"""
Crecimiento dinámico (neurogénesis)
===================================
Crea nuevas conexiones en el grafo a partir de inferencias exitosas
y aprendizajes del usuario (hechos "inferidos" o refuerzo de rutas).
"""

from __future__ import annotations

from typing import Any, Protocol


class GrafoLike(Protocol):
    def agregar_hecho(self, sujeto: str, relacion: str, objeto: str, confianza: float = 1.0, origen: str = "usuario") -> Any: ...
    def buscar(self, sujeto: str | None = None, relacion: str | None = None, objeto: str | None = None) -> list: ...
    def relacionados(self, sujeto: str) -> list: ...
    def total_hechos(self) -> int: ...


class CrecimientoDinamico:
    def __init__(self) -> None:
        self.nuevas_conexiones = 0
        self.historial: list[dict[str, Any]] = []

    def crecer_desde_inferencia(
        self,
        grafo: GrafoLike,
        sujeto: str,
        relacion: str,
        objeto: str,
        confianza: float,
    ) -> bool:
        """Materializa una conclusión deductiva/abductiva como hecho inferido si no existe."""
        if not sujeto or not objeto or confianza < 0.5:
            return False
        existentes = grafo.buscar(sujeto, relacion, objeto)
        if existentes:
            return False
        grafo.agregar_hecho(sujeto, relacion, objeto, confianza=min(0.8, confianza), origen="inferido")
        self.nuevas_conexiones += 1
        self.historial.append(
            {"tipo": "inferido", "sujeto": sujeto, "relacion": relacion, "objeto": objeto, "confianza": confianza}
        )
        if len(self.historial) > 40:
            self.historial = self.historial[-40:]
        return True

    def crecer_desde_aprendizaje(self, sujeto: str, relacion: str, objeto: str) -> None:
        self.nuevas_conexiones += 1
        self.historial.append(
            {"tipo": "aprendizaje", "sujeto": sujeto, "relacion": relacion, "objeto": objeto}
        )

    def estado(self) -> dict[str, Any]:
        return {
            "nuevas_conexiones": self.nuevas_conexiones,
            "ultimas": self.historial[-5:],
        }
