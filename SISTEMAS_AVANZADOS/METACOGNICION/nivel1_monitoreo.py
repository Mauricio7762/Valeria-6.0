"""
Metacognición nivel 1 — Monitoreo de ejecución
==============================================
Observa cada respuesta del razonamiento: confianza, estrategia,
si hubo aprendizaje, y registra métricas simples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegistroMeta:
    texto_usuario: str
    estrategia: str
    confianza: float
    intencion: str
    fue_aprendizaje: bool
    necesita_mas_datos: bool


@dataclass
class MonitorMetacognitivo:
    historial: list[RegistroMeta] = field(default_factory=list)
    max_historial: int = 100

    def registrar(self, texto_usuario: str, razon: dict[str, Any]) -> RegistroMeta:
        estrategia = str(razon.get("estrategia") or "desconocida")
        try:
            confianza = float(razon.get("confianza") or 0.0)
        except (TypeError, ValueError):
            confianza = 0.0
        intencion = str(razon.get("intencion") or "general")
        fue_aprendizaje = estrategia == "aprendizaje" or intencion == "enseñanza"
        conclusion = str(razon.get("conclusion") or "")
        necesita = (
            not fue_aprendizaje
            and (
                confianza < 0.4
                or "no tengo hechos" in conclusion.lower()
                or "no pude" in conclusion.lower()
            )
        )
        reg = RegistroMeta(
            texto_usuario=texto_usuario,
            estrategia=estrategia,
            confianza=confianza,
            intencion=intencion,
            fue_aprendizaje=fue_aprendizaje,
            necesita_mas_datos=necesita,
        )
        self.historial.append(reg)
        if len(self.historial) > self.max_historial:
            self.historial = self.historial[-self.max_historial :]
        return reg

    def estado(self) -> dict[str, Any]:
        if not self.historial:
            return {"registros": 0, "confianza_media": None}
        confs = [r.confianza for r in self.historial]
        return {
            "registros": len(self.historial),
            "confianza_media": round(sum(confs) / len(confs), 3),
            "aprendizajes": sum(1 for r in self.historial if r.fue_aprendizaje),
            "baja_confianza": sum(1 for r in self.historial if r.confianza < 0.4),
        }
