"""
Sistema de recompensa (dopaminérgico simplificado)
==================================================
Señales internas que refuerzan exploración y aprendizaje.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SenalRecompensa:
    tipo: str
    valor: float
    motivo: str


@dataclass
class SistemaRecompensa:
    """Acumula recompensa intrínseca de la sesión."""

    total: float = 0.0
    historial: list[SenalRecompensa] = field(default_factory=list)
    max_hist: int = 80

    def emitir(self, tipo: str, valor: float, motivo: str) -> SenalRecompensa:
        s = SenalRecompensa(tipo=tipo, valor=valor, motivo=motivo)
        self.total += valor
        self.historial.append(s)
        if len(self.historial) > self.max_hist:
            self.historial = self.historial[-self.max_hist :]
        return s

    def por_aprendizaje(self) -> SenalRecompensa:
        return self.emitir("aprendizaje", 0.4, "Nuevo hecho incorporado al grafo")

    def por_alta_confianza(self, conf: float) -> SenalRecompensa:
        return self.emitir("maestria", 0.2 * conf, f"Respuesta con confianza {conf:.0%}")

    def por_laguna_detectada(self) -> SenalRecompensa:
        # Curiosidad: detectar que no sé también genera drive
        return self.emitir("curiosidad", 0.15, "Laguna de conocimiento detectada")

    def por_exploracion(self) -> SenalRecompensa:
        return self.emitir("exploracion", 0.25, "Pregunta autónoma generada")

    def estado(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 3),
            "ultimas": [
                {"tipo": s.tipo, "valor": s.valor, "motivo": s.motivo}
                for s in self.historial[-5:]
            ],
        }
