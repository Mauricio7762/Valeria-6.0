"""
Metacognición nivel 4 — Ajuste
==============================
Aprende de aciertos/fallos recientes y ajusta preferencias:
- preferir estrategias que dieron alta confianza
- penalizar estrategias que fallaron
- umbral para pedir enseñanza
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .nivel1_monitoreo import RegistroMeta


@dataclass
class PreferenciasEstrategia:
    """Pesos relativos por estrategia (mayor = más preferida)."""

    pesos: dict[str, float] = field(
        default_factory=lambda: {
            "deductiva": 1.0,
            "abductiva": 1.0,
            "cbr": 0.8,
            "aprendizaje": 1.0,
        }
    )
    umbral_pedir_ensenanza: float = 0.4
    total_ajustes: int = 0

    def ordenar(self, estrategias: list[str]) -> list[str]:
        return sorted(
            estrategias,
            key=lambda e: self.pesos.get(e, 0.5),
            reverse=True,
        )


class AjustadorMetacognitivo:
    def __init__(self) -> None:
        self.prefs = PreferenciasEstrategia()
        self._historial_ajustes: list[dict[str, Any]] = []

    def ajustar_desde_registro(self, reg: RegistroMeta) -> dict[str, Any]:
        """
        Actualiza pesos según el resultado de un turno.
        - Alta confianza → refuerza estrategia
        - Baja confianza / necesita datos → penaliza un poco
        - Aprendizaje → neutro/positivo
        """
        est = reg.estrategia
        if est not in self.prefs.pesos:
            self.prefs.pesos[est] = 1.0

        delta = 0.0
        motivo = ""

        if reg.fue_aprendizaje:
            delta = 0.05
            motivo = "aprendizaje exitoso"
        elif reg.confianza >= 0.7:
            delta = 0.12
            motivo = "alta confianza"
        elif reg.confianza >= 0.45:
            delta = 0.03
            motivo = "confianza moderada"
        elif reg.necesita_mas_datos or reg.confianza < 0.35:
            delta = -0.1
            motivo = "baja confianza o sin hechos"
        else:
            delta = -0.02
            motivo = "resultado flojo"

        antes = self.prefs.pesos[est]
        self.prefs.pesos[est] = max(0.2, min(2.5, antes + delta))
        self.prefs.total_ajustes += 1

        # Adaptar umbral de pedir enseñanza
        if reg.necesita_mas_datos:
            self.prefs.umbral_pedir_ensenanza = min(
                0.55, self.prefs.umbral_pedir_ensenanza + 0.02
            )
        elif reg.confianza >= 0.7:
            self.prefs.umbral_pedir_ensenanza = max(
                0.3, self.prefs.umbral_pedir_ensenanza - 0.01
            )

        ajuste = {
            "estrategia": est,
            "delta": round(delta, 3),
            "peso_antes": round(antes, 3),
            "peso_despues": round(self.prefs.pesos[est], 3),
            "motivo": motivo,
        }
        self._historial_ajustes.append(ajuste)
        if len(self._historial_ajustes) > 50:
            self._historial_ajustes = self._historial_ajustes[-50:]
        return ajuste

    def reordenar_plan(self, estrategias: list[str]) -> list[str]:
        """Aplica preferencias aprendidas al plan del nivel 3."""
        if not estrategias:
            return estrategias
        # Mantener solo las del plan, pero ordenadas por peso
        return self.prefs.ordenar(list(estrategias))

    def estado(self) -> dict[str, Any]:
        return {
            "pesos": {k: round(v, 3) for k, v in self.prefs.pesos.items()},
            "umbral_pedir_ensenanza": round(self.prefs.umbral_pedir_ensenanza, 3),
            "total_ajustes": self.prefs.total_ajustes,
            "ultimos_ajustes": self._historial_ajustes[-5:],
        }
