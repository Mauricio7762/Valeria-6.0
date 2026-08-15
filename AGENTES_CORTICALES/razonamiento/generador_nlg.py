"""
Generador de Lenguaje Natural (NLG estructurado)
=================================================
Convierte un ResultadoInferencia en una conclusión legible en
español. Deliberadamente simple (plantillas), sin modelo generativo.
"""

from __future__ import annotations

from .motor_inferencia import ResultadoInferencia

_PLANTILLAS = {
    "deductiva": "Por deducción: {conclusion}",
    "abductiva": "La explicación más plausible es: {conclusion}",
    "cbr": "{conclusion}",
}

_SIN_CONCLUSION = (
    "No tengo hechos suficientes en mi grafo de conocimiento para "
    "responder con certeza. Podés enseñarme el hecho relevante."
)


class GeneradorNLG:
    def generar(self, resultado: ResultadoInferencia, pregunta_original: str) -> str:
        if not resultado.conclusion:
            return _SIN_CONCLUSION

        plantilla = _PLANTILLAS.get(resultado.estrategia, "{conclusion}")
        texto = plantilla.format(conclusion=resultado.conclusion)

        if resultado.confianza < 0.5:
            texto += " (confianza baja, tomalo como hipótesis)"

        return texto
