"""
Metacognición nivel 3 — Planificación del razonamiento
======================================================
Antes de responder, decide el orden de estrategias a intentar
(deductiva / abductiva / CBR / pedir enseñanza) según la intención
y el estado del grafo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanRazonamiento:
    intencion: str
    entidad: str | None
    estrategias: list[str] = field(default_factory=list)
    motivo: str = ""
    usar_memoria_episodica: bool = True
    pedir_ensenanza_si_falla: bool = True


class PlanificadorMetacognitivo:
    """
    Planifica cómo razonar. No ejecuta la inferencia; solo ordena intentos.
    """

    def planificar(
        self,
        intencion: str,
        entidad: str | None,
        grafo_tiene_entidad: bool,
        grafo_tiene_causas: bool = False,
        hay_episodios_relacionados: bool = False,
    ) -> PlanRazonamiento:
        intencion = (intencion or "general").lower()
        estrategias: list[str] = []
        motivo = ""

        if intencion == "causal":
            # Primero buscar causas; si no, deducir sobre la entidad; luego CBR
            if grafo_tiene_causas or entidad:
                estrategias.append("abductiva")
                motivo = "Pregunta causal: priorizar abducción de causas"
            if grafo_tiene_entidad:
                estrategias.append("deductiva")
            estrategias.append("cbr")

        elif intencion in ("definicion", "propiedad", "verificacion"):
            if grafo_tiene_entidad:
                estrategias = ["deductiva", "cbr"]
                motivo = "Definición/propiedad: priorizar hechos del grafo"
            else:
                estrategias = ["cbr", "deductiva"]
                motivo = "Entidad no está en el grafo: intentar analogía primero"

        elif intencion == "comparacion":
            estrategias = ["deductiva", "cbr"]
            motivo = "Comparación: hechos de ambas entidades si existen"

        else:
            if grafo_tiene_entidad:
                estrategias = ["deductiva", "abductiva", "cbr"]
                motivo = "General con entidad conocida"
            else:
                estrategias = ["cbr", "deductiva"]
                motivo = "General sin entidad clara en el grafo"

        # Deduplicar preservando orden
        vistos: set[str] = set()
        ordenadas: list[str] = []
        for e in estrategias:
            if e not in vistos:
                vistos.add(e)
                ordenadas.append(e)

        return PlanRazonamiento(
            intencion=intencion,
            entidad=entidad,
            estrategias=ordenadas or ["deductiva", "cbr"],
            motivo=motivo,
            usar_memoria_episodica=hay_episodios_relacionados or True,
            pedir_ensenanza_si_falla=not grafo_tiene_entidad,
        )

    def estado(self) -> dict[str, Any]:
        return {"nivel": 3, "nombre": "planificacion_razonamiento"}
