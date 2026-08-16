"""
Metacognición nivel 2 — Evaluación de la calidad de la respuesta
================================================================
Decide si conviene matizar, pedir más información o afirmar.
"""

from __future__ import annotations

from typing import Any

from .nivel1_monitoreo import RegistroMeta


class EvaluadorMetacognitivo:
    """Reglas simples de evaluación post-razonamiento."""

    def evaluar(self, registro: RegistroMeta, conclusion: str) -> dict[str, Any]:
        acciones: list[str] = []
        nota = ""

        if registro.fue_aprendizaje:
            return {
                "calidad": "aprendizaje",
                "acciones": ["confirmar_al_usuario"],
                "nota_usuario": "",
                "mostrar_conclusion": True,
            }

        if registro.necesita_mas_datos or registro.confianza < 0.35:
            nota = (
                "Si querés, enseñame el hecho con una frase del tipo "
                "«X es un Y» o «X es parte de Y»."
            )
            acciones.append("pedir_ensenanza")
            calidad = "insuficiente"
        elif registro.confianza < 0.55:
            nota = "Tómalo con cautela: mi certeza es moderada."
            acciones.append("matizar")
            calidad = "moderada"
        else:
            calidad = "buena"
            acciones.append("afirmar")

        if registro.estrategia == "cbr" and registro.confianza < 0.5:
            acciones.append("advertir_analogia")
            if not nota:
                nota = "Respondí por analogía; puede no aplicar del todo a tu caso."

        return {
            "calidad": calidad,
            "acciones": acciones,
            "nota_usuario": nota,
            "mostrar_conclusion": True,
        }
